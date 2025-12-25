from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration"""
    # task awaits execution
    PENDING = "PENDING"
    
    # task is being executed
    PROCESSING = "PROCESSING"
    
    # task is completed
    COMPLETED = "COMPLETED"

