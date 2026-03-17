"""
relatorio_pdf.py
----------------
Generate PDF reports from IBSCBS scan results using WeasyPrint.
"""

from datetime import datetime

from markupsafe import escape
from weasyprint import HTML


def gerar_relatorio_pdf(resultados: list[dict]) -> bytes:
    """Generate a PDF report with IBSCBS scan analysis.

    Args:
        resultados: List of company result dicts (same format as
            ``services.invoice_scanner.scan_directory`` output).

    Returns:
        PDF file content as bytes.
    """
    com_ibs = [r for r in resultados if r["usa_ibs"]]
    sem_ibs = [r for r in resultados if not r["usa_ibs"]]

    pct_com_ibs = (len(com_ibs) / len(resultados) * 100) if resultados else 0
    pct_sem_ibs = (len(sem_ibs) / len(resultados) * 100) if resultados else 0

    total_xmls = sum(
        s["total_xmls"]
        for r in resultados
        for s in r["tipos"].values()
    )
    total_xmls_com_ibs = sum(
        s["xmls_com_ibs"]
        for r in resultados
        for s in r["tipos"].values()
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Relat\u00f3rio de Varredura IBSCBS</title>
        <style>
            @page {{
                size: A4;
                margin: 2.5cm 2cm 2.5cm 2cm;
                @bottom-right {{
                    content: "P\u00e1gina " counter(page) " de " counter(pages);
                    font-size: 10pt;
                    color: #888;
                }}
            }}

            body {{
                font-family: 'Segoe UI', 'DejaVu Sans', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #2c3e50;
                margin: 0;
                padding: 0;
            }}

            .header {{
                text-align: center;
                border-bottom: 3px solid #2980b9;
                padding-bottom: 15pt;
                margin-bottom: 35pt;
            }}

            .title {{
                font-size: 26pt;
                font-weight: 700;
                color: #2980b9;
                margin: 0 0 10pt 0;
                letter-spacing: 0.5px;
            }}

            .subtitle {{
                font-size: 12pt;
                color: #7f8c8d;
                margin: 0;
            }}

            .section {{
                margin-bottom: 30pt;
            }}

            .section-title {{
                font-size: 16pt;
                font-weight: bold;
                color: #2c3e50;
                border-bottom: 2px solid #bdc3c7;
                padding-bottom: 6pt;
                margin-bottom: 18pt;
            }}

            .stats-table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                margin: 15pt 0;
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid #e0e0e0;
            }}

            .stats-table th,
            .stats-table td {{
                padding: 10pt 14pt;
                text-align: left;
                border-bottom: 1px solid #e0e0e0;
            }}

            .stats-table tr:last-child td {{
                border-bottom: none;
            }}

            .stats-table th {{
                background: #f8f9fa;
                color: #2c3e50;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 10pt;
                letter-spacing: 0.5pt;
                border-bottom: 2px solid #2980b9;
            }}

            .stats-table tr:nth-child(even) {{
                background: #fcfcfc;
            }}

            .company-list {{
                margin: 15pt 0;
            }}

            .company-item {{
                margin-bottom: 15pt;
                padding: 12pt 14pt;
                background: #ffffff;
                border: 1px solid #ecf0f1;
                border-left-width: 5px;
                border-left-color: #2980b9;
                border-radius: 4px 8px 8px 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            }}

            .company-name {{
                font-weight: bold;
                font-size: 13pt;
                color: #2c3e50;
                margin-bottom: 10pt;
            }}

            .company-detail {{
                margin-left: 15pt;
                font-size: 10.5pt;
                color: #34495e;
                margin-bottom: 6pt;
            }}

            .file-item {{
                margin-left: 30pt;
                font-size: 9pt;
                color: #666;
                font-family: monospace;
                margin-bottom: 3pt;
            }}

            .tag-chip {{
                display: inline-block;
                background: #e3f2fd;
                color: #1976D2;
                padding: 2pt 6pt;
                border-radius: 3pt;
                font-size: 8pt;
                margin: 1pt;
                font-family: monospace;
            }}

            .note-warning {{
                color: #b38000;
                background-color: #fff8e1;
                padding: 4pt 8pt;
                border-radius: 4pt;
                border-left: 3pt solid #ffc107;
                font-size: 9pt;
                margin-top: 5pt;
                margin-left: 20pt;
                margin-bottom: 5pt;
                font-family: monospace;
            }}

            .notes {{
                background: #fff3e0;
                border: 1px solid #ffcc02;
                border-radius: 4pt;
                padding: 12pt;
                margin-top: 20pt;
            }}

            .notes-title {{
                font-weight: bold;
                color: #e65100;
                margin-bottom: 8pt;
            }}

            .notes-list {{
                margin: 0;
                padding-left: 20pt;
            }}

            .notes-list li {{
                margin-bottom: 8pt;
                font-size: 10.5pt;
                color: #4a4a4a;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">RELAT\u00d3RIO EXPLORAT\u00d3RIO IBSCBS</h1>
            <p class="subtitle">Varredura gerada em: {datetime.now().strftime('%d/%m/%Y \u00e0s %H:%M:%S')}</p>
        </div>

        <div class="section">
            <h2 class="section-title">RESUMO EXECUTIVO</h2>
            <table class="stats-table">
                <tr>
                    <th>M\u00e9trica</th>
                    <th>Valor</th>
                </tr>
                <tr>
                    <td>Total de Empresas Analisadas</td>
                    <td>{len(resultados)}</td>
                </tr>
                <tr>
                    <td>Empresas com IBSCBS</td>
                    <td>{len(com_ibs)} ({pct_com_ibs:.1f}%)</td>
                </tr>
                <tr>
                    <td>Empresas sem IBSCBS</td>
                    <td>{len(sem_ibs)} ({pct_sem_ibs:.1f}%)</td>
                </tr>
                <tr>
                    <td>Total de XMLs Analisados</td>
                    <td>{total_xmls}</td>
                </tr>
                <tr>
                    <td>XMLs com IBSCBS</td>
                    <td>{total_xmls_com_ibs} ({(total_xmls_com_ibs / total_xmls * 100 if total_xmls else 0):.1f}%)</td>
                </tr>
            </table>
        </div>
    """

    # -- Companies WITH IBSCBS --
    if com_ibs:
        html_content += """
        <div class="section">
            <h2 class="section-title">EMPRESAS COM IBSCBS</h2>
            <div class="company-list">
        """

        for empresa in com_ibs:
            name = escape(empresa["empresa"])
            cnpj_str = (
                f" - {escape(empresa['cnpj'])}"
                if empresa.get("cnpj") and empresa["cnpj"] != "Desconhecido"
                else ""
            )
            html_content += f"""
            <div class="company-item">
                <div class="company-name">\u2022 {name}{cnpj_str}</div>
            """

            for tipo, stats in empresa["tipos"].items():
                if stats["total_xmls"] > 0:
                    pct = stats["xmls_com_ibs"] / stats["total_xmls"] * 100
                    html_content += f"""
                    <div class="company-detail">
                        {escape(tipo)}: {stats['xmls_com_ibs']}/{stats['total_xmls']} ({pct:.1f}%)
                    </div>
                    """

                    if stats.get("arquivos"):
                        for arq, tags in stats["arquivos"]:
                            tags_html = "".join(
                                f'<span class="tag-chip">{escape(tag)}</span>'
                                for tag in tags
                            )
                            html_content += f"""
                            <div class="file-item">
                                📄 {escape(arq)}<br>{tags_html}
                            </div>
                            """

                    if stats.get("todos_arquivos"):
                        ibs_files = [a[0] for a in stats.get("arquivos", [])]
                        non_ibs_files = [
                            arq
                            for arq in stats["todos_arquivos"]
                            if arq not in ibs_files
                        ]
                        if non_ibs_files:
                            html_content += """
                            <div class="company-detail" style="color: #b38000; font-weight: bold; margin-top: 10pt;">
                                Aten\u00e7\u00e3o: Notas sem IBSCBS identificadas:
                            </div>
                            """
                            for arq in non_ibs_files:
                                html_content += f"""
                                <div class="note-warning">
                                    ⚠️ 📄 {escape(arq)}
                                </div>
                                """

            html_content += "</div>"

        html_content += "</div></div>"

    # -- Companies WITHOUT IBSCBS --
    if sem_ibs:
        html_content += """
        <div class="section">
            <h2 class="section-title">EMPRESAS SEM IBSCBS</h2>
            <div class="company-list">
        """

        for empresa in sem_ibs:
            total_notas = sum(s["total_xmls"] for s in empresa["tipos"].values())
            name = escape(empresa["empresa"])
            cnpj_str = (
                f" - {escape(empresa['cnpj'])}"
                if empresa.get("cnpj") and empresa["cnpj"] != "Desconhecido"
                else ""
            )

            html_content += f"""
            <div class="company-item">
                <div class="company-name">\u2022 {name}{cnpj_str}</div>
                <div class="company-detail">
                    {total_notas} nota(s) analisada(s)
                </div>
            </div>
            """

        html_content += "</div></div>"

    # -- Methodological notes --
    html_content += """
        <div class="notes">
            <div class="notes-title">OBSERVA\u00c7\u00d5ES METODOL\u00d3GICAS</div>
            <ul class="notes-list">
                <li><strong>Empresa com IBSCBS:</strong> Entidade que possui pelo menos um XML atestando os campos do imposto nos agrupamentos avaliados.</li>
                <li><strong>Empresa sem IBSCBS:</strong> Entidade onde a totalidade de XMLs processados n\u00e3o cont\u00e9m ind\u00edcios do novo referencial tribut\u00e1rio.</li>
                <li><strong>Tags detectadas:</strong> IBSCBS, ibscbs, vIBSCBS, pIBSCBS, cIBSCBS, indIBSCBS.</li>
            </ul>
        </div>
    </body>
    </html>
    """

    html_doc = HTML(string=html_content)
    pdf_bytes = html_doc.write_pdf()

    return pdf_bytes
