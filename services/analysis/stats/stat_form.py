from dataclasses import dataclass
from typing import Optional


@dataclass
class StatForm:
    count: int
    form: str
    page: Optional[int] = None  # only for PDF
