"""
Plain data structures shared between the core (business logic) and UI layers.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AnalysisResult:
    """Everything the UI needs to render after analyzing one APK."""

    apk: Any
    icon: Optional[Any]
    sections: Dict[str, Dict[str, Any]]
