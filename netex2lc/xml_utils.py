"""XML parsing utilities with XPath support for performance."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional

try:
    from lxml import etree as ET

    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET  # type: ignore

    LXML_AVAILABLE = False


# Common namespaces
NAMESPACES: Dict[str, str] = {
    "netex": "http://www.netex.org.uk/netex",
    "siri": "http://www.siri.org.uk/siri",
    "gml": "http://www.opengis.net/gml/3.2",
}


def local_name(tag: str) -> str:
    """Extract local name from a potentially namespaced tag."""
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def get_namespace(tag: str) -> Optional[str]:
    """Extract namespace from a tag."""
    if not isinstance(tag, str):
        return None
    if tag.startswith("{") and "}" in tag:
        return tag[1 : tag.index("}")]
    return None


def iter_elements(root, name: str) -> Iterator:
    """Iterate over elements with the given local name.

    Uses XPath when lxml is available for better performance.
    """
    if LXML_AVAILABLE:
        # Use XPath with local-name() for namespace-agnostic matching
        xpath = f".//*[local-name()='{name}']"
        try:
            yield from root.xpath(xpath)
            return
        except Exception:
            pass  # Fall back to iteration

    # Fallback: iterate and filter
    for elem in root.iter():
        if local_name(elem.tag) == name:
            yield elem


def iter_elements_stream(path: str, name: str) -> Iterator:
    """Stream elements from a file without loading entire tree.

    Memory-efficient for large files.
    """
    if not LXML_AVAILABLE:
        # Fallback: load entire file
        tree = ET.parse(path)
        yield from iter_elements(tree.getroot(), name)
        return

    # Use iterparse for memory efficiency
    context = ET.iterparse(path, events=("end",))
    for event, elem in context:
        if local_name(elem.tag) == name:
            yield elem
            # Clear element to free memory
            elem.clear()
            # Also clear parent references
            while elem.getprevious() is not None:
                del elem.getparent()[0]


def find_first(elem, names: Iterable[str]) -> Optional[Any]:
    """Find first child element matching any of the given names.

    Uses XPath when lxml is available.
    """
    names_list = list(names)

    if LXML_AVAILABLE:
        # Build XPath expression
        conditions = " or ".join(f"local-name()='{n}'" for n in names_list)
        xpath = f".//*[{conditions}]"
        try:
            results = elem.xpath(xpath)
            if results:
                return results[0]
            return None
        except Exception:
            pass  # Fall back to iteration

    # Fallback: iterate and filter
    names_set = set(names_list)
    for child in elem.iter():
        if local_name(child.tag) in names_set:
            return child
    return None


def find_all(elem, names: Iterable[str]) -> List:
    """Find all child elements matching any of the given names."""
    names_list = list(names)

    if LXML_AVAILABLE:
        conditions = " or ".join(f"local-name()='{n}'" for n in names_list)
        xpath = f".//*[{conditions}]"
        try:
            return elem.xpath(xpath)
        except Exception:
            pass  # Fall back to iteration

    names_set = set(names_list)
    return [child for child in elem.iter() if local_name(child.tag) in names_set]


def find_text(elem, names: Iterable[str]) -> Optional[str]:
    """Find and return text content of first matching child element."""
    child = find_first(elem, names)
    if child is None:
        return None
    text = child.text.strip() if child.text else None
    return text if text else None


def find_ref(elem, names: Iterable[str]) -> Optional[str]:
    """Find and return ref/id attribute or text content of first matching element."""
    child = find_first(elem, names)
    if child is None:
        return None
    ref = child.get("ref") or child.get("id")
    if ref:
        return ref
    text = child.text.strip() if child.text else None
    return text


def find_attribute(elem, names: Iterable[str], attr: str) -> Optional[str]:
    """Find element and return specific attribute value."""
    child = find_first(elem, names)
    if child is None:
        return None
    return child.get(attr)


def xpath_text(elem, xpath_expr: str, namespaces: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Execute XPath and return text of first result.

    Only works with lxml.
    """
    if not LXML_AVAILABLE:
        return None

    ns = namespaces or NAMESPACES
    try:
        results = elem.xpath(xpath_expr, namespaces=ns)
        if results:
            if hasattr(results[0], "text"):
                return results[0].text.strip() if results[0].text else None
            return str(results[0]).strip()
        return None
    except Exception:
        return None


def parse_xml(path: str) -> Any:
    """Parse XML file and return root element."""
    tree = ET.parse(path)
    return tree.getroot()


def parse_xml_bytes(content: bytes) -> Any:
    """Parse XML from bytes and return root element."""
    if LXML_AVAILABLE:
        return ET.fromstring(content)
    return ET.fromstring(content.decode("utf-8"))
