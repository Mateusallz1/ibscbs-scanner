"""
app.py
------
Flask application: thin route handlers that delegate to services.
"""

import io
import logging
import os
import sys
import threading
import uuid
from datetime import datetime

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(__file__))

import relatorio_pdf  # noqa: E402
from services.file_processor import process_upload  # noqa: E402
from services.invoice_scanner import scan_directory  # noqa: E402
from utils.config import MAX_CONCURRENT_SCANS, MAX_UPLOAD_SIZE_MB  # noqa: E402
from utils.file_utils import cleanup_directory  # noqa: E402

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --- App ---
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# --- Concurrency control ---
_scan_semaphore = threading.Semaphore(MAX_CONCURRENT_SCANS)

# --- Thread-safe scan result storage (keyed by UUID) ---
_scan_results: dict[str, list[dict]] = {}
_results_lock = threading.Lock()
_RESULT_TTL_SECONDS = 3600  # 1 hour


def _store_result(results: list[dict]) -> str:
    """Store scan results and return a unique scan_id."""
    scan_id = uuid.uuid4().hex
    now = datetime.now().timestamp()

    with _results_lock:
        # Evict expired entries
        expired = [
            sid for sid, (_, ts) in _scan_results.items()
            if now - ts > _RESULT_TTL_SECONDS
        ]
        for sid in expired:
            del _scan_results[sid]

        _scan_results[scan_id] = (results, now)

    return scan_id


def _get_result(scan_id: str) -> list[dict] | None:
    """Retrieve stored results by scan_id, or None if missing/expired."""
    with _results_lock:
        entry = _scan_results.get(scan_id)
        if entry is None:
            return None
        results, ts = entry
        if datetime.now().timestamp() - ts > _RESULT_TTL_SECONDS:
            del _scan_results[scan_id]
            return None
        return results


# --- Security headers ---

@app.after_request
def add_security_headers(response):
    """Attach security headers to every response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return response


# --- Error handlers ---

@app.errorhandler(RequestEntityTooLarge)
def handle_too_large(_exc):
    return jsonify({
        "success": False,
        "error": f"Arquivo excede o limite de {MAX_UPLOAD_SIZE_MB} MB.",
    }), 413


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def scan_ibs():
    """Accept uploaded files, scan for IBSCBS, and return results."""
    if "files" not in request.files:
        return jsonify({
            "error": "Nenhum arquivo enviado. Envie arquivos .zip, .rar ou .xml.",
        }), 400

    files = request.files.getlist("files")

    acquired = _scan_semaphore.acquire(blocking=False)
    if not acquired:
        return jsonify({
            "success": False,
            "error": "Servidor ocupado. Aguarde um momento e tente novamente.",
        }), 429

    temp_dir = None
    try:
        temp_dir, target_dir = process_upload(files)
        results = scan_directory(target_dir, verbose=False)
        scan_id = _store_result(results)

        return jsonify({
            "success": True,
            "scan_id": scan_id,
            "resultados": results,
        })
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception:
        logger.exception("Unexpected error during scan")
        return jsonify({"success": False, "error": "Erro interno ao processar os arquivos."}), 500
    finally:
        _scan_semaphore.release()
        if temp_dir:
            cleanup_directory(temp_dir)


@app.route("/api/capture-lead", methods=["POST"])
def capture_lead():
    """Persist a user lead (name + email) to leads.txt."""
    data = request.get_json(silent=True) or {}
    nome = "".join(c for c in str(data.get("nome", "")) if c >= " ").strip()
    email = "".join(c for c in str(data.get("email", "")) if c >= " ").strip()

    if not nome or not email:
        return jsonify({"success": False, "error": "Nome e e-mail são obrigatórios."}), 400

    if len(nome) > 200 or len(email) > 254:
        return jsonify({"success": False, "error": "Dados inválidos."}), 400

    leads_file = os.path.join(os.path.dirname(__file__), "leads.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(leads_file, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {nome} | {email}\n")

    logger.info("Lead capturado: %s <%s>", nome, email)
    return jsonify({"success": True})


@app.route("/api/export-pdf", methods=["GET"])
def export_pdf():
    """Export scan results as a PDF report."""
    scan_id = request.args.get("scan_id", "")

    results = _get_result(scan_id)
    if results is None:
        return jsonify({
            "error": "Nenhuma varredura encontrada. Realize uma nova varredura.",
        }), 400

    try:
        pdf_content = relatorio_pdf.gerar_relatorio_pdf(results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Relatorio_IBSCBS_{timestamp}.pdf"

        return send_file(
            io.BytesIO(pdf_content),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception:
        logger.exception("Error generating PDF report")
        return jsonify({"error": "Erro interno ao gerar o relatório PDF."}), 500


if __name__ == "__main__":
    logger.info("Iniciando interface gráfica web do Scanner de IBSCBS...")
    logger.info("Acesse http://127.0.0.1:5000 no seu navegador.")
    app.run(debug=True, port=5000)
