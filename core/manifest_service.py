"""
Formats an APK's AndroidManifest.xml into pretty-printed text.
"""
import os
import xml.dom.minidom as minidom

from utils.optional_deps import ET, HAS_LXML, etree


def format_manifest(apk) -> str:
    """Return the AndroidManifest.xml of `apk` as pretty-printed XML text."""
    try:
        xml_root = apk.get_android_manifest_xml()
        if xml_root is None:
            return "Manifest XML is missing or corrupted."

        raw_xml = (
            etree.tostring(xml_root, encoding="utf-8")
            if HAS_LXML
            else ET.tostring(xml_root, encoding="utf-8")
        )
        pretty = minidom.parseString(raw_xml).toprettyxml(indent="    ")
        return os.linesep.join(line for line in pretty.splitlines() if line.strip())
    except Exception as exc:
        return f"Error processing Manifest:\n{exc}"
