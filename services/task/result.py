import json
from flask import current_app

RESULT_TTL = 86400

class TaskResult:
    @staticmethod
    def save(task_id, result_data):
        redis_client = current_app.redis_client_tasks
        redis_client.hset(f"task:{task_id}", "result_data_json", json.dumps(result_data))
        redis_client.expire(f"task:{task_id}", RESULT_TTL)
    
    @staticmethod
    def load(task_id):
        redis_client = current_app.redis_client_tasks
        raw_data = redis_client.hgetall(f"task:{task_id}")
        result_json = raw_data.get(b'result_data_json') or raw_data.get('result_data_json')
        if result_json:
            return json.loads(result_json.decode() if isinstance(result_json, bytes) else result_json)
        return None

