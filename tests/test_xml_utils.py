"""Tests for XML utilities module."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from netex2lc.xml_utils import (
    local_name,
    get_namespace,
    iter_elements,
    find_first,
    find_text,
    find_ref,
    parse_xml,
    LXML_AVAILABLE,
)


class TestLocalName:
    """Tests for local_name function."""

    def test_local_name_with_namespace(self):
        """Test extracting local name from namespaced tag."""
        assert local_name("{http://example.org}Element") == "Element"

    def test_local_name_without_namespace(self):
        """Test extracting local name from non-namespaced tag."""
        assert local_name("Element") == "Element"

    def test_local_name_empty(self):
        """Test with empty string."""
        assert local_name("") == ""

    def test_local_name_non_string(self):
        """Test with non-string input."""
        assert local_name(None) == ""
        assert local_name(123) == ""


class TestGetNamespace:
    """Tests for get_namespace function."""

    def test_get_namespace_present(self):
        """Test extracting namespace from tag."""
        ns = get_namespace("{http://example.org}Element")
        assert ns == "http://example.org"

    def test_get_namespace_absent(self):
        """Test with no namespace."""
        ns = get_namespace("Element")
        assert ns is None


class TestIterElements:
    """Tests for iter_elements function."""

    def test_iter_elements_finds_matching(self):
        """Test finding elements by local name."""
        xml_content = """<?xml version="1.0"?>
        <Root xmlns="http://example.org">
            <Child>First</Child>
            <Child>Second</Child>
            <Other>Third</Other>
        </Root>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "test.xml"
            xml_path.write_text(xml_content)

            root = parse_xml(str(xml_path))
            children = list(iter_elements(root, "Child"))

            assert len(children) == 2


class TestFindFirst:
    """Tests for find_first function."""

    def test_find_first_single_name(self):
        """Test finding first element with single name."""
        xml_content = """<?xml version="1.0"?>
        <Root>
            <Child>First</Child>
            <Child>Second</Child>
        </Root>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "test.xml"
            xml_path.write_text(xml_content)

            root = parse_xml(str(xml_path))
            child = find_first(root, ["Child"])

            assert child is not None
            assert child.text == "First"

    def test_find_first_multiple_names(self):
        """Test finding first element with multiple possible names."""
        xml_content = """<?xml version="1.0"?>
        <Root>
            <AltName>Found</AltName>
        </Root>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "test.xml"
            xml_path.write_text(xml_content)

            root = parse_xml(str(xml_path))
            elem = find_first(root, ["Name", "AltName", "OtherName"])

            assert elem is not None
            assert elem.text == "Found"


class TestFindText:
    """Tests for find_text function."""

    def test_find_text_exists(self):
        """Test finding text content."""
        xml_content = """<?xml version="1.0"?>
        <Root>
            <Name>Test Value</Name>
        </Root>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "test.xml"
            xml_path.write_text(xml_content)

            root = parse_xml(str(xml_path))
            text = find_text(root, ["Name"])

            assert text == "Test Value"

    def test_find_text_not_exists(self):
        """Test when text not found."""
        xml_content = """<?xml version="1.0"?>
        <Root></Root>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "test.xml"
            xml_path.write_text(xml_content)

            root = parse_xml(str(xml_path))
            text = find_text(root, ["Name"])

            assert text is None


class TestFindRef:
    """Tests for find_ref function."""

    def test_find_ref_attribute(self):
        """Test finding ref attribute."""
        xml_content = """<?xml version="1.0"?>
        <Root>
            <StopRef ref="STOP123"/>
        </Root>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "test.xml"
            xml_path.write_text(xml_content)

            root = parse_xml(str(xml_path))
            ref = find_ref(root, ["StopRef"])

            assert ref == "STOP123"

    def test_find_ref_text_fallback(self):
        """Test finding ref from text content."""
        xml_content = """<?xml version="1.0"?>
        <Root>
            <StopRef>STOP456</StopRef>
        </Root>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "test.xml"
            xml_path.write_text(xml_content)

            root = parse_xml(str(xml_path))
            ref = find_ref(root, ["StopRef"])

            assert ref == "STOP456"


class TestLxmlAvailability:
    """Tests for lxml availability."""

    def test_lxml_is_available(self):
        """Test that lxml is available (required dependency)."""
        assert LXML_AVAILABLE is True
