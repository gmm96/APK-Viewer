"""
Abstraction over "how do we render a byte count for humans", so widgets
depend on an interface rather than a bare function. This is what lets
FilesPanel be unit-tested with a fake formatter, and would let a different
unit system be swapped in without touching any widget code.
"""
from abc import ABC, abstractmethod


class SizeFormatter(ABC):
    @abstractmethod
    def format(self, num_bytes) -> str:
        raise NotImplementedError


class HumanReadableSizeFormatter(SizeFormatter):
    """Formats byte counts as B / KB / MB / GB / TB, as most file browsers do."""

    _UNITS = ("B", "KB", "MB", "GB")

    def format(self, num_bytes) -> str:
        try:
            num = float(num_bytes)
        except (TypeError, ValueError):
            return "-"

        for unit in self._UNITS:
            if num < 1024.0:
                return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} TB"
