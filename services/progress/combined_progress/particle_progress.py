from dataclasses import dataclass

from services.progress.task_progress import TaskProgress

@dataclass
class ParticleProgress(TaskProgress):
    value: float = 0
    max_value: float = 100