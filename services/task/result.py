import json
from typing import Any, Optional

from flask import current_app


class TaskResult:
    @staticmethod
    def save(task_id: str, result_data: dict[str, Any]) -> None:
        redis_client = current_app.redis_client_tasks
        ttl_seconds: int = int(current_app.config["REDIS_TASK_TTL"])
        redis_client.hset(f"task:{task_id}", "result_data_json", json.dumps(result_data))
        redis_client.expire(f"task:{task_id}", ttl_seconds)

    @staticmethod
    def load(task_id: str) -> Optional[dict[str, Any]]:
        redis_client = current_app.redis_client_tasks
        raw_data = redis_client.hgetall(f"task:{task_id}")
        result_json = raw_data.get(b"result_data_json") or raw_data.get("result_data_json")

        if result_json:
            return json.loads(result_json.decode() if isinstance(result_json, bytes) else result_json)

        return None
