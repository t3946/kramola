import os


def get_config(base_dir: str) -> dict:
    return {
        "REDIS_TASK_TTL": int(os.environ.get("REDIS_TASK_TTL", 3600)),
        "EXECUTOR_TYPE": os.environ.get("EXECUTOR_TYPE", "thread"),
        "EXECUTOR_MAX_WORKERS": int(os.environ.get("EXECUTOR_MAX_WORKERS", 5)),
        "UPLOAD_DIR": os.path.join(base_dir, "uploads"),
        "RESULT_DIR": os.path.join(base_dir, "results"),
        "PREDEFINED_LISTS_DIR": os.path.join(base_dir, "predefined_lists"),
        "UPLOAD_DIR_HIGHLIGHT": os.path.join(base_dir, "uploads", "highlight"),
        "RESULT_DIR_HIGHLIGHT": os.path.join(base_dir, "results", "highlight"),
        "UPLOAD_DIR_FOOTNOTES": os.path.join(base_dir, "uploads", "footnotes"),
        "RESULT_DIR_FOOTNOTES": os.path.join(base_dir, "results", "footnotes"),
    }
