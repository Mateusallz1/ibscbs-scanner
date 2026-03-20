document.addEventListener('DOMContentLoaded', () => {
    const scanForm = document.getElementById('scan-form');
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');

    const selectedFileInfo = document.getElementById('selected-file-info');
    const fileNamesDisplay = document.getElementById('file-names');

    const btnScan = document.getElementById('btn-scan');
    const loader = document.getElementById('loader');
    const errorBanner = document.getElementById('error-banner');
    const errorText = document.getElementById('error-text');
    const dashboard = document.getElementById('dashboard');

    // Stats
    const statTotal = document.getElementById('stat-total');
    const statComIbs = document.getElementById('stat-com-ibs');
    const statSemIbs = document.getElementById('stat-sem-ibs');
    const badgeComIbs = document.getElementById('badge-com-ibs');
    const badgeSemIbs = document.getElementById('badge-sem-ibs');

    // Lists
    const listComIbs = document.getElementById('list-com-ibs');
    const listSemIbs = document.getElementById('list-sem-ibs');

    // Columns and grid (for show/hide logic)
    const colComIbs = document.getElementById('col-com-ibs');
    const colSemIbs = document.getElementById('col-sem-ibs');
    const resultsGrid = document.getElementById('results-grid');
    const emptyState = document.getElementById('empty-state');
    const dashboardSummary = document.getElementById('dashboard-summary');

    let selectedFiles = [];
    let currentScanId = null;

    // --- Utility: escape user-provided strings before inserting as HTML ---
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('active'), false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('active'), false);
    });

    // Handle dropped files/folders
    dropArea.addEventListener('drop', async (e) => {
        const dt = e.dataTransfer;

        if (dt.files && dt.files.length > 0) {
            handleFiles(dt.files);
        }
    }, false);

    // Click on drop area opens folder picker
    dropArea.addEventListener('click', () => {
        fileInput.click();
    });
    fileInput.addEventListener('change', function () {
        if (this.files.length > 0) handleFiles(this.files);
    });

    function setMultipleFiles(files) {
        selectedFiles = Array.from(files);
        const names = selectedFiles.map(f => f.name).join(', ');
        fileNamesDisplay.textContent = names;
        selectedFileInfo.classList.remove('hidden');
        btnScan.disabled = false;
        errorBanner.classList.add('hidden');
    }

    function handleFiles(files) {
        if (!files || files.length === 0) return;

        const validFiles = [];
        const invalidFiles = [];

        for (let file of files) {
            const ext = file.name.toLowerCase();
            if (ext.endsWith('.zip') || ext.endsWith('.rar') || ext.endsWith('.xml')) {
                validFiles.push(file);
            } else {
                invalidFiles.push(file.name);
            }
        }

        if (invalidFiles.length > 0) {
            selectedFiles = [];
            fileNamesDisplay.textContent = '';
            selectedFileInfo.classList.add('hidden');
            btnScan.disabled = true;
            showError('Arquivos inválidos: ' + invalidFiles.join(', ') + '. Apenas .zip, .rar e .xml são suportados.');
            return;
        }

        // Verificar se não há mistura de tipos
        const hasArchives = validFiles.some(f => f.name.toLowerCase().endsWith('.zip') || f.name.toLowerCase().endsWith('.rar'));
        const hasXmls = validFiles.some(f => f.name.toLowerCase().endsWith('.xml'));

        if (hasArchives && hasXmls) {
            selectedFiles = [];
            fileNamesDisplay.textContent = '';
            selectedFileInfo.classList.add('hidden');
            btnScan.disabled = true;
            showError('Não é permitido misturar arquivos compactados (.zip/.rar) e arquivos XML.');
            return;
        }

        if (hasArchives && validFiles.length > 1) {
            selectedFiles = [];
            fileNamesDisplay.textContent = '';
            selectedFileInfo.classList.add('hidden');
            btnScan.disabled = true;
            showError('Envie apenas um arquivo compactado. Para múltiplos XMLs, envie-os separadamente.');
            return;
        }

        setMultipleFiles(validFiles);
    }

    scanForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (selectedFiles.length === 0) return;

        // Reset UI State
        errorBanner.classList.add('hidden');
        dashboard.classList.add('hidden');
        loader.classList.remove('hidden');
        btnScan.disabled = true;

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!data.success) {
                showError(data.error || 'Erro desconhecido ao processar os arquivos.');
                return;
            }

            currentScanId = data.scan_id;
            renderDashboard(data.resultados);

            const scanCount = parseInt(localStorage.getItem('ibscbs_scan_count') || '0', 10);
            localStorage.setItem('ibscbs_scan_count', scanCount + 1);
            checkLeadModal();

        } catch (error) {
            showError('Erro de conexão com o servidor: ' + error.message);
        } finally {
            loader.classList.add('hidden');
            btnScan.disabled = false;
        }
    });

    function showError(message) {
        errorText.textContent = message;
        errorBanner.classList.remove('hidden');
    }

    function renderDashboard(resultados) {
        // Estatísticas
        const comIbsArray = resultados.filter(r => r.usa_ibs);
        const semIbsArray = resultados.filter(r => !r.usa_ibs);

        statTotal.textContent = resultados.length;
        statComIbs.textContent = comIbsArray.length;
        statSemIbs.textContent = semIbsArray.length;

        badgeComIbs.textContent = comIbsArray.length;
        badgeSemIbs.textContent = semIbsArray.length;

        // Pasta vazia — sem nenhuma nota encontrada
        if (resultados.length === 0) {
            dashboardSummary.classList.add('hidden');
            resultsGrid.classList.add('hidden');
            emptyState.classList.remove('hidden');
            if (btnExportPdf) btnExportPdf.closest('.dashboard-actions').classList.add('hidden');
            dashboard.classList.remove('hidden');
            return;
        }
        dashboardSummary.classList.remove('hidden');
        if (btnExportPdf) btnExportPdf.closest('.dashboard-actions').classList.remove('hidden');
        resultsGrid.classList.remove('hidden');
        emptyState.classList.add('hidden');

        // Limpar listas
        listComIbs.innerHTML = '';
        listSemIbs.innerHTML = '';

        // Renderizar e exibir/ocultar coluna COM IBS
        if (comIbsArray.length === 0) {
            colComIbs.classList.add('hidden');
        } else {
            colComIbs.classList.remove('hidden');
            comIbsArray.forEach(empresa => {
                listComIbs.appendChild(createCompanyItem(empresa, true));
            });
        }

        // Renderizar e exibir/ocultar coluna SEM IBS
        if (semIbsArray.length === 0) {
            colSemIbs.classList.add('hidden');
        } else {
            colSemIbs.classList.remove('hidden');
            semIbsArray.forEach(empresa => {
                listSemIbs.appendChild(createCompanyItem(empresa, false));
            });
        }

        // Grid de coluna única quando só um grupo está visível
        const onlyOne = comIbsArray.length === 0 || semIbsArray.length === 0;
        resultsGrid.classList.toggle('single-column', onlyOne);

        // Mostrar dashboard
        dashboard.classList.remove('hidden');
    }

    function createCompanyItem(empresa, hasIbs) {
        const item = document.createElement('div');
        item.className = 'md-list-item';

        let detailHtml = '';
        let hasMissingIbs = false;

        if (hasIbs) {
            detailHtml = '<div class="company-details">';
            for (const [tipo, stats] of Object.entries(empresa.tipos)) {
                if (stats.todos_arquivos && stats.todos_arquivos.length > 0) {
                    const notasSem = stats.todos_arquivos.filter(arq => !stats.arquivos.some(a => a[0] === arq));
                    if (notasSem.length > 0) hasMissingIbs = true;
                }
                if (stats.total_xmls > 0) {
                    const statusText = stats.xmls_com_ibs > 0
                        ? `<span class="text-success">${stats.xmls_com_ibs}/${stats.total_xmls} com IBSCBS</span>`
                        : `${stats.xmls_com_ibs}/${stats.total_xmls} sem IBSCBS`;
                    detailHtml += `<div class="company-detail-item"><strong>${escapeHtml(tipo)}</strong>: ${statusText}</div>`;

                    if (stats.xmls_com_ibs > 0) {
                        detailHtml += `<div style="margin-left:8px;">`;
                        stats.arquivos.forEach(([arq, tags]) => {
                            const tagsChips = tags.map(t => `<span class="tag-chip">${escapeHtml(t)}</span>`).join('');
                            detailHtml += `<div style="font-size:12px; margin-top:4px;">\ud83d\udcc4 ${escapeHtml(arq)}<br>${tagsChips}</div>`;
                        });
                        detailHtml += `</div>`;
                    }
                    if (stats.todos_arquivos && stats.todos_arquivos.length > 0) {
                        const notasSemIbs = stats.todos_arquivos.filter(arq => !stats.arquivos.some(a => a[0] === arq));
                        if (notasSemIbs.length > 0) {
                            detailHtml += `<div style="margin-left:8px; margin-top:12px; color: #FBC02D;"><strong>Atenção: Notas sem IBSCBS identificadas:</strong></div>`;
                            detailHtml += `<div style="margin-left:8px; display: flex; flex-direction: column; gap: 6px; margin-top: 6px; margin-bottom: 8px;">`;
                            notasSemIbs.forEach(arq => {
                                detailHtml += `<div class="note-warning">
                                    <span class="material-symbols-outlined note-warning-icon">warning</span>
                                    <span>\ud83d\udcc4 ${escapeHtml(arq)}</span>
                                </div>`;
                            });
                            detailHtml += `</div>`;
                        }
                    }
                }
            }
            detailHtml += '</div>';
        } else {
            // Conta total de notas varridas e mostra as notas
            let total = 0;
            let arquivosVistos = [];
            for (const [, stats] of Object.entries(empresa.tipos)) {
                total += stats.total_xmls;
                if (stats.todos_arquivos && stats.todos_arquivos.length > 0) {
                    arquivosVistos.push(...stats.todos_arquivos);
                }
            }
            detailHtml = `<div class="company-details"><div class="company-detail-item">${total} nota(s) analisada(s)</div>`;
            if (arquivosVistos.length > 0) {
                detailHtml += `<div style="margin-top: 8px;">`;
                arquivosVistos.forEach(arq => {
                    detailHtml += `<div style="font-size:12px; margin-top:4px;">\ud83d\udcc4 ${escapeHtml(arq)}</div>`;
                });
                detailHtml += `</div>`;
            }
            detailHtml += `</div>`;
        }

        let iconHtml = '';
        if (hasIbs) {
            if (hasMissingIbs) {
                iconHtml = `<span class="material-symbols-outlined text-warning">warning</span>`;
            } else {
                iconHtml = `<span class="material-symbols-outlined text-success">check_circle</span>`;
            }
        } else {
            iconHtml = `<span class="material-symbols-outlined text-error">cancel</span>`;
        }

        const companyName = escapeHtml(empresa.empresa);
        const companyCnpj = empresa.cnpj && empresa.cnpj !== 'Desconhecido' ? escapeHtml(empresa.cnpj) : '';

        item.innerHTML = `
            <div class="company-name" style="align-items: flex-start;">
                <span style="display:flex; gap:8px;">
                    ${iconHtml}
                    <div style="display: flex; flex-direction: column;">
                        <span>${companyName}</span>
                        <span style="font-size: 12px; font-weight: 400; color: var(--md-sys-color-on-surface-variant);">${companyCnpj}</span>
                    </div>
                </span>
                <span class="material-symbols-outlined expand-icon">expand_more</span>
            </div>
            ${detailHtml}
        `;

        item.addEventListener('click', () => {
            const details = item.querySelector('.company-details');
            if (details) {
                details.classList.toggle('expanded');
                item.classList.toggle('expanded');
            }
        });

        return item;
    }

    // Botão de exportar PDF
    const btnExportPdf = document.getElementById('btn-export-pdf');
    if (btnExportPdf) {
        btnExportPdf.addEventListener('click', async () => {
            if (!currentScanId) {
                showError('Nenhuma varredura realizada. Processe arquivos antes de exportar.');
                return;
            }

            try {
                btnExportPdf.disabled = true;
                const response = await fetch(`/api/export-pdf?scan_id=${encodeURIComponent(currentScanId)}`);

                if (!response.ok) {
                    const data = await response.json();
                    showError(data.error || 'Erro ao gerar PDF.');
                    return;
                }

                // Criar download do PDF
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'Relatorio_IBSCBS.pdf';
                document.body.appendChild(link);
                link.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link);
            } catch (error) {
                showError('Erro ao baixar PDF: ' + error.message);
            } finally {
                btnExportPdf.disabled = false;
            }
        });
    }

    // --- Theme Toggle ---
    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    const themeToggleIcon = document.getElementById('theme-toggle-icon');

    function applyTheme(theme) {
        if (theme === 'light') {
            document.body.setAttribute('data-theme', 'light');
            themeToggleIcon.textContent = 'dark_mode';
        } else {
            document.body.removeAttribute('data-theme');
            themeToggleIcon.textContent = 'light_mode';
        }
    }

    applyTheme(localStorage.getItem('ibscbs_theme') || 'light');

    btnThemeToggle.addEventListener('click', () => {
        const next = document.body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        localStorage.setItem('ibscbs_theme', next);
        applyTheme(next);
    });

    // --- Info Modal ---
    const infoModal = document.getElementById('info-modal');
    document.getElementById('btn-info-open').addEventListener('click', () => {
        infoModal.classList.remove('hidden');
    });
    document.getElementById('btn-info-close').addEventListener('click', () => {
        infoModal.classList.add('hidden');
    });
    infoModal.addEventListener('click', (e) => {
        if (e.target === infoModal) infoModal.classList.add('hidden');
    });

    // --- Lead Capture Modal ---
    const leadModal = document.getElementById('lead-modal');
    const leadForm = document.getElementById('lead-form');
    const leadError = document.getElementById('lead-error');

    function checkLeadModal() {
        if (localStorage.getItem('ibscbs_lead_done')) return;
        const count = parseInt(localStorage.getItem('ibscbs_scan_count') || '0', 10);
        if (count >= 2) leadModal.classList.remove('hidden');
    }

    leadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const nome = document.getElementById('lead-nome').value.trim();
        const email = document.getElementById('lead-email').value.trim();

        const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        if (!nome || !emailValid) {
            leadError.classList.remove('hidden');
            return;
        }
        leadError.classList.add('hidden');

        try {
            await fetch('/api/capture-lead', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome, email }),
            });
        } catch (_) { /* silent — não bloquear o usuário */ }

        localStorage.setItem('ibscbs_lead_done', '1');
        leadModal.classList.add('hidden');
    });

});
