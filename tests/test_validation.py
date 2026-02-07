"""Tests for validation module."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from netex2lc.validation import (
    validate_xml_wellformed,
    detect_format,
    detect_siri_profile,
    validate_netex_structure,
    validate_siri_structure,
    validate_input,
)


class TestXMLValidation:
    """Tests for XML validation functions."""

    def test_validate_wellformed_valid(self, siri_et_response_path: str):
        """Test validating well-formed XML."""
        is_valid, error = validate_xml_wellformed(siri_et_response_path)
        assert is_valid is True
        assert error is None

    def test_validate_wellformed_invalid(self):
        """Test validating malformed XML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_xml = Path(tmpdir) / "bad.xml"
            bad_xml.write_text("<root><unclosed>")

            is_valid, error = validate_xml_wellformed(str(bad_xml))
            assert is_valid is False
            assert error is not None

    def test_validate_wellformed_nonexistent(self):
        """Test validating non-existent file."""
        is_valid, error = validate_xml_wellformed("/nonexistent/file.xml")
        assert is_valid is False


class TestFormatDetection:
    """Tests for format detection."""

    def test_detect_siri_format(self, siri_et_response_path: str):
        """Test detecting SIRI format."""
        fmt = detect_format(siri_et_response_path)
        assert fmt == "siri"

    def test_detect_netex_format(self, simple_timetable_path: str):
        """Test detecting NeTEx format."""
        fmt = detect_format(simple_timetable_path)
        assert fmt == "netex"

    def test_detect_unknown_format(self):
        """Test detecting unknown format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            unknown_xml = Path(tmpdir) / "unknown.xml"
            unknown_xml.write_text('<?xml version="1.0"?><random>data</random>')

            fmt = detect_format(str(unknown_xml))
            assert fmt is None


class TestSIRIProfileDetection:
    """Tests for SIRI profile detection."""

    def test_detect_et_profile(self, siri_et_response_path: str):
        """Test detecting SIRI-ET profile."""
        profile = detect_siri_profile(siri_et_response_path)
        assert profile == "et"

    def test_detect_vm_profile(self, siri_vm_response_path: str):
        """Test detecting SIRI-VM profile."""
        profile = detect_siri_profile(siri_vm_response_path)
        assert profile == "vm"

    def test_detect_sx_profile(self, siri_sx_response_path: str):
        """Test detecting SIRI-SX profile."""
        profile = detect_siri_profile(siri_sx_response_path)
        assert profile == "sx"


class TestStructureValidation:
    """Tests for structure validation."""

    def test_validate_netex_structure(self, simple_timetable_path: str):
        """Test NeTEx structure validation."""
        warnings = validate_netex_structure(simple_timetable_path)
        # May have warnings depending on file content
        assert isinstance(warnings, list)

    def test_validate_siri_structure(self, siri_et_response_path: str):
        """Test SIRI structure validation."""
        warnings = validate_siri_structure(siri_et_response_path, profile="et")
        assert isinstance(warnings, list)


class TestValidateInput:
    """Tests for validate_input function."""

    def test_validate_existing_file(self, siri_et_response_path: str):
        """Test validating an existing valid file."""
        result = validate_input(siri_et_response_path)
        assert result is True

    def test_validate_nonexistent_file(self):
        """Test validating a non-existent file."""
        result = validate_input("/nonexistent/file.xml", strict=False)
        assert result is False

    def test_validate_strict_mode(self):
        """Test validation in strict mode raises exception."""
        from netex2lc.logging_config import ValidationError

        with pytest.raises(ValidationError):
            validate_input("/nonexistent/file.xml", strict=True)
