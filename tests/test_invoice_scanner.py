"""Tests for services.invoice_scanner module."""

import os

import pytest

from services.invoice_scanner import scan_directory


SAMPLE_NFE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe>
      <ide><mod>55</mod></ide>
      <emit>
        <CNPJ>11222333000181</CNPJ>
        <xNome>Empresa Alpha</xNome>
      </emit>
      <det><imposto><IBSCBS><vIBSCBS>50</vIBSCBS></IBSCBS></imposto></det>
    </infNFe>
  </NFe>
</nfeProc>
"""

SAMPLE_NFCE_NO_IBS = """\
<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe>
      <ide><mod>65</mod></ide>
      <emit>
        <CNPJ>99888777000166</CNPJ>
        <xNome>Empresa Beta</xNome>
      </emit>
    </infNFe>
  </NFe>
</nfeProc>
"""


@pytest.fixture
def sample_tree(tmp_path):
    """Create a directory tree with two companies."""
    alpha_dir = tmp_path / "Empresa Alpha" / "NFe"
    alpha_dir.mkdir(parents=True)
    (alpha_dir / "nota1.xml").write_text(SAMPLE_NFE_XML, encoding="utf-8")

    beta_dir = tmp_path / "Empresa Beta" / "NFCe"
    beta_dir.mkdir(parents=True)
    (beta_dir / "nota2.xml").write_text(SAMPLE_NFCE_NO_IBS, encoding="utf-8")

    return tmp_path


class TestScanDirectory:
    def test_finds_all_companies(self, sample_tree):
        results = scan_directory(str(sample_tree))
        assert len(results) == 2

    def test_identifies_ibs_usage(self, sample_tree):
        results = scan_directory(str(sample_tree))
        with_ibs = [r for r in results if r["usa_ibs"]]
        without_ibs = [r for r in results if not r["usa_ibs"]]

        assert len(with_ibs) == 1
        assert len(without_ibs) == 1
        assert with_ibs[0]["empresa"] == "Empresa Alpha"
        assert without_ibs[0]["empresa"] == "Empresa Beta"

    def test_groups_by_cnpj(self, sample_tree):
        # Add a second XML for the same company (same CNPJ)
        extra_dir = sample_tree / "Alpha Branch" / "NFCe"
        extra_dir.mkdir(parents=True)
        (extra_dir / "nota3.xml").write_text(SAMPLE_NFE_XML, encoding="utf-8")

        results = scan_directory(str(sample_tree))
        # Should still be 2 companies (Alpha grouped by CNPJ)
        assert len(results) == 2

    def test_nonexistent_path_raises(self):
        with pytest.raises(FileNotFoundError):
            scan_directory("/nonexistent/path/xyz")

    def test_empty_directory(self, tmp_path):
        results = scan_directory(str(tmp_path))
        assert results == []

    def test_sorted_by_company_name(self, sample_tree):
        results = scan_directory(str(sample_tree))
        names = [r["empresa"] for r in results]
        assert names == sorted(names)
