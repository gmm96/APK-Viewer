"""
Composition root for the analysis pipeline: wires an APK loader, an icon
extractor and a set of section extractors together, and exposes a single
`analyze()` entry point. Every dependency can be overridden by the caller
(constructor injection), which is what makes this class unit-testable
without touching real APK files.
"""
from typing import Dict, Optional

from .apk_loader import ApkLoader
from .icon_extractor import IconExtractor
from .info_extractors import (
    AnalysisSectionExtractor,
    AppInfoExtractor,
    ComponentsExtractor,
    SecurityInfoExtractor,
    TrackerDetector,
)
from .models import AnalysisResult


class ApkAnalyzer:
    def __init__(
        self,
        apk_loader: Optional[ApkLoader] = None,
        icon_extractor: Optional[IconExtractor] = None,
        section_extractors: Optional[Dict[str, AnalysisSectionExtractor]] = None,
    ):
        self._apk_loader = apk_loader or ApkLoader()
        self._icon_extractor = icon_extractor or IconExtractor()
        self._section_extractors = section_extractors or self._default_section_extractors()

    @staticmethod
    def _default_section_extractors() -> Dict[str, AnalysisSectionExtractor]:
        return {
            "App Information": AppInfoExtractor(),
            "Security & Operations": SecurityInfoExtractor(),
            "Components & Intents": ComponentsExtractor(),
            "Extras & Libraries": TrackerDetector(),
        }

    def analyze(self, apk_path: str) -> AnalysisResult:
        apk = self._apk_loader.load(apk_path)
        sections = {
            title: extractor.extract(apk)
            for title, extractor in self._section_extractors.items()
        }
        icon = self._icon_extractor.extract(apk)
        return AnalysisResult(apk=apk, icon=icon, sections=sections)
