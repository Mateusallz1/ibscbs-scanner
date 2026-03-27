"""
config.py
---------
Application-wide constants and configuration values.
"""

import os

# IBS tag names to search for in invoice XMLs
IBS_TAGS: list[str] = [
    "IBSCBS",
    "ibscbs",
    "vIBSCBS",
    "pIBSCBS",
    "cIBSCBS",
    "indIBSCBS",
]

# Invoice model codes from <ide><mod> element
INVOICE_MODEL_NFE = "55"
INVOICE_MODEL_NFCE = "65"

# Invoice type label for NFS (identified by root tag, not <ide><mod>)
INVOICE_TYPE_NFS = "NFS"

# Valid root element local names for Brazilian electronic invoices
VALID_XML_ROOTS: set[str] = {
    "nfeProc",
    "NFe",
    "enviNFe",
    "nfceProc",
    "NFCe",
    "enviNFCe",
    "procEventoNFe",
    "retEnviNFe",
    "Nfse",
    "CompNfse",
    "ListaNfse",
    "ConsultarNfseResposta",
    "ListaNotaFiscal",
}

# Upload constraints
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 50))
ALLOWED_EXTENSIONS: set[str] = {".zip", ".rar", ".xml"}

# Concurrency: max number of /api/scan requests processed simultaneously.
# Requests that arrive while the limit is reached receive HTTP 429.
MAX_CONCURRENT_SCANS = int(os.environ.get("MAX_CONCURRENT_SCANS", 3))

# Archive bomb protection
MAX_EXTRACTED_SIZE_MB = int(os.environ.get("MAX_EXTRACTED_SIZE_MB", 200))
MAX_EXTRACTED_FILES = 10_000   # max number of files inside the archive

# Archive extraction: max items at root level before treating
# the entire extraction folder as the target directory
MAX_ARCHIVE_ROOT_ITEMS = 3

# Google Apps Script URL for lead capture
GOOGLE_SCRIPT_URL = os.environ.get(
    "GOOGLE_SCRIPT_URL",
    "https://script.google.com/macros/s/"
    "AKfycbwZEB-ADXbxM3RO3iqg8XYaYAnuwMboKU3VirLBb7rTVqFlsbZx6FDkOUbnufYQ4TaO7w/exec",
)
