# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask web application that scans Brazilian electronic invoice XML files (NFe/NFCe) to detect usage of the IBSCBS tax field across companies. Users upload `.zip`, `.rar`, or individual `.xml` files via a drag-and-drop web UI, and the app reports which companies include IBSCBS tags in their invoices. Results can be exported as a styled PDF report.

## Running the App

```bash
pip install -r requirements.txt
python app.py
# Access at http://127.0.0.1:5000
```

Python 3.13+ (see `runtime.txt`). RAR extraction requires `patool`/`patoolib` and an external `unrar` tool on the system PATH.

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Architecture

```
REFORMA/
  app.py                    # Flask routes (thin handlers delegating to services)
  ConfereEmpresa.py         # CLI shim (backward-compatible, delegates to services)
  relatorio_pdf.py          # PDF report generation via WeasyPrint
  services/
    xml_parser.py           # parse_invoice_xml() — single-pass XML parsing
    invoice_scanner.py      # scan_directory() — walk tree, group by CNPJ
    file_processor.py       # process_upload() — validate, save, extract uploads
  utils/
    config.py               # Constants (IBS_TAGS, invoice model codes, limits)
    validators.py           # Input validation (files, XML roots, CNPJ formatting)
    file_utils.py           # Path sanitization, zip-slip protection, cleanup
  static/                   # Vanilla JS + Material 3 dark theme CSS
  templates/                # Single-page Jinja2 template
  tests/                    # pytest test suite
```

**Data flow:** Upload → `file_processor.process_upload()` (validates, extracts to temp dir) → `invoice_scanner.scan_directory()` (walks tree, calls `xml_parser.parse_invoice_xml()` per file, groups by CNPJ) → JSON response with `scan_id` → JS renders dashboard. PDF export uses `scan_id` to retrieve stored results.

**Scan result storage:** Results are stored in-memory keyed by UUID (`scan_id`) with a 1-hour TTL, protected by `threading.Lock`. The frontend passes `scan_id` to `/api/export-pdf`.

**CLI usage:** `python ConfereEmpresa.py <path> [--verbose] [--exportar file.txt]` — delegates to `services.invoice_scanner.scan_directory()`.

## Key Data Structures

`scan_directory()` returns `list[CompanyResult]`:
```python
{
    "empresa": str,          # Company name from <emit><xNome>
    "cnpj": str,             # Formatted CNPJ or "Desconhecido"
    "tipos": {               # Keyed by "NFe" | "NFCe" | "Desconhecido"
        "NFe": {
            "total_xmls": int,
            "xmls_com_ibs": int,
            "arquivos": [(filename, [tag_names])],  # files WITH IBSCBS
            "todos_arquivos": [filename],            # all files
        }
    },
    "usa_ibs": bool,         # True if any XML has IBSCBS
}
```

## Coding Conventions (from `.github/copilot-instructions.md`)

- **English-only code** (variable names, function names, comments). Portuguese only for user-facing strings.
- PEP 8, snake_case for functions/variables, PascalCase for classes.
- XML namespace handling uses `strip_namespace()` from `utils/validators.py`.
- All user-provided strings are escaped before HTML insertion (XSS protection via `markupsafe.escape` in PDF, `escapeHtml()` in JS).
- Uploaded filenames are sanitized via `werkzeug.utils.secure_filename`.
- Flask route handlers are thin — business logic lives in `services/`.
- Use `logging` module (not `print()`).
