"""
invoice_scanner.py
------------------
Walk a directory tree of company invoice XMLs and aggregate
IBSCBS usage statistics per company (grouped by CNPJ).
"""

import logging
import os
from typing import TypedDict

from services.xml_parser import parse_invoice_xml

logger = logging.getLogger(__name__)


class InvoiceTypeStats(TypedDict):
    """Per-type (NFe / NFCe) statistics for one company."""

    tipo: str
    total_xmls: int
    xmls_com_ibs: int
    arquivos: list[tuple[str, list[str]]]
    todos_arquivos: list[str]


class CompanyResult(TypedDict):
    """Aggregated scan result for a single company."""

    empresa: str
    cnpj: str
    tipos: dict[str, InvoiceTypeStats]
    usa_ibs: bool


def scan_directory(
    root_path: str,
    verbose: bool = False,
) -> list[CompanyResult]:
    """Recursively scan *root_path* for invoice XMLs and group by company.

    Each XML is parsed for emitter identity (CNPJ + name) and IBSCBS
    tag presence.  Results are grouped by CNPJ (or company name when
    CNPJ is unavailable) and sorted alphabetically.

    Args:
        root_path: Directory to scan (contains company sub-folders).
        verbose: If ``True``, emit detailed per-file log messages.

    Returns:
        A list of ``CompanyResult`` dicts ordered by company name.

    Raises:
        FileNotFoundError: If *root_path* does not exist.
    """
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"Caminho não encontrado: {root_path}")

    company_map: dict[str, CompanyResult] = {}

    for dir_path, _dirs, files in os.walk(root_path):
        for filename in files:
            if not filename.lower().endswith(".xml"):
                continue

            full_path = os.path.join(dir_path, filename)
            data = parse_invoice_xml(full_path)

            if not data["valid"]:
                if verbose:
                    logger.info(
                        "XML ignored (malformed or invalid): %s", filename,
                    )
                continue

            company_name = data["company_name"]
            cnpj = data["cnpj"]
            invoice_type = data["invoice_type"]
            has_ibs = data["has_ibs"]
            ibs_tags = data["ibs_tags"]

            if verbose:
                logger.debug(
                    "Read: %s | Company: %s | CNPJ: %s | Type: %s | IBS: %s",
                    filename, company_name, cnpj, invoice_type, has_ibs,
                )

            # Key preferring CNPJ; falls back to name when missing
            key = cnpj if cnpj != "Desconhecido" else company_name

            if key not in company_map:
                company_map[key] = {
                    "empresa": company_name,
                    "cnpj": cnpj,
                    "tipos": {},
                    "usa_ibs": False,
                }

            company = company_map[key]

            if invoice_type not in company["tipos"]:
                company["tipos"][invoice_type] = {
                    "tipo": invoice_type,
                    "total_xmls": 0,
                    "xmls_com_ibs": 0,
                    "arquivos": [],
                    "todos_arquivos": [],
                }

            stats = company["tipos"][invoice_type]
            stats["total_xmls"] += 1
            stats["todos_arquivos"].append(filename)

            if has_ibs:
                stats["xmls_com_ibs"] += 1
                stats["arquivos"].append((filename, ibs_tags))
                company["usa_ibs"] = True

    results = list(company_map.values())
    results.sort(key=lambda r: (r["empresa"], r["cnpj"]))

    if not results and verbose:
        logger.warning(
            "No valid XML files with explicit emitter found in %s", root_path,
        )

    return results
