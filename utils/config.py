"""
config.py
---------
Application-wide constants and configuration values.
"""

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
}

# Upload constraints
MAX_UPLOAD_SIZE_MB = 50
ALLOWED_EXTENSIONS: set[str] = {".zip", ".rar", ".xml"}

# Archive extraction: max items at root level before treating
# the entire extraction folder as the target directory
MAX_ARCHIVE_ROOT_ITEMS = 3
