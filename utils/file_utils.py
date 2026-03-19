"""
file_utils.py
-------------
Filesystem helpers for path sanitization, directory cleanup,
and archive extraction root detection.
"""

import logging
import os
import shutil
import zipfile

import rarfile

from utils.config import MAX_ARCHIVE_ROOT_ITEMS, MAX_EXTRACTED_FILES, MAX_EXTRACTED_SIZE_MB

logger = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    """Return a safe version of *name* with path separators removed.

    Uses Werkzeug's ``secure_filename`` and falls back to a generic
    name when the result would be empty (e.g. all-dots input).

    Args:
        name: Original filename from the upload.

    Returns:
        A filesystem-safe filename string.
    """
    safe = secure_filename(name)
    if not safe:
        safe = "unnamed_file"
    return safe


def find_extraction_root(extract_dir: str) -> str:
    """Determine the effective root directory inside an extracted archive.

    When an archive contains a single subfolder (and at most a few
    loose files), we treat that subfolder as the real root.  Otherwise
    we use *extract_dir* itself.

    Args:
        extract_dir: Path to the directory where the archive was extracted.

    Returns:
        The path to use as the scanning root.
    """
    items = os.listdir(extract_dir)
    subdirs = [
        item for item in items
        if os.path.isdir(os.path.join(extract_dir, item))
    ]

    if len(subdirs) == 1 and len(items) <= MAX_ARCHIVE_ROOT_ITEMS:
        return os.path.join(extract_dir, subdirs[0])

    return extract_dir


def cleanup_directory(path: str) -> None:
    """Remove a directory tree, logging any errors instead of raising.

    Args:
        path: Directory to remove.
    """
    try:
        shutil.rmtree(path, ignore_errors=False)
    except Exception:
        logger.warning("Failed to clean up directory: %s", path, exc_info=True)


def validate_archive_bomb(archive_path: str) -> None:
    """Pre-extraction zip/rar bomb protection.

    Inspects archive metadata to ensure the total uncompressed size and
    file count stay within configured limits. Raises ``ValueError`` if
    either limit is exceeded.

    Note: ZIP metadata can be forged (file_size set to 0). A second
    on-disk check after extraction is performed by
    ``validate_extracted_size``.

    Args:
        archive_path: Path to the archive file (.zip or .rar).
    """
    ext = os.path.splitext(archive_path)[1].lower()
    max_bytes = MAX_EXTRACTED_SIZE_MB * 1024 * 1024

    if ext == ".zip":
        with zipfile.ZipFile(archive_path) as zf:
            entries = zf.infolist()
            file_count = len(entries)
            total_size = sum(e.file_size for e in entries)
    elif ext == ".rar":
        with rarfile.RarFile(archive_path) as rf:
            entries = [e for e in rf.infolist() if not e.isdir()]
            file_count = len(entries)
            total_size = sum(e.file_size for e in entries)
    else:
        return

    if file_count > MAX_EXTRACTED_FILES:
        raise ValueError(
            f"O arquivo contém {file_count:,} arquivos. "
            f"O limite é {MAX_EXTRACTED_FILES:,}."
        )

    if total_size > max_bytes:
        size_mb = total_size / (1024 * 1024)
        raise ValueError(
            f"Conteúdo descompactado ({size_mb:.0f} MB) excede o limite de "
            f"{MAX_EXTRACTED_SIZE_MB} MB."
        )


def validate_extracted_size(extract_dir: str) -> None:
    """Post-extraction size check to catch forged ZIP metadata.

    Walks the extraction directory and sums actual file sizes on disk.
    Raises ``ValueError`` if the total exceeds the configured limit.

    Args:
        extract_dir: Directory that was just extracted into.
    """
    max_bytes = MAX_EXTRACTED_SIZE_MB * 1024 * 1024
    total = 0
    for dir_path, _dirs, filenames in os.walk(extract_dir):
        for fname in filenames:
            total += os.path.getsize(os.path.join(dir_path, fname))
            if total > max_bytes:
                size_mb = total / (1024 * 1024)
                raise ValueError(
                    f"Conteúdo extraído ({size_mb:.0f} MB) excede o limite de "
                    f"{MAX_EXTRACTED_SIZE_MB} MB."
                )


def validate_paths_within(base_dir: str, paths: list[str]) -> None:
    """Ensure every path in *paths* is located inside *base_dir*.

    Raises ``ValueError`` if any path escapes the base directory
    (zip-slip protection).

    Args:
        base_dir: The trusted base directory.
        paths: List of absolute file paths to verify.
    """
    real_base = os.path.realpath(base_dir)
    for p in paths:
        real_p = os.path.realpath(p)
        if not real_p.startswith(real_base + os.sep) and real_p != real_base:
            raise ValueError(
                f"Arquivo fora do diretório permitido: {os.path.basename(p)}"
            )
