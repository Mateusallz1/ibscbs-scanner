---
name: "reforma-xmlscanner"
description: "Workspace-wide coding guidelines. Use when: writing Python, handling XML files, creating Flask routes, or organizing project structure in this REFORMA XML scanner project."
applies_globally: true
---

# REFORMA XML Scanner — Coding Guidelines

## Code Style & Language

- **Use English-only code**: All variable names, function names, class names, and code comments must be in English. This ensures consistency and maintainability across the codebase.
- **Portuguese** may appear in user-facing strings (UI, API responses, error messages).
- Follow **PEP 8** for Python code formatting.
- Use **snake_case** for functions and variables, **PascalCase** for classes.
- Avoid single-letter variable names except in loops (`i`, `j`, `k`). Use descriptive names like `invoice`, `element`, `namespace`.

## XML Handling — Strict Validation

**All XML parsing must include error handling and validation:**

1. **Namespace handling**: Always account for XML namespaces when using ElementTree. Use namespace maps or wildcard matching (`.//{}`).
2. **Validation**: Before processing XML, validate structure:
   - Check required root elements exist
   - Verify expected child elements are present
   - Log or return meaningful errors for malformed XML
3. **Safe defaults**: If an XML field is missing, use safe defaults (None, empty string, or 0) rather than raising exceptions, unless the field is critical to the operation.
4. **Error reporting**: Include the problematic XML filename/path in all error messages.

**Example approach:**
```python
def parse_invoice_xml(filepath: str) -> dict:
    """Parse NFe/NFCe XML with validation."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Validate structure
        if root.tag not in ['NFe', 'NFCe']:
            raise ValueError(f"Invalid root element: {root.tag}")
        
        # Extract data with safe defaults
        ibs_value = extract_ibs(root)
        return {"filename": filepath, "ibs": ibs_value}
    
    except ET.ParseError as e:
        return {"filename": filepath, "error": f"XML parse error: {e}"}
```

## File Organization — Modular Structure

Organize code into distinct layers:

```
REFORMA/
├── app.py                    # Flask app config, route registration only
├── .github/
│   └── copilot-instructions.md
├── services/
│   ├── xml_parser.py         # Core XML parsing logic
│   ├── invoice_scanner.py    # IBS detection and business logic
│   └── file_processor.py     # File upload, decompression, storage
├── utils/
│   ├── validators.py         # XML structure validation
│   ├── file_utils.py         # Path handling, cleanup
│   └── config.py             # Constants, configuration
├── static/
│   ├── script.js
│   └── style.css
├── templates/
│   └── index.html
└── tests/
    ├── test_xml_parser.py
    └── test_invoice_scanner.py
```

**Module responsibilities:**
- `app.py`: Flask app creation, route definitions, request/response handling only. Import from services.
- `services/`: Business logic, file processing, XML analysis. Pure functions that return data structures.
- `utils/`: Helpers (validation, file I/O, configuration constants).
- `static/`, `templates/`: Frontend assets.

## Flask Routes & API Design

- **Route handlers should be thin**: Logic goes in `services/`, not in route functions.
- **Consistent API responses**:
  ```python
  # Success
  return jsonify({"success": True, "data": {...}})
  
  # Error
  return jsonify({"success": False, "error": "descriptive message"}), 400
  ```
- **Validate inputs early**: Check file existence, MIME types, and size before processing.
- **Resource cleanup**: Always clean up temporary files in `finally` blocks.

Example route structure:
```python
@app.route('/api/scan', methods=['POST'])
def scan_invoices():
    try:
        files = validate_uploaded_files(request)  # From utils/validators.py
        results = process_invoices(files)         # From services/invoice_scanner.py
        return jsonify({"success": True, "results": results})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cleanup_temp_files()
```

## XML IBS Detection Logic

- **IBS field names**: Support these common variants:
  - `IBSCBS`, `ibscbs`, `vIBSCBS`, `pIBSCBS`, `cIBSCBS`, `indIBSCBS`
  - Use namespace-aware XPath queries (e.g., `.//{*}IBSCBS`)
- **Invoice types**: Handle both NFe (Nota Fiscal Eletrônica) and NFCe (Nota Fiscal de Consumidor Eletrônica).
- **Folder structure**: Expect companies organized as:
  ```
  <company_name>/
    ├── NFe/
    │   └── *.xml
    ├── NFCe/
    │   └── *.xml
  ```

## Imports & Dependencies

- Use standard library first (`xml.etree.ElementTree`, `os`, `pathlib`, `tempfile`).
- For external packages, prefer Flask ecosystem: `flask`, `jinja2`.
- Archive handling: Use `zipfile` and `shutil` for decompression.
- **Keep dependencies minimal**. Avoid heavy frameworks for this project.

## Documentation & Comments

- **Docstrings**: Include for all public functions using Google-style format:
  ```python
  def scan_xml_for_ibs(filepath: str) -> bool:
      """Check if XML file contains IBS field.
      
      Args:
          filepath: Path to XML file.
      
      Returns:
          True if any IBS variant found, False otherwise.
      
      Raises:
          ValueError: If file does not exist or is not valid XML.
      """
  ```
- **Comments**: Use for *why*, not *what*. Good code should be self-documenting.

## Error Handling

- **Catch specific exceptions**, not bare `except:`.
- **Log context**: Include filename, line number, and relevant data in error messages.
- **User-friendly errors**: API responses should not expose internal stack traces.
- **Graceful degradation**: If a single file fails, continue processing others (use try-catch in loops).

## Testing Approach

While not a priority, structure code to be testable:
- Separate I/O from business logic.
- Pure functions (no side effects) make testing easier.
- Use dependency injection for file paths and external resources.

---

## Summary for Copilot

When working on this project:
1. **Always write in English** — variable names, comments, and code.
2. **Validate all XML** — check structure, handle missing fields safely.
3. **Keep routes thin** — move logic to `services/` modules.
4. **Organize files** — separate concerns (app, services, utils, static).
5. **Use namespace-aware XML parsing** — `.//{*}tag` patterns for flexibility.
6. **Clean up resources** — temporary files, decompressed data.
7. **Return consistent API responses** — with `success` and `data`/`error` keys.
