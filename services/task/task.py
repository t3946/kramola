from datetime import datetime, timedelta, timezone
from enum import Enum

_MSK_TZ = timezone(timedelta(hours=3))


class TaskStatus(str, Enum):
    """Task status enumeration"""
    # task awaits execution
    PENDING = "PENDING"

    # task is being executed
    PROCESSING = "PROCESSING"

    # task is completed
    COMPLETED = "COMPLETED"


_TASK_STATUS_LABEL_RU: dict[TaskStatus, str] = {
    TaskStatus.PENDING: "В очереди",
    TaskStatus.PROCESSING: "Выполняется",
    TaskStatus.COMPLETED: "Завершена",
}


class Task:
    task_id: str
    status: TaskStatus
    source_label: str
    created_at: datetime | None
    has_source_archive: bool

    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        source_label: str,
        created_at: datetime | None,
        has_source_archive: bool,
    ) -> None:
        self.task_id = task_id
        self.status = status
        self.source_label = source_label
        self.created_at = created_at
        self.has_source_archive = has_source_archive

    def status_display_ru(self) -> str:
        return _TASK_STATUS_LABEL_RU.get(self.status, self.status.value)

    def created_at_display_moscow(self) -> str:
        if not self.created_at:
            return "—"

        dt_utc: datetime = self.created_at

        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)

        msk: datetime = dt_utc.astimezone(_MSK_TZ)

        return msk.strftime("%d.%m.%Y %H:%M") + " МСК"
