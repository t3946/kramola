from typing import Tuple


class Color:
    """Parses #xxxxxx hex color and exposes rrggbb string and rgb tuple."""

    def __init__(self, hex_color: str) -> None:
        s = hex_color.strip().lstrip("#")
        self._hex: str = s.lower()

    def rrggbb(self) -> str:
        """Hex without #, lowercase (e.g. 'ff00ab')."""
        return self._hex

    def rgb(self) -> Tuple[float, float, float]:
        """RGB channels in 0.0..1.0."""
        r = int(self._hex[0:2], 16) / 255.0
        g = int(self._hex[2:4], 16) / 255.0
        b = int(self._hex[4:6], 16) / 255.0

        return (r, g, b)
