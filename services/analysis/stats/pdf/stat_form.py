from dataclasses import dataclass
from typing import Optional, List


@dataclass
class StatForm:
    count: int
    form: str
    pages: List[int]
