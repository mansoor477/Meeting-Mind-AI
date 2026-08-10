document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const sampleSelect = document.getElementById('sample-select');
    const transcriptInput = document.getElementById('transcript-input');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    const stripTimestampsCb = document.getElementById('strip-timestamps');
    const cleanFillersCb = document.getElementById('clean-fillers');
    const forceMockCb = document.getElementById('force-mock');
    const providerSelect = document.getElementById('provider-select');
    const processBtn = document.getElementById('process-btn');


    const welcomePlaceholder = document.getElementById('welcome-placeholder');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultsContent = document.getElementById('results-content');

    // Stats
    const statTimestamps = document.getElementById('stat-timestamps');
    const statFillers = document.getElementById('stat-fillers');
    const statActions = document.getElementById('stat-actions');
    const statDecisions = document.getElementById('stat-decisions');
    const statRisks = document.getElementById('stat-risks');

    const actionCountBadge = document.getElementById('action-count-badge');
    const decisionCountBadge = document.getElementById('decision-count-badge');
    const riskCountBadge = document.getElementById('risk-count-badge');

    // Tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Tab Views
    const summaryTitle = document.getElementById('summary-title');
    const summaryOverview = document.getElementById('summary-overview');
    const takeawaysList = document.getElementById('takeaways-list');
    const participantsChips = document.getElementById('participants-chips');

    const actionsTableBody = document.getElementById('actions-table-body');
    const actionCardsContainer = document.getElementById('action-cards-container');
    const decisionsTableBody = document.getElementById('decisions-table-body');
    const risksTableBody = document.getElementById('risks-table-body');

    const markdownViewer = document.getElementById('markdown-viewer');
    const copyMDBtn = document.getElementById('copy-md-btn');
    const copyFeedback = document.getElementById('copy-feedback');

    const jsonViewer = document.getElementById('json-viewer');
    const downloadJsonBtn = document.getElementById('download-json-btn');

    let currentResponseData = null;

    // Load Samples
    fetch('/api/samples')
        .then(res => res.json())
        .then(data => {
            if (data.samples && data.samples.length > 0) {
                data.samples.forEach((sample, idx) => {
                    const opt = document.createElement('option');
                    opt.value = sample.content;
                    opt.textContent = sample.title;
                    sampleSelect.appendChild(opt);

                    // Auto-select first sample
                    if (idx === 0) {
                        sampleSelect.selectedIndex = 1;
                        transcriptInput.value = sample.content;
                    }
                });
            }
        })
        .catch(err => console.log('Failed to fetch samples:', err));

    sampleSelect.addEventListener('change', (e) => {
        if (e.target.value) {
            transcriptInput.value = e.target.value;
        }
    });

    // File Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent-indigo)';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--border-color)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border-color)';
        if (e.dataTransfer.files.length > 0) {
            readTextFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            readTextFile(e.target.files[0]);
        }
    });

    function readTextFile(file) {
        const reader = new FileReader();
        reader.onload = (evt) => {
            transcriptInput.value = evt.target.result;
        };
        reader.readAsText(file);
    }

    // Tabs switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const targetTab = btn.getAttribute('data-tab');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // Priority Filters
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            const filter = chip.getAttribute('data-filter');
            filterActions(filter);
        });
    });

    function filterActions(priorityFilter) {
        const rows = actionsTableBody.querySelectorAll('tr');
        const cards = actionCardsContainer.querySelectorAll('.action-card');

        rows.forEach(row => {
            const priority = row.getAttribute('data-priority');
            if (priorityFilter === 'ALL' || priority === priorityFilter) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });

        cards.forEach(card => {
            const priority = card.getAttribute('data-priority');
            if (priorityFilter === 'ALL' || priority === priorityFilter) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // Process Trigger
    processBtn.addEventListener('click', async () => {
        const text = transcriptInput.value.trim();
        if (!text) {
            alert('Please paste or upload a meeting transcript first.');
            return;
        }

        // Show loading state
        welcomePlaceholder.classList.add('hidden');
        resultsContent.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');

        try {
            const payload = {
                transcript: text,
                strip_timestamps: stripTimestampsCb.checked,
                clean_fillers: cleanFillersCb.checked,
                force_mock: forceMockCb.checked,
                provider: providerSelect ? providerSelect.value : 'azure_openai',
                model: 'gpt-4o'
            };

            const response = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            const data = await response.json();
            currentResponseData = data;

            renderResults(data);

            loadingSpinner.classList.add('hidden');
            resultsContent.classList.remove('hidden');

        } catch (err) {
            loadingSpinner.classList.add('hidden');
            welcomePlaceholder.classList.remove('hidden');
            alert(`Error processing transcript: ${err.message}`);
        }
    });

    function renderResults(data) {
        const stats = data.preprocessor_stats;
        const intel = data.intelligence;

        // Stats
        statTimestamps.textContent = stats.timestamps_removed;
        statFillers.textContent = stats.fillers_removed;
        statActions.textContent = intel.action_items.length;
        statDecisions.textContent = intel.decisions.length;
        statRisks.textContent = intel.risks.length;

        actionCountBadge.textContent = intel.action_items.length;
        decisionCountBadge.textContent = intel.decisions.length;
        riskCountBadge.textContent = intel.risks.length;

        // 1. Summary
        summaryTitle.textContent = intel.summary.title || intel.meeting_title;
        summaryOverview.textContent = intel.summary.overview;

        takeawaysList.innerHTML = '';
        intel.summary.key_takeaways.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            takeawaysList.appendChild(li);
        });

        participantsChips.innerHTML = '';
        intel.summary.participants.forEach(p => {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.textContent = p;
            participantsChips.appendChild(chip);
        });

        // 2. Action Items Table & Cards
        actionsTableBody.innerHTML = '';
        actionCardsContainer.innerHTML = '';

        intel.action_items.forEach((item, idx) => {
            const pClass = `badge-${(item.priority || 'medium').toLowerCase()}`;
            const taskId = item.task_id || `ACTION-00${idx + 1}`;
            const effort = item.complexity || item.effort || 'Moderate';
            const timeline = item.timeline || item.target_timeline || 'N/A';
            
            // Table row
            const tr = document.createElement('tr');
            tr.setAttribute('data-priority', item.priority);
            tr.innerHTML = `
                <td><strong>${taskId}</strong></td>
                <td>${item.title}</td>
                <td><code>${item.assignee}</code></td>
                <td><span class="badge ${pClass}">${item.priority}</span></td>
                <td><code>${effort}</code></td>
                <td>${timeline}</td>
            `;
            actionsTableBody.appendChild(tr);

            // Card
            const card = document.createElement('div');
            card.className = `action-card ${(item.priority || 'medium').toLowerCase()}-border`;
            card.setAttribute('data-priority', item.priority);

            let acHtml = '';
            if (item.acceptance_criteria && item.acceptance_criteria.length > 0) {
                acHtml = `<ul class="ac-checklist">` +
                    item.acceptance_criteria.map(ac => `
                        <li class="ac-item">
                            <input type="checkbox"> <span>${ac}</span>
                        </li>
                    `).join('') + `</ul>`;
            }

            card.innerHTML = `
                <div class="card-header">
                    <span class="card-title">[${taskId}] ${item.title}</span>
                    <span class="badge ${pClass}">${item.priority}</span>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    <strong>Assignee:</strong> <code>${item.assignee}</code> | 
                    <strong>Effort/Complexity:</strong> <code>${effort}</code> | 
                    <strong>Timeline:</strong> ${timeline}
                </div>
                ${item.context_snippet ? `<div style="font-style: italic; font-size: 0.82rem; color: var(--text-dim);">"${item.context_snippet}"</div>` : ''}
                ${acHtml}
            `;
            actionCardsContainer.appendChild(card);
        });

        // 3. Decisions Table
        decisionsTableBody.innerHTML = '';
        intel.decisions.forEach((dec, idx) => {
            const tr = document.createElement('tr');
            const decId = dec.decision_id || `DEC-00${idx + 1}`;
            const rationale = dec.reason || dec.rationale || '';
            const impacted = dec.impacted_systems || [];
            const systems = impacted.map(s => `<code>${s}</code>`).join(', ');
            tr.innerHTML = `
                <td><strong>${decId}</strong></td>
                <td><strong>${dec.topic}</strong></td>
                <td>${dec.decision}</td>
                <td>${rationale}</td>
                <td>${systems || 'N/A'}</td>
                <td><code>${dec.owner || 'Team'}</code></td>
            `;
            decisionsTableBody.appendChild(tr);
        });

        // 4. Risks Table
        risksTableBody.innerHTML = '';
        intel.risks.forEach((risk, idx) => {
            const severity = risk.severity || 'Medium';
            const riskId = risk.risk_id || `RISK-00${idx + 1}`;
            const component = risk.impact || risk.affected_component || 'System';
            const description = risk.description || risk.risk_description || risk.risk || '';
            const sClass = `badge-${severity.toLowerCase()}`;
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${riskId}</strong></td>
                <td><code>${component}</code></td>
                <td>${description}</td>
                <td><span class="badge ${sClass}">${severity}</span></td>
                <td>${risk.mitigation_strategy || 'N/A'}</td>
            `;
            risksTableBody.appendChild(tr);
        });

        // 5. Markdown Digest
        markdownViewer.textContent = data.markdown_digest;

        // 6. JSON Viewer
        jsonViewer.textContent = data.json_output;
    }

    // Copy Markdown
    copyMDBtn.addEventListener('click', () => {
        if (markdownViewer.textContent) {
            navigator.clipboard.writeText(markdownViewer.textContent);
            copyFeedback.textContent = '✓ Copied to clipboard!';
            setTimeout(() => copyFeedback.textContent = '', 2500);
        }
    });

    // Download JSON
    downloadJsonBtn.addEventListener('click', () => {
        if (jsonViewer.textContent) {
            const blob = new Blob([jsonViewer.textContent], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'meeting_intelligence.json';
            a.click();
            URL.revokeObjectURL(url);
        }
    });
});
