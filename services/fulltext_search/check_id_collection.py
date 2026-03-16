import uuid
from typing import Tuple


class CheckIdCollection:
    def __init__(self):
        self.check_id_map: dict[Tuple[int, int], uuid.UUID] = {}

    def __getitem__(self, tokens_indices: Tuple[int, int]) -> uuid.UUID:
        if tokens_indices not in self.check_id_map:
            self.check_id_map[tokens_indices] = uuid.uuid1()

        return self.check_id_map[tokens_indices]