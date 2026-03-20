"""Tests for Flask application routes."""

import io
import zipfile

import pytest

from app import app


@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


SAMPLE_XML = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe>
      <ide><mod>55</mod></ide>
      <emit>
        <CNPJ>12345678000190</CNPJ>
        <xNome>Test Company</xNome>
      </emit>
    </infNFe>
  </NFe>
</nfeProc>
"""


def _make_zip(xml_content: bytes = SAMPLE_XML) -> io.BytesIO:
    """Create an in-memory zip file containing a single XML."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Company/NFe/nota.xml", xml_content)
    buf.seek(0)
    return buf


class TestIndexRoute:
    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Validador" in resp.data


class TestScanRoute:
    def test_no_files(self, client):
        resp = client.post("/api/scan")
        assert resp.status_code == 400

    def test_xml_upload(self, client):
        data = {
            "files": (io.BytesIO(SAMPLE_XML), "nota.xml"),
        }
        resp = client.post(
            "/api/scan",
            data=data,
            content_type="multipart/form-data",
        )
        json_data = resp.get_json()
        assert resp.status_code == 200
        assert json_data["success"] is True
        assert "scan_id" in json_data
        assert len(json_data["resultados"]) > 0

    def test_zip_upload(self, client):
        zip_buf = _make_zip()
        data = {
            "files": (zip_buf, "archive.zip"),
        }
        resp = client.post(
            "/api/scan",
            data=data,
            content_type="multipart/form-data",
        )
        json_data = resp.get_json()
        assert resp.status_code == 200
        assert json_data["success"] is True

    def test_mixed_types_rejected(self, client):
        data = {
            "files": [
                (io.BytesIO(SAMPLE_XML), "nota.xml"),
                (_make_zip(), "archive.zip"),
            ],
        }
        resp = client.post(
            "/api/scan",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


class TestExportPdfRoute:
    def test_no_scan_id(self, client):
        resp = client.get("/api/export-pdf")
        assert resp.status_code == 400

    def test_invalid_scan_id(self, client):
        resp = client.get("/api/export-pdf?scan_id=nonexistent")
        assert resp.status_code == 400

    def test_valid_export(self, client):
        # First, perform a scan
        data = {
            "files": (io.BytesIO(SAMPLE_XML), "nota.xml"),
        }
        scan_resp = client.post(
            "/api/scan",
            data=data,
            content_type="multipart/form-data",
        )
        scan_id = scan_resp.get_json()["scan_id"]

        # Then export PDF
        resp = client.get(f"/api/export-pdf?scan_id={scan_id}")
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"
        assert resp.data[:4] == b"%PDF"
