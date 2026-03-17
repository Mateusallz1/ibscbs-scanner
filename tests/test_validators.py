"""Tests for utils.validators module."""

import xml.etree.ElementTree as ET

import pytest

from utils.validators import (
    format_cnpj,
    strip_namespace,
    validate_xml_root,
)


class TestStripNamespace:
    def test_with_namespace(self):
        assert strip_namespace("{http://example.com}tagName") == "tagName"

    def test_without_namespace(self):
        assert strip_namespace("tagName") == "tagName"

    def test_empty_string(self):
        assert strip_namespace("") == ""


class TestFormatCnpj:
    def test_valid_14_digits(self):
        assert format_cnpj("12345678000190") == "12.345.678/0001-90"

    def test_short_cnpj(self):
        assert format_cnpj("123") == "123"

    def test_long_cnpj(self):
        assert format_cnpj("123456789012345") == "123456789012345"

    def test_whitespace_stripped(self):
        assert format_cnpj("  12345678000190  ") == "12.345.678/0001-90"


class TestValidateXmlRoot:
    def test_valid_nfe_proc(self):
        root = ET.fromstring(
            '<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"></nfeProc>'
        )
        assert validate_xml_root(root) is True

    def test_valid_nfe(self):
        root = ET.fromstring("<NFe></NFe>")
        assert validate_xml_root(root) is True

    def test_invalid_root(self):
        root = ET.fromstring("<randomTag></randomTag>")
        assert validate_xml_root(root) is False
