"""
xml_parser.py
-------------
Parse Brazilian electronic invoice XMLs (NFe / NFCe) and extract
emitter information and IBSCBS tax field presence.
"""

import logging
import xml.etree.ElementTree as ET
from typing import TypedDict

from utils.config import IBS_TAGS, INVOICE_MODEL_NFE, INVOICE_MODEL_NFCE, INVOICE_TYPE_NFS
from utils.validators import format_cnpj, strip_namespace, validate_xml_root

logger = logging.getLogger(__name__)


class InvoiceData(TypedDict):
    """Schema for a single parsed invoice XML."""

    valid: bool
    company_name: str
    cnpj: str
    invoice_type: str  # "NFe" | "NFCe" | "Unknown"
    has_ibs: bool
    ibs_tags: list[str]
    error: str | None


def parse_invoice_xml(filepath: str) -> InvoiceData:
    """Parse an NFe/NFCe XML file and extract relevant data.

    Extracts:
    - Emitter company name (``<emit><xNome>``)
    - Emitter CNPJ (``<emit><CNPJ>``)
    - Invoice type from ``<ide><mod>`` (55 = NFe, 65 = NFCe)
    - Whether any IBSCBS-related tags are present

    All data is collected in a single pass over the element tree.

    Args:
        filepath: Absolute path to the XML file.

    Returns:
        An ``InvoiceData`` dict with the extracted fields.
    """
    result: InvoiceData = {
        "valid": False,
        "company_name": "Emissor Desconhecido",
        "cnpj": "Desconhecido",
        "invoice_type": "Desconhecido",
        "has_ibs": False,
        "ibs_tags": [],
        "error": None,
    }

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError as exc:
        logger.warning("XML parse error in %s: %s", filepath, exc)
        result["error"] = str(exc)
        return result
    except OSError as exc:
        logger.warning("Cannot read file %s: %s", filepath, exc)
        result["error"] = str(exc)
        return result

    root_tag_local = strip_namespace(root.tag)
    # NFS files can be wrapped in many root tags (ConsultarNfseResposta,
    # ListaNotaFiscal, CompNfse, Nfse, etc.).  The reliable signal is the
    # presence of a <Nfse> element anywhere in the tree.
    _NFS_ROOT_TAGS = {"Nfse", "CompNfse", "ListaNfse", "ConsultarNfseResposta", "ListaNotaFiscal"}
    is_nfse = root_tag_local in _NFS_ROOT_TAGS or any(
        strip_namespace(e.tag) == "Nfse" for e in root.iter()
    )

    if not validate_xml_root(root):
        logger.debug(
            "Unrecognised root element '%s' in %s — processing anyway",
            root_tag_local, filepath,
        )

    result["valid"] = True

    # --- Single-pass collection ---
    emitter_name = ""
    emitter_cnpj = ""
    invoice_model = ""
    ibs_tags_found: list[str] = []

    for elem in root.iter():
        local_tag = strip_namespace(elem.tag)

        if is_nfse:
            # NFS: company info lives in <PrestadorServico>
            # <RazaoSocial> is a direct child; <Cnpj> may be nested inside
            # <IdentificacaoPrestador> — use iter() to find both at any depth.
            if local_tag == "PrestadorServico":
                for descendant in elem.iter():
                    desc_tag = strip_namespace(descendant.tag)
                    if desc_tag == "RazaoSocial" and descendant.text and not emitter_name:
                        emitter_name = descendant.text.strip()
                    elif desc_tag == "Cnpj" and descendant.text and not emitter_cnpj:
                        raw_cnpj = descendant.text.strip()
                        if len(raw_cnpj) != 14:
                            logger.warning(
                                "Malformed CNPJ '%s' in %s", raw_cnpj, filepath,
                            )
                        emitter_cnpj = format_cnpj(raw_cnpj)
        else:
            # NFe/NFCe: company info in <emit>, model code in <ide><mod>
            if local_tag == "emit":
                for child in elem:
                    child_tag = strip_namespace(child.tag)
                    if child_tag == "xNome" and child.text:
                        emitter_name = child.text.strip()
                    elif child_tag == "CNPJ" and child.text:
                        raw_cnpj = child.text.strip()
                        if len(raw_cnpj) != 14:
                            logger.warning(
                                "Malformed CNPJ '%s' in %s", raw_cnpj, filepath,
                            )
                        emitter_cnpj = format_cnpj(raw_cnpj)

            elif local_tag == "ide" and not invoice_model:
                for child in elem:
                    child_tag = strip_namespace(child.tag)
                    if child_tag == "mod" and child.text:
                        invoice_model = child.text.strip()
                        break

        # IBS tag detection (by tag name)
        if any(ibs.lower() in local_tag.lower() for ibs in IBS_TAGS):
            if local_tag not in ibs_tags_found:
                ibs_tags_found.append(local_tag)

        # IBS detection in text content and attribute values
        combined_text = (elem.text or "") + " ".join(elem.attrib.values())
        for ibs in IBS_TAGS:
            label = f"(valor) {ibs}"
            if ibs in combined_text and label not in ibs_tags_found:
                ibs_tags_found.append(label)

    # Populate result
    if emitter_name:
        result["company_name"] = emitter_name
    if emitter_cnpj:
        result["cnpj"] = emitter_cnpj

    # Resolve invoice type
    if is_nfse:
        result["invoice_type"] = INVOICE_TYPE_NFS
    elif invoice_model == INVOICE_MODEL_NFE:
        result["invoice_type"] = "NFe"
    elif invoice_model == INVOICE_MODEL_NFCE:
        result["invoice_type"] = "NFCe"
    else:
        # Heuristic fallback: check tag names — "nfse" must come before "nfe"
        for elem in root.iter():
            local_tag = strip_namespace(elem.tag)
            if "nfse" in local_tag.lower():
                result["invoice_type"] = INVOICE_TYPE_NFS
                break
            elif "nfce" in local_tag.lower():
                result["invoice_type"] = "NFCe"
                break
            elif "nfe" in local_tag.lower():
                result["invoice_type"] = "NFe"
                break

    if ibs_tags_found:
        result["has_ibs"] = True
        result["ibs_tags"] = ibs_tags_found

    return result
