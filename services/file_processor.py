"""
file_processor.py
-----------------
Handle uploaded files: save to temporary directory, extract archives,
and prepare the directory tree for scanning.
"""

import logging
import os
import tempfile
import zipfile

try:
    import patoolib
except ImportError:
    import patool as patoolib  # type: ignore[no-redef]

from utils.file_utils import (
    cleanup_directory,
    find_extraction_root,
    sanitize_filename,
    validate_paths_within,
)
from utils.validators import validate_uploaded_files

logger = logging.getLogger(__name__)


def process_upload(files: list) -> tuple[str, str]:
    """Validate, save, and extract uploaded files.

    Args:
        files: List of ``FileStorage`` objects from the Flask request.

    Returns:
        A tuple ``(temp_dir, target_dir)`` where *temp_dir* is the
        temporary directory to clean up later and *target_dir* is the
        path to scan for invoices.

    Raises:
        ValueError: On invalid input (wrong extension, mixed types, etc.).
    """
    archives, xmls = validate_uploaded_files(files)

    temp_dir = tempfile.mkdtemp()

    try:
        if archives:
            target_dir = _extract_archive(archives[0], temp_dir)
        else:
            target_dir = _save_loose_xmls(xmls, temp_dir)
    except Exception:
        cleanup_directory(temp_dir)
        raise

    return temp_dir, target_dir


def _extract_archive(archive, temp_dir: str) -> str:
    """Save and extract a single archive file.

    After extraction, validates that all resulting files are within
    the temporary directory (zip-slip protection).
    """
    safe_name = sanitize_filename(archive.filename)
    archive_path = os.path.join(temp_dir, safe_name)
    archive.save(archive_path)

    extract_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(extract_dir, exist_ok=True)

    if safe_name.lower().endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)
    elif safe_name.lower().endswith(".rar"):
        patoolib.extract_archive(
            archive_path, outdir=extract_dir, interactive=False,
        )

    # Zip-slip protection: ensure all extracted files stay inside temp_dir
    extracted_paths = []
    for dir_path, _dirs, filenames in os.walk(extract_dir):
        for fname in filenames:
            extracted_paths.append(os.path.join(dir_path, fname))

    validate_paths_within(temp_dir, extracted_paths)

    return find_extraction_root(extract_dir)


def _save_loose_xmls(xmls: list, temp_dir: str) -> str:
    """Save individual XML files into a company sub-folder."""
    company_dir = os.path.join(temp_dir, "Empresa_Avulsa")
    nfe_dir = os.path.join(company_dir, "NFe")
    os.makedirs(nfe_dir, exist_ok=True)

    for xml_file in xmls:
        safe_name = sanitize_filename(xml_file.filename)
        xml_file.save(os.path.join(nfe_dir, safe_name))

    return temp_dir
