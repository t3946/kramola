import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from flask import current_app, has_app_context
from redis import Redis

from services.redis.connection import get_redis_connection

PARSER_LAST_PARSE_KEY_PREFIX: str = "parser:last_parse:"


def _get_parser_redis_client() -> Redis:
    if has_app_context():
        client: Redis | None = getattr(current_app, "redis_client_tasks", None)
        if client is not None:
            return client

    redis_db: int = int(os.environ.get("REDIS_DB_TASKS", "0"))

    return get_redis_connection(db=redis_db, decode_responses=True)


class Parser(ABC):
    def _redis_client_for_parser(self) -> Redis:
        return _get_parser_redis_client()

    @classmethod
    def _last_parse_redis_key(cls) -> str:
        return f"{PARSER_LAST_PARSE_KEY_PREFIX}{cls.__name__}"

    def _update_last_parse_date(self) -> None:
        client: Redis = self._redis_client_for_parser()
        now_iso: str = datetime.now(timezone.utc).isoformat()

        client.set(self.__class__._last_parse_redis_key(), now_iso)

    @classmethod
    def get_last_parse_datetime(cls) -> datetime | None:
        client: Redis = _get_parser_redis_client()
        raw: str | None = client.get(cls._last_parse_redis_key())

        if raw is None:
            return None

        return datetime.fromisoformat(raw)

    @abstractmethod
    def _perform_update(self) -> None:
        pass

    def update(self) -> None:
        self._perform_update()
        self._update_last_parse_date()
