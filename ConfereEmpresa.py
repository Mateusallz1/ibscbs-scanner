"""
ConfereEmpresa.py
-----------------
CLI interface for scanning invoice XMLs for IBSCBS usage.

This module is kept as a thin shim that delegates to
``services.invoice_scanner`` and ``services.xml_parser``.
It preserves backward-compatible function signatures so that
existing scripts or imports continue to work.

Usage::

    python ConfereEmpresa.py <root_path>
    python ConfereEmpresa.py <root_path> --verbose
    python ConfereEmpresa.py <root_path> --exportar resultado.txt
"""

import argparse
import logging
import os
import sys
from datetime import datetime

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(__file__))

from services.invoice_scanner import scan_directory  # noqa: E402
from services.xml_parser import parse_invoice_xml  # noqa: E402

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backward-compatible wrappers
# ---------------------------------------------------------------------------

def extrair_dados_xml(caminho_xml: str) -> dict:
    """Parse a single XML file (legacy interface).

    Delegates to ``services.xml_parser.parse_invoice_xml`` and maps
    the result keys back to the Portuguese names used by old callers.
    """
    data = parse_invoice_xml(caminho_xml)
    return {
        "valido": data["valid"],
        "empresa": data["company_name"],
        "cnpj": data["cnpj"],
        "tipo_nota": data["invoice_type"],
        "usa_ibs": data["has_ibs"],
        "tags_ibs": data["ibs_tags"],
    }


def varrer_raiz(caminho_raiz: str, verbose: bool = False) -> list[dict]:
    """Scan a directory tree for IBSCBS usage (legacy interface).

    Delegates to ``services.invoice_scanner.scan_directory``.
    """
    return scan_directory(caminho_raiz, verbose=verbose)


# ---------------------------------------------------------------------------
# Text report (CLI-only output)
# ---------------------------------------------------------------------------

def gerar_relatorio(resultados: list[dict]) -> str:
    """Generate a plain-text report of IBSCBS scan results."""
    lines: list[str] = []
    sep = "\u2500" * 60

    lines.append(sep)
    lines.append("  RELAT\u00d3RIO DE USO DO CAMPO IBSCBS NAS NOTAS FISCAIS")
    lines.append(f"  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    lines.append(sep)

    with_ibs = [r for r in resultados if r["usa_ibs"]]
    without_ibs = [r for r in resultados if not r["usa_ibs"]]

    lines.append(f"\nTotal de empresas analisadas : {len(resultados)}")
    lines.append(f"Empresas com IBSCBS          : {len(with_ibs)}")
    lines.append(f"Empresas sem IBSCBS          : {len(without_ibs)}")

    # -- Companies WITH IBSCBS --
    lines.append(f"\n{'\u2550' * 60}")
    lines.append("  EMPRESAS QUE UTILIZAM IBSCBS")
    lines.append(f"{'\u2550' * 60}")

    if not with_ibs:
        lines.append("\n  Nenhuma empresa com IBSCBS encontrada.")
    else:
        for r in with_ibs:
            lines.append(f"\n  \u2714 {r['empresa']}")

            types_with = [
                t for t, s in r["tipos"].items() if s["xmls_com_ibs"] > 0
            ]

            if len(types_with) == 1:
                other = "NFCe" if types_with[0] == "NFe" else "NFe"
                if other in [
                    t for t, s in r["tipos"].items() if s["total_xmls"] > 0
                ]:
                    lines.append(
                        f"     \u2192 IBSCBS presente apenas nas {types_with[0]}"
                    )
                else:
                    lines.append(
                        f"     \u2192 IBSCBS presente nas {types_with[0]} "
                        f"(tipo {other} n\u00e3o encontrado)"
                    )
            elif len(types_with) > 1:
                lines.append(
                    f"     \u2192 IBSCBS presente em: {' e '.join(types_with)}"
                )

            for tipo, stats in r["tipos"].items():
                if stats["total_xmls"] == 0:
                    lines.append(f"     {tipo}: 0 notas analisadas")
                    continue
                status = (
                    "COM IBSCBS" if stats["xmls_com_ibs"] > 0 else "sem IBSCBS"
                )
                lines.append(
                    f"     {tipo}: {stats['xmls_com_ibs']}/{stats['total_xmls']}"
                    f" nota(s) com IBSCBS [{status}]"
                )
                for arq, tags in stats["arquivos"]:
                    lines.append(
                        f"       \u2022 {arq}  \u2192  tags: {', '.join(tags)}"
                    )

    # -- Companies WITHOUT IBSCBS --
    lines.append(f"\n{'\u2550' * 60}")
    lines.append("  EMPRESAS SEM IBSCBS")
    lines.append(f"{'\u2550' * 60}")

    if not without_ibs:
        lines.append("\n  Todas as empresas utilizam IBSCBS.")
    else:
        for r in without_ibs:
            total_xmls = sum(s["total_xmls"] for s in r["tipos"].values())
            lines.append(
                f"\n  \u2718 {r['empresa']}  ({total_xmls} nota(s) analisada(s))"
            )

    lines.append(f"\n{sep}\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Varre XMLs de notas fiscais e detecta uso do campo IBSCBS por empresa.",
    )
    parser.add_argument(
        "caminho",
        nargs="+",
        help="Caminho raiz contendo as pastas das empresas.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Exibe detalhes do processamento arquivo a arquivo.",
    )
    parser.add_argument(
        "--exportar", "-e",
        metavar="ARQUIVO",
        help="Salva o relat\u00f3rio em um arquivo de texto.",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    path = " ".join(args.caminho)

    logger.info("Iniciando varredura em: %s", path)

    try:
        resultados = varrer_raiz(path, verbose=args.verbose)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        sys.exit(1)

    report = gerar_relatorio(resultados)
    print(report)

    if args.exportar:
        with open(args.exportar, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info("Relat\u00f3rio salvo em: %s", args.exportar)


if __name__ == "__main__":
    main()
