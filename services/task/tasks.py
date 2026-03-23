import json
from datetime import datetime, timedelta, timezone
from redis import Redis

from services.task.redis_fields import (
    REDIS_TASK_CREATED_AT,
    REDIS_TASK_SOURCE_ARCHIVED_FILENAME,
    REDIS_TASK_SOURCE_FILENAME,
)
from services.task.task import Task, TaskStatus

_TASK_KEY_PREFIX: str = "task:"


def _normalize_redis_hash(raw: dict) -> dict[str, str]:
    out: dict[str, str] = {}

    for k, v in raw.items():
        ks: str = k.decode() if isinstance(k, bytes) else k
        vs: str = v.decode() if isinstance(v, bytes) else v
        out[ks] = vs

    return out


def _status_from_redis_state(state_str: str | None) -> TaskStatus:
    if state_str is None:
        return TaskStatus.PENDING

    matched: TaskStatus | None = next(
        (s for s in TaskStatus if s.value == state_str),
        None,
    )

    return matched if matched is not None else TaskStatus.PENDING


def _parse_created_at(iso_str: str | None) -> datetime | None:
    if not iso_str:
        return None

    normalized: str = iso_str.replace("Z", "+00:00", 1) if iso_str.endswith("Z") else iso_str

    return datetime.fromisoformat(normalized)


def _created_at_from_fields(fields: dict[str, str]) -> datetime | None:
    from_redis: datetime | None = _parse_created_at(fields.get(REDIS_TASK_CREATED_AT))

    if from_redis:
        return from_redis

    raw_json: str | None = fields.get("result_data_json")

    if not raw_json:
        return None

    payload: dict = json.loads(raw_json)
    from_json: str | None = payload.get("created_at")

    return _parse_created_at(from_json)


def _source_label_from_fields(fields: dict[str, str]) -> str:
    fn: str | None = fields.get(REDIS_TASK_SOURCE_FILENAME)

    if fn:
        return fn

    raw_json: str | None = fields.get("result_data_json")

    if raw_json:
        payload: dict = json.loads(raw_json)
        from_result: str | None = payload.get("source_filename")

        if from_result:
            return from_result

    return "—"


def _expires_at_for_display(
    created_at: datetime | None,
    task_ttl_seconds: int,
    redis_client: Redis,
    task_key: str,
) -> datetime | None:
    """Policy-based expiry: created_at + task_ttl. Fallback: Redis TTL when created_at is unknown."""
    if created_at is not None:
        start: datetime = created_at

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        return start + timedelta(seconds=task_ttl_seconds)

    ttl_raw: int = int(redis_client.ttl(task_key))

    if ttl_raw > 0:
        return datetime.now(timezone.utc) + timedelta(seconds=ttl_raw)

    return None


class Tasks:
    @staticmethod
    def get_all(redis_client: Redis, task_ttl_seconds: int) -> list[Task]:
        ids: set[str] = set()

        for raw_key in redis_client.scan_iter(match=f"{_TASK_KEY_PREFIX}*", count=500):
            key: str = raw_key.decode() if isinstance(raw_key, bytes) else raw_key

            if not key.startswith(_TASK_KEY_PREFIX):
                continue

            rest: str = key[len(_TASK_KEY_PREFIX):]

            if not rest:
                continue

            tid: str = rest.split(":", 1)[0]
            ids.add(tid)

        tasks: list[Task] = []

        for tid in sorted(ids):
            raw_hash = redis_client.hgetall(f"task:{tid}")
            fields: dict[str, str] = _normalize_redis_hash(raw_hash) if raw_hash else {}
            state_raw: str | None = fields.get("state")
            archived: str | None = fields.get(REDIS_TASK_SOURCE_ARCHIVED_FILENAME)
            has_archive: bool = bool(archived)
            created: datetime | None = _created_at_from_fields(fields)
            label: str = _source_label_from_fields(fields)
            main_key: str = f"task:{tid}"
            expires_at: datetime | None = _expires_at_for_display(
                created,
                task_ttl_seconds,
                redis_client,
                main_key,
            )

            tasks.append(
                Task(
                    task_id=tid,
                    status=_status_from_redis_state(state_raw),
                    source_label=label,
                    created_at=created,
                    expires_at=expires_at,
                    has_source_archive=has_archive,
                )
            )

        return tasks
