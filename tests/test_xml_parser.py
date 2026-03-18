"""Tests for services.xml_parser module."""

import os
import tempfile

import pytest

from services.xml_parser import parse_invoice_xml


SAMPLE_NFE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe>
      <ide>
        <mod>55</mod>
      </ide>
      <emit>
        <CNPJ>12345678000190</CNPJ>
        <xNome>Empresa Teste Ltda</xNome>
      </emit>
      <det>
        <imposto>
          <IBSCBS>
            <vIBSCBS>100.00</vIBSCBS>
          </IBSCBS>
        </imposto>
      </det>
    </infNFe>
  </NFe>
</nfeProc>
"""

SAMPLE_NFCE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe>
      <ide>
        <mod>65</mod>
      </ide>
      <emit>
        <CNPJ>98765432000101</CNPJ>
        <xNome>Loja Consumidor SA</xNome>
      </emit>
    </infNFe>
  </NFe>
</nfeProc>
"""

SAMPLE_NFS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Nfse xmlns="http://www.abrasf.org.br/nfse.xsd">
  <InfNfse>
    <PrestadorServico>
      <IdentificacaoPrestador>
        <Cnpj>12345678000195</Cnpj>
        <InscricaoMunicipal>6078885</InscricaoMunicipal>
      </IdentificacaoPrestador>
      <RazaoSocial>Empresa Teste Servicos</RazaoSocial>
    </PrestadorServico>
  </InfNfse>
</Nfse>
"""

SAMPLE_NFS_WITH_IBS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Nfse xmlns="http://www.abrasf.org.br/nfse.xsd">
  <InfNfse>
    <PrestadorServico>
      <IdentificacaoPrestador>
        <Cnpj>98765432000101</Cnpj>
      </IdentificacaoPrestador>
      <RazaoSocial>Prestadora IBS SA</RazaoSocial>
    </PrestadorServico>
    <Servico>
      <Valores>
        <IBSCBS>50.00</IBSCBS>
      </Valores>
    </Servico>
  </InfNfse>
</Nfse>
"""

SAMPLE_NO_EMIT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe>
      <ide><mod>55</mod></ide>
    </infNFe>
  </NFe>
</nfeProc>
"""


@pytest.fixture
def xml_file(tmp_path):
    """Helper to write XML content to a temp file and return the path."""
    def _write(content: str, name: str = "test.xml") -> str:
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        return str(path)
    return _write


class TestParseInvoiceXml:
    def test_valid_nfe_with_ibs(self, xml_file):
        path = xml_file(SAMPLE_NFE_XML)
        result = parse_invoice_xml(path)

        assert result["valid"] is True
        assert result["company_name"] == "Empresa Teste Ltda"
        assert result["cnpj"] == "12.345.678/0001-90"
        assert result["invoice_type"] == "NFe"
        assert result["has_ibs"] is True
        assert len(result["ibs_tags"]) > 0
        assert result["error"] is None

    def test_valid_nfce_without_ibs(self, xml_file):
        path = xml_file(SAMPLE_NFCE_XML)
        result = parse_invoice_xml(path)

        assert result["valid"] is True
        assert result["company_name"] == "Loja Consumidor SA"
        assert result["invoice_type"] == "NFCe"
        assert result["has_ibs"] is False
        assert result["ibs_tags"] == []

    def test_missing_emitter(self, xml_file):
        path = xml_file(SAMPLE_NO_EMIT_XML)
        result = parse_invoice_xml(path)

        assert result["valid"] is True
        assert result["company_name"] == "Emissor Desconhecido"
        assert result["cnpj"] == "Desconhecido"

    def test_malformed_xml(self, xml_file):
        path = xml_file("<not valid xml", name="bad.xml")
        result = parse_invoice_xml(path)

        assert result["valid"] is False
        assert result["error"] is not None

    def test_nonexistent_file(self):
        result = parse_invoice_xml("/nonexistent/path/file.xml")

        assert result["valid"] is False
        assert result["error"] is not None

    def test_cnpj_formatting_14_digits(self, xml_file):
        path = xml_file(SAMPLE_NFE_XML)
        result = parse_invoice_xml(path)
        assert result["cnpj"] == "12.345.678/0001-90"

    def test_cnpj_formatting_non_standard(self, xml_file):
        xml = SAMPLE_NFE_XML.replace("12345678000190", "123")
        path = xml_file(xml, name="short_cnpj.xml")
        result = parse_invoice_xml(path)
        # Non-14-digit CNPJ should be kept as-is
        assert result["cnpj"] == "123"

    def test_ibs_tags_detected(self, xml_file):
        path = xml_file(SAMPLE_NFE_XML)
        result = parse_invoice_xml(path)
        # Should find IBSCBS and vIBSCBS tags
        tag_names = [t for t in result["ibs_tags"] if not t.startswith("(valor)")]
        assert "IBSCBS" in tag_names or "vIBSCBS" in tag_names

    def test_nfs_invoice_type(self, xml_file):
        path = xml_file(SAMPLE_NFS_XML)
        result = parse_invoice_xml(path)

        assert result["valid"] is True
        assert result["invoice_type"] == "NFS"
        assert result["company_name"] == "Empresa Teste Servicos"
        assert result["cnpj"] == "12.345.678/0001-95"
        assert result["has_ibs"] is False
        assert result["error"] is None

    def test_nfs_with_ibs(self, xml_file):
        path = xml_file(SAMPLE_NFS_WITH_IBS_XML)
        result = parse_invoice_xml(path)

        assert result["valid"] is True
        assert result["invoice_type"] == "NFS"
        assert result["company_name"] == "Prestadora IBS SA"
        assert result["has_ibs"] is True
