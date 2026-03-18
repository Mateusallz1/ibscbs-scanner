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
MAX_UPLOAD_SIZE_MB = 50
ALLOWED_EXTENSIONS: set[str] = {".zip", ".rar", ".xml"}

# Archive extraction: max items at root level before treating
# the entire extraction folder as the target directory
MAX_ARCHIVE_ROOT_ITEMS = 3
