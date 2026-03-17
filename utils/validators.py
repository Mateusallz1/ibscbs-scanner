"""
validators.py
-------------
Input validation helpers for uploads and XML structures.
"""

import xml.etree.ElementTree as ET

from utils.config import ALLOWED_EXTENSIONS, VALID_XML_ROOTS


# Magic byte signatures for supported archive/XML formats
_MAGIC_BYTES: dict[str, list[bytes]] = {
    ".zip": [b"PK"],
    ".rar": [b"Rar!"],
    ".xml": [b"<?xml", b"\xef\xbb\xbf<?xml", b"\xef\xbb\xbf<", b"<"],  # XML declaration, BOM, or direct root element
}


def validate_uploaded_files(
    files: list,
) -> tuple[list, list]:
    """Categorise and validate uploaded files.

    Rules enforced:
    - Only ``.zip``, ``.rar``, and ``.xml`` extensions are accepted.
    - Archives and XMLs must not be mixed in the same request.
    - At most one archive file is allowed per request.
    - File magic bytes must match the declared extension.

    Args:
        files: List of ``FileStorage`` objects from Flask request.

    Returns:
        A tuple ``(archives, xmls)`` of validated file lists.

    Raises:
        ValueError: When any validation rule is violated.
    """
    if not files or all(f.filename == "" for f in files):
        raise ValueError("Nenhum arquivo selecionado.")

    archives: list = []
    xmls: list = []
    invalid: list[str] = []

    for f in files:
        ext = _file_extension(f.filename)
        if ext not in ALLOWED_EXTENSIONS:
            invalid.append(f.filename or "unnamed")
        elif ext in {".zip", ".rar"}:
            archives.append(f)
        else:
            xmls.append(f)

    if invalid:
        raise ValueError(
            "Arquivos inválidos: "
            + ", ".join(invalid)
            + ". Apenas .zip, .rar e .xml são suportados."
        )

    if archives and xmls:
        raise ValueError(
            "Não é permitido misturar arquivos compactados (.zip/.rar) "
            "e arquivos XML. Envie apenas um tipo."
        )

    if len(archives) > 1:
        raise ValueError(
            "Envie apenas um arquivo compactado (.zip ou .rar). "
            "Para múltiplos XMLs, envie-os separadamente."
        )

    # Validate magic bytes
    for f in archives + xmls:
        ext = _file_extension(f.filename)
        _validate_magic_bytes(f, ext)

    return archives, xmls


def validate_xml_root(root: ET.Element) -> bool:
    """Check whether *root* has a recognised NFe/NFCe root tag.

    Args:
        root: The root ``Element`` of a parsed XML tree.

    Returns:
        ``True`` if the root tag (ignoring namespace) is a known
        invoice element.
    """
    tag_local = strip_namespace(root.tag)
    return tag_local in VALID_XML_ROOTS


def strip_namespace(tag: str) -> str:
    """Remove the XML namespace prefix from *tag*.

    Example::

        strip_namespace("{http://www.portalfiscal.inf.br/nfe}nfeProc")
        # => "nfeProc"

    Args:
        tag: A potentially namespace-qualified XML tag string.

    Returns:
        The local name portion of the tag.
    """
    if "}" in tag:
        return tag.split("}")[-1]
    return tag


def format_cnpj(raw: str) -> str:
    """Format a raw 14-digit CNPJ string into the standard display form.

    Args:
        raw: Raw CNPJ string (digits only).

    Returns:
        Formatted CNPJ (e.g. ``12.345.678/0001-90``) or the original
        string if it is not exactly 14 characters.
    """
    raw = raw.strip()
    if len(raw) == 14:
        return f"{raw[0:2]}.{raw[2:5]}.{raw[5:8]}/{raw[8:12]}-{raw[12:14]}"
    return raw


# --- private helpers ---

def _file_extension(filename: str | None) -> str:
    """Return the lowercased file extension including the dot."""
    if not filename:
        return ""
    dot = filename.rfind(".")
    if dot == -1:
        return ""
    return filename[dot:].lower()


def _validate_magic_bytes(file_storage, ext: str) -> None:
    """Read the first bytes of *file_storage* and verify magic signature.

    The file stream position is reset after reading.

    Raises:
        ValueError: If the magic bytes do not match the extension.
    """
    expected_signatures = _MAGIC_BYTES.get(ext)
    if not expected_signatures:
        return

    max_len = max(len(sig) for sig in expected_signatures)
    header = file_storage.stream.read(max_len)
    file_storage.stream.seek(0)

    if not any(header.startswith(sig) for sig in expected_signatures):
        raise ValueError(
            f"O conteúdo do arquivo '{file_storage.filename}' não corresponde "
            f"ao formato esperado ({ext})."
        )
