"""XML validation utilities for NeTEx and SIRI files."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from lxml import etree

from .logging_config import ValidationError, get_logger

logger = get_logger()

# NeTEx namespace
NETEX_NS = "http://www.netex.org.uk/netex"
# SIRI namespace
SIRI_NS = "http://www.siri.org.uk/siri"


def validate_xml_wellformed(path: str) -> Tuple[bool, Optional[str]]:
    """Check if XML file is well-formed.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        etree.parse(path)
        return True, None
    except etree.XMLSyntaxError as e:
        return False, f"XML syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"


def detect_format(path: str) -> Optional[str]:
    """Detect whether file is NeTEx or SIRI format.

    Returns:
        'netex', 'siri', or None if unknown
    """
    try:
        tree = etree.parse(path)
        root = tree.getroot()
        ns = root.nsmap.get(None, "")

        if "netex" in ns.lower() or root.tag.endswith("PublicationDelivery"):
            return "netex"
        if "siri" in ns.lower() or root.tag.endswith("Siri"):
            return "siri"

        # Check for common root elements
        local_tag = etree.QName(root).localname
        if local_tag in ("PublicationDelivery", "CompositeFrame", "TimetableFrame"):
            return "netex"
        if local_tag in ("Siri", "ServiceDelivery"):
            return "siri"

        return None
    except Exception:
        return None


def detect_siri_profile(path: str) -> Optional[str]:
    """Detect SIRI profile type (ET, VM, SX).

    Returns:
        'et', 'vm', 'sx', or None if unknown
    """
    try:
        tree = etree.parse(path)
        root = tree.getroot()

        # Convert to string for simple detection
        xml_str = etree.tostring(root, encoding="unicode")[:5000]

        if "EstimatedTimetableDelivery" in xml_str or "EstimatedVehicleJourney" in xml_str:
            return "et"
        if "VehicleMonitoringDelivery" in xml_str or "VehicleActivity" in xml_str:
            return "vm"
        if "SituationExchangeDelivery" in xml_str or "PtSituationElement" in xml_str:
            return "sx"
        if "StopMonitoringDelivery" in xml_str:
            return "sm"

        return None
    except Exception:
        return None


def validate_netex_structure(path: str) -> List[str]:
    """Validate basic NeTEx structure.

    Returns list of warnings (empty if valid).
    """
    warnings = []
    try:
        tree = etree.parse(path)
        root = tree.getroot()

        # Check for required elements
        has_service_journeys = False
        has_passing_times = False

        for elem in root.iter():
            local = etree.QName(elem).localname
            if local == "ServiceJourney":
                has_service_journeys = True
            if local in ("TimetabledPassingTime", "PassingTime", "Call"):
                has_passing_times = True

        if not has_service_journeys:
            warnings.append("No ServiceJourney elements found - file may not contain timetable data")
        if not has_passing_times:
            warnings.append("No PassingTime/Call elements found - connections cannot be generated")

    except Exception as e:
        warnings.append(f"Error validating structure: {e}")

    return warnings


def validate_siri_structure(path: str, profile: Optional[str] = None) -> List[str]:
    """Validate basic SIRI structure.

    Returns list of warnings (empty if valid).
    """
    warnings = []
    try:
        tree = etree.parse(path)
        root = tree.getroot()

        detected_profile = detect_siri_profile(path)
        if profile and detected_profile and profile != detected_profile:
            warnings.append(
                f"Specified profile '{profile}' doesn't match detected profile '{detected_profile}'"
            )

        if detected_profile == "et":
            has_journeys = any(
                etree.QName(e).localname == "EstimatedVehicleJourney" for e in root.iter()
            )
            if not has_journeys:
                warnings.append("No EstimatedVehicleJourney elements found")

        elif detected_profile == "vm":
            has_activities = any(
                etree.QName(e).localname == "VehicleActivity" for e in root.iter()
            )
            if not has_activities:
                warnings.append("No VehicleActivity elements found")

        elif detected_profile == "sx":
            has_situations = any(
                etree.QName(e).localname == "PtSituationElement" for e in root.iter()
            )
            if not has_situations:
                warnings.append("No PtSituationElement found")

    except Exception as e:
        warnings.append(f"Error validating structure: {e}")

    return warnings


def validate_input(path: str, strict: bool = False) -> bool:
    """Validate input file.

    Args:
        path: Path to XML file
        strict: If True, raise ValidationError on issues

    Returns:
        True if valid, False otherwise
    """
    # Check file exists
    if not Path(path).exists():
        msg = f"File not found: {path}"
        if strict:
            raise ValidationError(msg)
        logger.error(msg)
        return False

    # Check well-formed XML
    is_valid, error = validate_xml_wellformed(path)
    if not is_valid:
        if strict:
            raise ValidationError(error)
        logger.error(error)
        return False

    # Detect format
    fmt = detect_format(path)
    if fmt is None:
        msg = f"Could not detect format (NeTEx/SIRI) for: {path}"
        logger.warning(msg)

    # Format-specific validation
    if fmt == "netex":
        warnings = validate_netex_structure(path)
    elif fmt == "siri":
        warnings = validate_siri_structure(path)
    else:
        warnings = []

    for warning in warnings:
        logger.warning(warning)

    return True
