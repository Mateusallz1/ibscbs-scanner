"""
debug_rar.py
------------
Debug utility for testing RAR extraction and XML parsing pipeline.

Usage::

    python -m tests.debug_rar <path_to_rar_file>
"""

import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

try:
    import patoolib
except ImportError:
    import patool as patoolib  # type: ignore[no-redef]

# Ensure project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.invoice_scanner import scan_directory  # noqa: E402


def test_rar(filepath: str) -> None:
    """Extract a RAR file and compare manual XML scan with pipeline output."""
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"Extracting {filepath} to {temp_dir}")
        patoolib.extract_archive(filepath, outdir=temp_dir, interactive=False)

        xml_files = []
        for root, _dirs, files in os.walk(temp_dir):
            for f in files:
                if f.lower().endswith(".xml"):
                    xml_files.append(os.path.join(root, f))

        print(f"Total XMLs found via os.walk: {len(xml_files)}")

        unique_companies: set[str] = set()
        for xml_path in xml_files:
            try:
                tree = ET.parse(xml_path)
                root_elem = tree.getroot()
                for el in root_elem.iter():
                    tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                    if tag == "emit":
                        for child in el:
                            ct = (
                                child.tag.split("}")[-1]
                                if "}" in child.tag
                                else child.tag
                            )
                            if ct == "xNome" and child.text:
                                unique_companies.add(child.text.strip())
                                break
                        break
            except Exception as exc:
                print(f"Error parsing {os.path.basename(xml_path)}: {exc}")

        print(f"Unique companies found: {len(unique_companies)}")
        print("Listing:")
        for company in sorted(unique_companies):
            print(f"- {company}")

        print("-------------------------------")
        results = scan_directory(temp_dir, verbose=False)
        print(f"Results via scan_directory: {len(results)}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_rar_file>")
        sys.exit(1)
    test_rar(sys.argv[1])
