"""
Extraction logic built on top of Androguard: turns an APK file into the
plain-data structures the UI layer renders. This module has no Tkinter
dependency, which keeps it independently testable.
"""
import io
import os

from androguard.core.apk import APK
from androguard.core.dex import DEX

from config import ANDROID_NS, DPI_SCORES, ICON_SIZE, KNOWN_TRACKERS
from utils.optional_deps import HAS_PIL, Image


def load_apk(apk_path: str) -> APK:
    return APK(apk_path)


# --- Icon extraction -----------------------------------------------------

def extract_icon(apk: APK):
    """Return a PIL Image for the app's best-available launcher icon, or None."""
    if not HAS_PIL:
        return None
    try:
        icon_path = apk.get_app_icon(max_dpi=True)

        if icon_path and icon_path.lower().endswith((".png", ".webp", ".jpg")):
            icon_data = apk.get_file(icon_path)
            if icon_data:
                return _load_and_resize(icon_data)

        base_name = _resolve_icon_base_name(apk, icon_path)
        return _find_best_icon_by_name(apk, base_name)
    except Exception:
        return None


def _resolve_icon_base_name(apk: APK, icon_path) -> str:
    if icon_path:
        return os.path.splitext(os.path.basename(icon_path))[0]

    xml_elem = apk.get_android_manifest_xml()
    if xml_elem is not None:
        app_tag = xml_elem.find(".//application")
        if app_tag is not None:
            icon_ref = app_tag.get(f"{ANDROID_NS}icon") or app_tag.get(f"{ANDROID_NS}roundIcon")
            if icon_ref and "/" in icon_ref:
                return icon_ref.split("/")[-1]

    return "ic_launcher"


def _find_best_icon_by_name(apk: APK, base_name: str):
    matches = [
        f for f in apk.get_files()
        if os.path.splitext(os.path.basename(f))[0] == base_name
        and f.lower().endswith((".png", ".webp", ".jpg"))
    ]
    matches.sort(
        key=lambda p: next((score for dpi, score in DPI_SCORES.items() if dpi in p.lower()), 0),
        reverse=True,
    )

    for match in matches:
        try:
            return _load_and_resize(apk.get_file(match))
        except Exception:
            continue
    return None


def _load_and_resize(icon_bytes: bytes):
    img = Image.open(io.BytesIO(icon_bytes))
    return img.resize(ICON_SIZE, Image.Resampling.LANCZOS)


# --- Analysis sections -----------------------------------------------------

def get_app_info(apk: APK) -> dict:
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


def get_security_info(apk: APK) -> dict:
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


def get_components_info(apk: APK) -> dict:
    return {
        "Activities": sorted(apk.get_activities()),
        "Services": sorted(apk.get_services()),
        "Receivers": sorted(apk.get_receivers()),
        "Providers": sorted(apk.get_providers()),
        "Intent Actions": sorted(_extract_intent_actions(apk)),
    }


def _extract_intent_actions(apk: APK) -> list:
    pkg_name = apk.get_package()
    actions = set()

    try:
        xml_root = apk.get_android_manifest_xml()
        if xml_root is None:
            return []

        for tag in ("activity", "activity-alias", "service", "receiver", "provider"):
            for comp in xml_root.iter(tag):
                if not _is_exported(comp):
                    continue
                comp_name = _resolve_component_name(comp, pkg_name)
                comp_type = tag.capitalize()

                for filter_node in comp.iter("intent-filter"):
                    actions.update(_actions_from_filter(filter_node, comp_type, comp_name))
    except Exception:
        pass

    return list(actions)


def _is_exported(comp) -> bool:
    exported = comp.get(f"{ANDROID_NS}exported", "").lower()
    has_filters = comp.find("intent-filter") is not None
    return exported == "true" or (not exported and has_filters)


def _resolve_component_name(comp, pkg_name: str) -> str:
    name = comp.get(f"{ANDROID_NS}name", "Unknown")
    if name.startswith("."):
        return pkg_name + name
    if "." not in name and name != "Unknown":
        return f"{pkg_name}.{name}"
    return name


def _actions_from_filter(filter_node, comp_type: str, comp_name: str) -> set:
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
            extras.extend(_data_node_extras(node))

    extras.append(f"{comp_type}='{comp_name}'")
    extras_str = ", ".join(extras)
    return {f"{action} ( {extras_str} )" for action in action_names}


def _data_node_extras(node) -> list:
    attr_labels = ("mimeType", "scheme", "host", "path", "pathPrefix")
    extras = []
    for attr in attr_labels:
        value = node.get(f"{ANDROID_NS}{attr}")
        if value:
            extras.append(f"{attr}='{value}'")
    return extras


def get_trackers_and_libraries(apk: APK) -> dict:
    packages = _collect_dex_packages(apk)
    trackers = {
        f"{tracker_name} (Found in: {pkg})"
        for pkg in packages
        for key, tracker_name in KNOWN_TRACKERS.items()
        if key in pkg.lower()
    }

    return {
        "Hardware Features": apk.get_features(),
        "Libraries": apk.get_libraries(),
        "Trackers": sorted(trackers),
    }


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


# --- Public entry point -----------------------------------------------------

def analyze(apk_path: str) -> dict:
    """Run the full analysis pipeline and return everything the UI needs."""
    apk = load_apk(apk_path)
    sections = {
        "App Information": get_app_info(apk),
        "Security & Operations": get_security_info(apk),
        "Components & Intents": get_components_info(apk),
        "Extras & Libraries": get_trackers_and_libraries(apk),
    }
    return {
        "apk": apk,
        "icon": extract_icon(apk),
        "sections": sections,
    }
