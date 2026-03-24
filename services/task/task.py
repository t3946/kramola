from datetime import datetime, timedelta, timezone
from enum import Enum

_MSK_TZ = timezone(timedelta(hours=3))
_KIB: int = 1024
_MIB: int = 1024 * 1024


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


def _datetime_display_moscow(dt: datetime | None) -> str:
    if not dt:
        return "—"

    dt_utc: datetime = dt

    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)

    msk: datetime = dt_utc.astimezone(_MSK_TZ)

    return msk.strftime("%d.%m.%Y %H:%M") + " МСК"


def _format_file_size_display(size_bytes: int) -> str:
    if size_bytes < _KIB:
        return f"{size_bytes} B"

    if size_bytes < _MIB:
        kb: float = size_bytes / _KIB

        return f"{kb:.1f} KB"

    mb: float = size_bytes / _MIB

    return f"{mb:.1f} MB"


class Task:
    task_id: str
    status: TaskStatus
    source_label: str
    created_at: datetime | None
    expires_at: datetime | None
    has_source_archive: bool
    processing_time_seconds: float | None
    source_file_size_bytes: int | None

    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        source_label: str,
        created_at: datetime | None,
        expires_at: datetime | None,
        has_source_archive: bool,
        processing_time_seconds: float | None,
        source_file_size_bytes: int | None,
    ) -> None:
        self.task_id = task_id
        self.status = status
        self.source_label = source_label
        self.created_at = created_at
        self.expires_at = expires_at
        self.has_source_archive = has_source_archive
        self.processing_time_seconds = processing_time_seconds
        self.source_file_size_bytes = source_file_size_bytes

    def processing_time_display(self) -> str:
        if self.processing_time_seconds is None:
            return "—"

        return f"{self.processing_time_seconds:.2f} с"

    def source_size_display(self) -> str:
        if self.source_file_size_bytes is None:
            return "—"

        return _format_file_size_display(self.source_file_size_bytes)

    def status_display_ru(self) -> str:
        return _TASK_STATUS_LABEL_RU.get(self.status, self.status.value)

    def created_at_display_moscow(self) -> str:
        return _datetime_display_moscow(self.created_at)

    def expires_at_display_moscow(self) -> str:
        return _datetime_display_moscow(self.expires_at)
