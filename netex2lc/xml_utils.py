from __future__ import annotations

from typing import Iterable, List, Optional

try:  # Prefer lxml if available
    from lxml import etree as ET  # type: ignore
except ImportError:  # pragma: no cover - fallback for minimal environments
    import xml.etree.ElementTree as ET  # type: ignore


def local_name(tag: str) -> str:
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def iter_elements(root, name: str):
    for elem in root.iter():
        if local_name(elem.tag) == name:
            yield elem


def find_first(elem, names: Iterable[str]):
    for child in elem.iter():
        if local_name(child.tag) in names:
            return child
    return None


def find_text(elem, names: Iterable[str]) -> Optional[str]:
    child = find_first(elem, names)
    if child is None:
        return None
    text = child.text.strip() if child.text else None
    if text:
        return text
    return None


def find_ref(elem, names: Iterable[str]) -> Optional[str]:
    child = find_first(elem, names)
    if child is None:
        return None
    ref = child.get("ref") or child.get("id")
    if ref:
        return ref
    text = child.text.strip() if child.text else None
    return text
