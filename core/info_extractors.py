"""
Section extractors: each turns raw Androguard APK data into a plain
label -> value dict ready for display. Sharing a common interface lets
`ApkAnalyzer` treat them interchangeably (Open/Closed: a new section is
added by writing a new extractor, without touching the analyzer).
"""
from abc import ABC, abstractmethod

from androguard.core.apk import APK
from androguard.core.dex import DEX

from config import ANDROID_NS, KNOWN_TRACKERS


class AnalysisSectionExtractor(ABC):
    """Base contract for anything that turns an APK into a display section."""

    @abstractmethod
    def extract(self, apk: APK) -> dict:
        raise NotImplementedError


class AppInfoExtractor(AnalysisSectionExtractor):
    def extract(self, apk: APK) -> dict:
        archs = {
            f.split("/")[1]
            for f in apk.get_files()
            if f.startswith("lib/") and len(f.split("/")) > 1
        }
        return {
            "App name": apk.get_app_name(),
            "Package name": apk.get_package(),
            "Version": apk.get_androidversion_name(),
            "Version code": apk.get_androidversion_code(),
            "Split / Multidex": "Yes" if apk.is_multidex() else "No",
            "Architectures": ", ".join(archs) if archs else "None / Unknown",
            "Min SDK": apk.get_min_sdk_version(),
            "Target SDK": apk.get_target_sdk_version(),
            "Max SDK": apk.get_max_sdk_version(),
            "Effective SDK": apk.get_effective_target_sdk_version(),
        }


class SecurityInfoExtractor(AnalysisSectionExtractor):
    def extract(self, apk: APK) -> dict:
        perms, appops = [], []
        for p in apk.get_permissions():
            (perms if p.startswith("android.permission.") else appops).append(p)

        certs = []
        for cert in apk.get_certificates():
            try:
                certs.append(f"Issuer: {cert.issuer.human_friendly}\nSubject: {cert.subject.human_friendly}")
            except Exception:
                certs.append("Unknown / Encrypted Certificate")

        return {
            "Permissions": sorted(perms),
            "AppOps / Custom Perms": sorted(appops),
            "Certificates": certs,
        }


class ComponentsExtractor(AnalysisSectionExtractor):
    def extract(self, apk: APK) -> dict:
        return {
            "Activities": sorted(apk.get_activities()),
            "Services": sorted(apk.get_services()),
            "Receivers": sorted(apk.get_receivers()),
            "Providers": sorted(apk.get_providers()),
            "Intent Actions": sorted(self._extract_intent_actions(apk)),
        }

    def _extract_intent_actions(self, apk: APK) -> list:
        pkg_name = apk.get_package()
        actions = set()

        try:
            xml_root = apk.get_android_manifest_xml()
            if xml_root is None:
                return []

            for tag in ("activity", "activity-alias", "service", "receiver", "provider"):
                for comp in xml_root.iter(tag):
                    if not self._is_exported(comp):
                        continue
                    comp_name = self._resolve_component_name(comp, pkg_name)
                    comp_type = tag.capitalize()

                    for filter_node in comp.iter("intent-filter"):
                        actions.update(self._actions_from_filter(filter_node, comp_type, comp_name))
        except Exception:
            pass

        return list(actions)

    @staticmethod
    def _is_exported(comp) -> bool:
        exported = comp.get(f"{ANDROID_NS}exported", "").lower()
        has_filters = comp.find("intent-filter") is not None
        return exported == "true" or (not exported and has_filters)

    @staticmethod
    def _resolve_component_name(comp, pkg_name: str) -> str:
        name = comp.get(f"{ANDROID_NS}name", "Unknown")
        if name.startswith("."):
            return pkg_name + name
        if "." not in name and name != "Unknown":
            return f"{pkg_name}.{name}"
        return name

    def _actions_from_filter(self, filter_node, comp_type: str, comp_name: str) -> set:
        action_names = []
        extras = []

        for node in filter_node:
            if node.tag == "action":
                name = node.get(f"{ANDROID_NS}name")
                if name:
                    action_names.append(name)
            elif node.tag == "category":
                cat = node.get(f"{ANDROID_NS}name")
                if cat:
                    extras.append(f"category='{cat.replace('android.intent.category.', '')}'")
            elif node.tag == "data":
                extras.extend(self._data_node_extras(node))

        extras.append(f"{comp_type}='{comp_name}'")
        extras_str = ", ".join(extras)
        return {f"{action} ( {extras_str} )" for action in action_names}

    @staticmethod
    def _data_node_extras(node) -> list:
        attr_labels = ("mimeType", "scheme", "host", "path", "pathPrefix")
        extras = []
        for attr in attr_labels:
            value = node.get(f"{ANDROID_NS}{attr}")
            if value:
                extras.append(f"{attr}='{value}'")
        return extras


class TrackerDetector(AnalysisSectionExtractor):
    """Scans DEX class packages for known analytics/ads/SDK signatures."""

    def __init__(self, tracker_signatures: dict = None):
        self._tracker_signatures = tracker_signatures or KNOWN_TRACKERS

    def extract(self, apk: APK) -> dict:
        packages = self._collect_dex_packages(apk)
        trackers = {
            f"{tracker_name} (Found in: {pkg})"
            for pkg in packages
            for key, tracker_name in self._tracker_signatures.items()
            if key in pkg.lower()
        }

        return {
            "Hardware Features": apk.get_features(),
            "Libraries": apk.get_libraries(),
            "Trackers": sorted(trackers),
        }

    @staticmethod
    def _collect_dex_packages(apk: APK) -> set:
        packages = set()
        for dex_bytes in apk.get_all_dex():
            try:
                for cls in DEX(dex_bytes).get_classes():
                    name = getattr(cls, "name", None)
                    if name is None:
                        name = cls.get_name()
                    parts = str(name).lstrip("L").split("/")
                    if len(parts) > 1:
                        packages.add(".".join(parts[:3] if len(parts) > 3 else parts[:-1]))
            except Exception:
                pass
        return packages
