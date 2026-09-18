"""
Small, dependency-free formatting helpers.
"""


def human_size(num_bytes) -> str:
    """Convert a byte count into a human-readable string (B, KB, MB, GB, TB)."""
    try:
        num = float(num_bytes)
    except (TypeError, ValueError):
        return "-"

    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024.0:
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"
