"""
file_utils.py
-------------
Filesystem helpers for path sanitization, directory cleanup,
and archive extraction root detection.
"""

import logging
import os
import shutil

from werkzeug.utils import secure_filename

from utils.config import MAX_ARCHIVE_ROOT_ITEMS

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
