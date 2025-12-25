from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"

