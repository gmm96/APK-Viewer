"""
Builds an in-memory tree representation of an APK's internal zip entries,
with per-node size aggregation and text-based filtering.
"""
import zipfile
from datetime import datetime


def build_file_tree(apk_path: str) -> dict:
    """Read the APK as a zip file and build a nested dict tree of its entries."""
    root_node = {}
    try:
        with zipfile.ZipFile(apk_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir() or not info.filename:
                    continue
                _insert_entry(root_node, info)
    except Exception:
        pass

    _aggregate_folder_sizes(root_node)
    return root_node


def _insert_entry(root_node: dict, info: zipfile.ZipInfo) -> None:
    parts = [p for p in info.filename.split("/") if p]
    if not parts:
        return

    node = root_node
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        if part not in node:
            node[part] = {"__children__": {}, "__is_file__": False, "__size__": 0}

        if is_last:
            node[part]["__is_file__"] = True
            node[part]["__size__"] = info.file_size
            node[part]["__compressed__"] = info.compress_size
            node[part]["__modified__"] = _format_mtime(info.date_time)

        node = node[part]["__children__"]


def _format_mtime(date_time_tuple) -> str:
    try:
        return datetime(*date_time_tuple).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def _aggregate_folder_sizes(node_dict: dict):
    """
    Recursively sum size/compressed size and find the most recent
    modification date for every folder node, bottom-up.
    """
    total_size = 0
    total_compressed = 0
    latest_modified = ""

    for meta in node_dict.values():
        if meta.get("__is_file__"):
            total_size += meta.get("__size__", 0)
            total_compressed += meta.get("__compressed__", 0)
            mtime = meta.get("__modified__", "")
        else:
            folder_size, folder_comp, mtime = _aggregate_folder_sizes(meta.get("__children__", {}))
            meta["__size__"] = folder_size
            meta["__compressed__"] = folder_comp
            meta["__modified__"] = mtime
            total_size += folder_size
            total_compressed += folder_comp

        if mtime > latest_modified:
            latest_modified = mtime

    return total_size, total_compressed, latest_modified


def filter_file_tree(node_dict: dict, query: str, force_include: bool = False) -> dict:
    """Return a filtered copy of the tree, keeping only nodes matching `query`."""
    if not query:
        return node_dict

    filtered = {}
    for name, meta in node_dict.items():
        matches_name = query in name.lower()
        should_include = force_include or matches_name

        if meta.get("__is_file__"):
            if should_include:
                filtered[name] = meta
        else:
            children = filter_file_tree(meta.get("__children__", {}), query, should_include)
            if children or should_include:
                new_meta = dict(meta)
                new_meta["__children__"] = children
                filtered[name] = new_meta

    return filtered
