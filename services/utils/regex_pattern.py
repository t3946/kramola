import re
import functools


class RegexPattern:
    """Information about a regex pattern that matched."""
    
    def __init__(self, pattern_name: str, pattern: str):
        self.pattern_name = pattern_name
        self._pattern = pattern
        self._compiled: re.Pattern | None = None

    @property
    def pattern(self) -> str:
        """Get pattern string."""
        return self._pattern

    @property
    def compiled(self) -> re.Pattern:
        """Get compiled regex pattern with caching."""
        if self._compiled is None:
            self._compiled = self._compile_pattern(self._pattern)
        return self._compiled

    @staticmethod
    @functools.lru_cache(maxsize=128)
    def _compile_pattern(pattern_str: str) -> re.Pattern:
        """Compile a single regex pattern with caching."""
        return re.compile(pattern_str)

    def __str__(self) -> str:
        return self._pattern
