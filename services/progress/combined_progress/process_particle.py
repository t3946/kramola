from dataclasses import dataclass
from typing import Optional


@dataclass
class ProgressParticle:
    key: str
    description: Optional[str] = ''
    max_value: Optional[int] = 100