/**
 * UI/UX-Testing-Tool: Frontend-Logik
 */

let currentRunId = null;
let eventSource = null;
let savedEnvironments = {};
let editingEnvName = null;
let runStartTime = null;
let currentRunResults = [];

// Helper, Icon-Konstanten, formatDuration, severityTooltip, renderConsoleOutput,
// setBtnLoading, setConnectionStatus, escapeHtml, escapeAttr, api: siehe common.js

// ========== Initialisierung ==========

document.addEventListener("DOMContentLoaded", () => {
    restoreFormFields();
    loadEnvironments();
    loadSelectors();
    loadReports();
    loadScreenshots();
    loadJiraConfig();
    applyLatestRunToCards();
    renderAllSparklines();
    syncThemeToggleState();

    // Enter-Taste im URL-Feld startet Tests
    document.getElementById("urlInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") runTests();
    });

    // Enter-Taste im Scan-URL-Feld startet Scan
    document.getElementById("scanUrlInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") startWebsiteScan();
    });

    // Formularfelder bei Aenderung in localStorage speichern
    const persistFields = ["urlInput", "loginUrlInput", "usernameInput", "passwordInput"];
    persistFields.forEach((id) => {
        document.getElementById(id).addEventListener("input", saveFormFields);
    });
});

// ========== Formularfelder persistieren ==========

function saveFormFields() {
    const data = {
        url: document.getElementById("urlInput").value,
        login_url: document.getElementById("loginUrlInput").value,
        username: document.getElementById("usernameInput").value,
        password: document.getElementById("passwordInput").value,
    };
    localStorage.setItem("ep_test_form", JSON.stringify(data));
}

function restoreFormFields() {
    try {
        const saved = JSON.parse(localStorage.getItem("ep_test_form"));
        if (!saved) return;
        document.getElementById("urlInput").value = saved.url || "";
        document.getElementById("loginUrlInput").value = saved.login_url || "";
        document.getElementById("usernameInput").value = saved.username || "";
        document.getElementById("passwordInput").value = saved.password || "";
        // Login-Sektion oeffnen falls Credentials vorhanden
        if (saved.username || saved.password || saved.login_url) {
            document.getElementById("loginSection").open = true;
        }
    } catch (e) {
        // localStorage nicht verfuegbar oder korrupt
    }
}

// ========== URL und Credentials aus dem Eingabefeld ==========

function getUrl() {
    return document.getElementById("urlInput").value.trim();
}

function getCredentials() {
    return {
        login_url: document.getElementById("loginUrlInput").value.trim(),
        username: document.getElementById("usernameInput").value.trim(),
        password: document.getElementById("passwordInput").value.trim(),
    };
}

// ========== Umgebungen ==========

async function loadEnvironments() {
    const envs = await api("/api/environments");
    savedEnvironments = envs;
    const container = document.getElementById("savedEnvs");
    const names = Object.keys(envs);

    document.getElementById("envCount").textContent = names.length;

    if (names.length === 0) {
        container.innerHTML = '<span class="env-hint">Noch keine URLs gespeichert. Gib oben eine URL ein.</span>';
        return;
    }

    container.innerHTML = names
        .map((name) => {
            const env = envs[name];
            const desc = env.description ? ` — ${escapeHtml(env.description)}` : "";
            const hasLogin = (env.username || env.login_url) ? " \uD83D\uDD12" : "";
            return `
                <div class="env-entry">
                    <button class="env-chip" onclick="selectEnvironment('${escapeHtml(name)}')" title="${escapeHtml(env.url)}">
                        <span class="env-chip-name">${escapeHtml(name)}${hasLogin}</span>
                        <span class="env-chip-desc">${escapeHtml(env.url)}${desc}</span>
                    </button>
                    <button class="env-chip-action env-chip-edit" onclick="editEnvironment('${escapeHtml(name)}')" title="Bearbeiten" aria-label="Bearbeiten">${ICON_EDIT}</button>
                    <button class="env-chip-action env-chip-delete" onclick="deleteEnvironment('${escapeHtml(name)}')" title="Entfernen" aria-label="Entfernen">${ICON_TRASH}</button>
                </div>
            `;
        })
        .join("");
}

function selectEnvironment(name) {
    const env = savedEnvironments[name];
    if (!env) return;

    document.getElementById("urlInput").value = env.url || "";
    document.getElementById("loginUrlInput").value = env.login_url || "";
    document.getElementById("usernameInput").value = env.username || "";
    document.getElementById("passwordInput").value = env.password || "";

    // Login-Sektion oeffnen falls Credentials vorhanden
    if (env.login_url || env.username || env.password) {
        document.getElementById("loginSection").open = true;
    }

    saveFormFields();

    // Visuelles Feedback
    const input = document.getElementById("urlInput");
    input.classList.add("flash");
    setTimeout(() => input.classList.remove("flash"), 300);
}

// ========== Umgebung speichern ==========

function saveAsEnvironment() {
    const url = getUrl();
    const creds = getCredentials();
    if (!url) {
        document.getElementById("urlInput").focus();
        document.getElementById("urlInput").classList.add("input-error");
        setTimeout(() => document.getElementById("urlInput").classList.remove("input-error"), 1000);
        return;
    }

    editingEnvName = null;
    document.getElementById("saveEnvModalTitle").textContent = "URL als Umgebung speichern";
    document.getElementById("saveEnvUrl").value = url;
    document.getElementById("saveEnvUrl").readOnly = true;
    document.getElementById("saveEnvName").value = "";
    document.getElementById("saveEnvDesc").value = "";
    document.getElementById("saveEnvLoginUrl").value = creds.login_url;
    document.getElementById("saveEnvUsername").value = creds.username;
    document.getElementById("saveEnvPassword").value = creds.password;
    document.getElementById("saveEnvModal").style.display = "flex";
    document.getElementById("saveEnvName").focus();
}

async function confirmSaveEnvironment() {
    const name = document.getElementById("saveEnvName").value.trim();
    const url = document.getElementById("saveEnvUrl").value.trim();
    const description = document.getElementById("saveEnvDesc").value.trim();
    const login_url = document.getElementById("saveEnvLoginUrl").value.trim();
    const username = document.getElementById("saveEnvUsername").value.trim();
    const password = document.getElementById("saveEnvPassword").value.trim();

    if (!name) {
        document.getElementById("saveEnvName").classList.add("input-error");
        setTimeout(() => document.getElementById("saveEnvName").classList.remove("input-error"), 1000);
        return;
    }

    // Bei Umbenennung: alten Eintrag loeschen
    if (editingEnvName && editingEnvName !== name) {
        await api(`/api/environments/${encodeURIComponent(editingEnvName)}`, {
            method: "DELETE",
        });
    }

    await api("/api/environments", {
        method: "POST",
        body: JSON.stringify({ name, url, description, login_url, username, password }),
    });

    editingEnvName = null;
    closeModal("saveEnvModal");
    loadEnvironments();
}

function editEnvironment(name) {
    const env = savedEnvironments[name];
    if (!env) return;

    editingEnvName = name;
    document.getElementById("saveEnvModalTitle").textContent = `Umgebung \u201E${name}\u201C bearbeiten`;
    document.getElementById("saveEnvName").value = name;
    document.getElementById("saveEnvUrl").value = env.url || "";
    document.getElementById("saveEnvUrl").readOnly = false;
    document.getElementById("saveEnvDesc").value = env.description || "";
    document.getElementById("saveEnvLoginUrl").value = env.login_url || "";
    document.getElementById("saveEnvUsername").value = env.username || "";
    document.getElementById("saveEnvPassword").value = env.password || "";

    // Login-Sektion oeffnen falls Credentials vorhanden
    const loginDetails = document.querySelector("#saveEnvModal details");
    if (loginDetails && (env.login_url || env.username || env.password)) {
        loginDetails.open = true;
    }

    document.getElementById("saveEnvModal").style.display = "flex";
    document.getElementById("saveEnvUrl").focus();
}

async function deleteEnvironment(name) {
    await api(`/api/environments/${encodeURIComponent(name)}`, {
        method: "DELETE",
    });
    loadEnvironments();
}

// ========== Selektoren ==========

async function loadSelectors() {
    const data = await api("/api/selectors");
    document.getElementById("selectorCount").textContent =
        `${data.configured}/${data.total}`;

    const card = document.getElementById("cardSelectors");
    if (data.configured === 0) {
        card.style.borderLeft = "3px solid var(--warning)";
    } else if (data.configured === data.total) {
        card.style.borderLeft = "3px solid var(--success)";
    } else {
        card.style.borderLeft = "3px solid var(--warning)";
    }
}

// ========== Tests starten ==========

async function runTests() {
    const url = getUrl();
    const suite = document.getElementById("suiteSelect").value || null;

    if (!url) {
        document.getElementById("urlInput").focus();
        document.getElementById("urlInput").classList.add("input-error");
        setTimeout(() => document.getElementById("urlInput").classList.remove("input-error"), 1000);
        return;
    }

    // UI-Status aktualisieren
    setBtnLoading("btnRunTests", true);
    document.getElementById("btnCancel").style.display = "";
    setConnectionStatus("running");
    runStartTime = Date.now();

    // Ergebnisse zuruecksetzen
    clearResults();
    document.getElementById("resultsSection").style.display = "block";
    document.getElementById("progressBar").style.display = "block";
    document.getElementById("progressFill").className = "progress-fill indeterminate";

    // Testlauf starten – URL und Credentials uebergeben
    const creds = getCredentials();
    const data = await api("/api/tests/run", {
        method: "POST",
        body: JSON.stringify({
            url: url,
            suite: suite,
            login_url: creds.login_url || null,
            username: creds.username || null,
            password: creds.password || null,
        }),
    });

    currentRunId = data.run_id;
    startLiveBrowser();
    startEventStream(data.run_id);
}

async function cancelTests() {
    if (!currentRunId) return;

    const cancelBtn = document.getElementById("btnCancel");
    cancelBtn.disabled = true;
    cancelBtn.textContent = "Wird abgebrochen...";

    try {
        await api(`/api/tests/cancel/${currentRunId}`, { method: "POST" });
    } catch (e) {
        // Ignorieren – Stream-Ende raeumt auf
    }
}

// ========== Live-Browser ==========

let liveBrowserInterval = null;

function startLiveBrowser() {
    const section = document.getElementById("liveBrowserSection");
    const img = document.getElementById("liveBrowserImg");
    section.style.display = "";
    liveBrowserInterval = setInterval(async () => {
        const res = await fetch("/live-browser");
        if (res.status === 204) return; // noch kein Screenshot
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const old = img.src;
        img.src = url;
        if (old.startsWith("blob:")) URL.revokeObjectURL(old);
        document.getElementById("liveBrowserLabel").textContent =
            "Zuletzt aktualisiert: " + new Date().toLocaleTimeString();
    }, 500);
}

function stopLiveBrowser() {
    if (liveBrowserInterval) {
        clearInterval(liveBrowserInterval);
        liveBrowserInterval = null;
    }
    document.getElementById("liveBrowserSection").style.display = "none";
}

// ========== Event Stream ==========

function startEventStream(runId) {
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`/api/tests/stream/${runId}`);

    eventSource.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === "result") {
            addTestResult(msg.data);
        } else if (msg.type === "done") {
            onTestsCompleted(msg.data);
            eventSource.close();
            eventSource = null;
        } else if (msg.error) {
            eventSource.close();
            eventSource = null;
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
        eventSource = null;
        pollStatus(runId);
    };
}

async function pollStatus(runId) {
    const interval = setInterval(async () => {
        const status = await api(`/api/tests/status/${runId}`);

        const displayed = document.querySelectorAll("#testList .test-item").length;
        if (status.results.length > displayed) {
            for (let i = displayed; i < status.results.length; i++) {
                addTestResult(status.results[i]);
            }
        }

        if (status.output) {
            renderConsoleOutput(status.output);
        }

        if (status.status === "completed" || status.status === "error") {
            clearInterval(interval);
            onTestsCompleted(status.summary);
        }
    }, 1000);
}

// ========== Ergebnisse anzeigen ==========

function clearResults() {
    document.getElementById("testList").innerHTML = "";
    document.getElementById("testListUI").innerHTML = "";
    document.getElementById("testListUX").innerHTML = "";
    document.getElementById("testListA11y").innerHTML = "";
    document.getElementById("consoleOutput").textContent = "";
    document.getElementById("resultsSummary").innerHTML = "";
    currentRunResults = [];
    document.getElementById("btnDiff").style.display = "none";
}

function addTestResult(result) {
    currentRunResults.push({
        name: result.name,
        outcome: result.outcome,
        suite: result.suite,
    });

    const icon = result.outcome === "passed" ? "\u2713"
        : result.outcome === "failed" ? "\u2717"
        : "\u2014";

    const name = result.name
        .replace("test_", "")
        .replace(/_/g, " ")
        .replace(/^\w/, (c) => c.toUpperCase());

    const html = `
        <div class="test-item ${result.outcome}">
            <span class="icon">${icon}</span>
            <span class="name">${escapeHtml(name)}</span>
            <span class="suite-tag ${result.suite}">${result.suite.toUpperCase()}</span>
        </div>
    `;

    document.getElementById("testList").insertAdjacentHTML("beforeend", html);

    const suiteMap = { ui: "testListUI", ux: "testListUX", a11y: "testListA11y" };
    const suiteList = suiteMap[result.suite];
    if (suiteList) {
        document.getElementById(suiteList).insertAdjacentHTML("beforeend", html);
    }

    updateSummary();

    const list = document.getElementById("testList");
    list.scrollTop = list.scrollHeight;
}

function updateSummary() {
    const items = document.querySelectorAll("#testList .test-item");
    let passed = 0, failed = 0, skipped = 0;

    items.forEach((item) => {
        if (item.classList.contains("passed")) passed++;
        else if (item.classList.contains("failed")) failed++;
        else skipped++;
    });

    document.getElementById("resultsSummary").innerHTML = `
        <span class="passed">${passed} bestanden</span>
        <span class="failed">${failed} fehlgeschlagen</span>
        <span class="skipped">${skipped} uebersprungen</span>
    `;
}

async function onTestsCompleted(data) {
    setBtnLoading("btnRunTests", false);

    const cancelBtn = document.getElementById("btnCancel");
    cancelBtn.style.display = "none";
    cancelBtn.disabled = false;
    cancelBtn.textContent = "Abbrechen";

    const cancelled = data.status === "cancelled";
    setConnectionStatus(cancelled ? "cancelled" : "idle");

    const fill = document.getElementById("progressFill");
    fill.className = "progress-fill";
    fill.style.width = "100%";

    const total = (data.passed || 0) + (data.failed || 0) + (data.skipped || 0);
    const pct = total > 0 ? Math.round(((data.passed || 0) / total) * 100) : 0;
    const errorPct = total > 0 ? Math.round(((data.failed || 0) / total) * 100) : 0;
    const durationMs = runStartTime ? Date.now() - runStartTime : null;
    runStartTime = null;

    document.getElementById("lastRunStatus").textContent = `${pct}% bestanden`;
    document.getElementById("lastRunDuration").textContent = durationMs ? formatDuration(durationMs) : "--";
    document.getElementById("lastRunErrorRate").textContent = total > 0 ? `${errorPct}%` : "--";

    if (!cancelled && total > 0) {
        addRunToHistory({
            pct: pct,
            passed: data.passed || 0,
            failed: data.failed || 0,
            total: total,
            duration_ms: durationMs,
            results: currentRunResults.slice(),
        });
    }
    renderAllSparklines();

    // Diff-Button anzeigen, wenn Vergleichs-Lauf existiert
    const history = getRunHistory();
    document.getElementById("btnDiff").style.display =
        (!cancelled && history.length >= 2) ? "" : "none";

    stopLiveBrowser();

    // Jira-Export-Button einblenden falls Fehler vorhanden und Jira konfiguriert
    const jiraConfig = await api("/api/jira/config").catch(() => ({}));
    const hasFailed = (data.failed || 0) > 0;
    const jiraConfigured = !!(jiraConfig.base_url && jiraConfig.project_key);
    document.getElementById("btnJiraExport").style.display =
        hasFailed && jiraConfigured ? "" : "none";

    setTimeout(() => {
        loadReports();
        loadScreenshots();
    }, 1000);
}

// ========== Tabs ==========

function switchTab(tabName) {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((t) => t.classList.remove("active"));

    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add("active");
    document.getElementById(`tab-${tabName}`).classList.add("active");

    if (tabName === "output" && currentRunId) {
        loadConsoleOutput(currentRunId);
    }
}

async function loadConsoleOutput(runId) {
    const status = await api(`/api/tests/status/${runId}`);
    if (status.output) {
        renderConsoleOutput(status.output);
    }
}

// ========== Discovery ==========

async function runDiscovery() {
    const url = getUrl();
    if (!url) {
        document.getElementById("urlInput").focus();
        document.getElementById("urlInput").classList.add("input-error");
        setTimeout(() => document.getElementById("urlInput").classList.remove("input-error"), 1000);
        return;
    }

    const modal = document.getElementById("discoveryModal");
    const statusEl = document.getElementById("discoveryStatus");
    const resultsEl = document.getElementById("discoveryResults");

    modal.style.display = "flex";
    statusEl.textContent = "Discovery wird durchgefuehrt";
    statusEl.classList.add("loading-dots");
    resultsEl.innerHTML = "";

    setBtnLoading("btnDiscover", true);
    setConnectionStatus("discovering");
    startLiveBrowser();

    try {
        const creds = getCredentials();
        const data = await api("/api/discovery/run", {
            method: "POST",
            body: JSON.stringify({
                url: url,
                login_url: creds.login_url || null,
                username: creds.username || null,
                password: creds.password || null,
            }),
        });

        if (data.error) {
            statusEl.textContent = `Fehler: ${data.error}`;
            return;
        }

        const selectors = data.selectors || {};
        const found = Object.values(selectors).filter((v) => v !== null).length;
        const total = Object.keys(selectors).length;

        statusEl.textContent = `${found}/${total} Elemente erkannt`;

        let html = "";
        Object.entries(selectors).forEach(([key, value]) => {
            const cls = value ? "found" : "missing";
            const display = value || "nicht gefunden";
            html += `
                <div class="discovery-item">
                    <span class="label">${key}</span>
                    <span class="value ${cls}">${escapeHtml(display)}</span>
                </div>
            `;
        });
        // DOM-Inspektion anzeigen falls vorhanden
        const domInfo = (data.details || {})._dom_inspection;
        if (domInfo && domInfo.length > 0) {
            html += `<div class="discovery-item dom-heading"><span class="label label-strong">DOM-Inspektion (Nachrichten-Container)</span></div>`;
            domInfo.forEach((el, i) => {
                const attrs = Object.entries(el.attrs || {})
                    .filter(([k]) => k !== "class")
                    .map(([k, v]) => `${k}="${v}"`)
                    .join(" ");
                const info = `&lt;${el.tag}&gt; class="${escapeHtml(el.classes)}"${attrs ? " " + escapeHtml(attrs) : ""}`;
                const text = el.text ? ` — "${escapeHtml(el.text.substring(0, 50))}"` : "";
                html += `
                    <div class="discovery-item">
                        <span class="label">[${i}]</span>
                        <span class="value value-mono">${info}${text}</span>
                    </div>
                `;
            });
        }

        resultsEl.innerHTML = html;

        loadSelectors();
    } catch (e) {
        statusEl.textContent = `Fehler: ${e.message}`;
    } finally {
        statusEl.classList.remove("loading-dots");
        setBtnLoading("btnDiscover", false);
        setConnectionStatus("idle");
        stopLiveBrowser();
    }
}

// ========== Reports ==========

const REPORT_KIND_LABEL = {
    chatbot: "Chatbot",
    website: "Website-Scan",
    checklist: "Checkliste",
    unknown: "Sonstige",
};

let _reportsCache = [];
let _reportFilter = "all";

async function loadReports() {
    _reportsCache = await api("/api/reports");
    renderReports();
}

function filterReports(kind) {
    _reportFilter = kind;
    document.querySelectorAll(".report-filter-btn").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.kind === kind);
    });
    renderReports();
}

function renderReports() {
    const container = document.getElementById("reportList");
    const reports = _reportFilter === "all"
        ? _reportsCache
        : _reportsCache.filter((r) => (r.kind || "unknown") === _reportFilter);

    if (reports.length === 0) {
        const msg = _reportFilter === "all"
            ? "Noch keine Reports vorhanden."
            : `Keine Reports der Kategorie "${REPORT_KIND_LABEL[_reportFilter] || _reportFilter}" vorhanden.`;
        container.innerHTML = `<p class="placeholder">${escapeHtml(msg)}</p>`;
        return;
    }

    container.innerHTML = reports
        .map((r) => {
            const date = new Date(r.modified).toLocaleString("de-DE");
            const kind = r.kind || "unknown";
            const label = REPORT_KIND_LABEL[kind] || REPORT_KIND_LABEL.unknown;
            return `
                <div class="report-item" onclick="showReport('${escapeHtml(r.name)}')">
                    <span class="report-badge report-badge-${escapeAttr(kind)}">${escapeHtml(label)}</span>
                    <span class="report-meta">
                        <span class="report-date">${escapeHtml(date)}</span>
                        <span class="report-name">${escapeHtml(r.name)}</span>
                    </span>
                </div>
            `;
        })
        .join("");
}

async function showReport(name) {
    const modal = document.getElementById("reportModal");
    document.getElementById("reportModalTitle").textContent = name;
    document.getElementById("reportModalContent").textContent = "Wird geladen...";
    modal.style.display = "flex";

    const data = await api(`/api/reports/${encodeURIComponent(name)}`);
    document.getElementById("reportModalContent").textContent =
        data.content || data.error || "Fehler beim Laden";
}

function copyReportToClipboard() {
    const content = document.getElementById("reportModalContent").textContent;
    const btn = document.getElementById("copyReportBtn");
    navigator.clipboard.writeText(content).then(() => {
        btn.textContent = "Kopiert!";
        setTimeout(() => { btn.textContent = "Kopieren"; }, 2000);
    }).catch(() => {
        // Fallback fuer aeltere Browser
        const textarea = document.createElement("textarea");
        textarea.value = content;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        btn.textContent = "Kopiert!";
        setTimeout(() => { btn.textContent = "Kopieren"; }, 2000);
    });
}

// ========== Screenshots ==========

async function loadScreenshots() {
    const shots = await api("/api/screenshots");
    const container = document.getElementById("screenshotGrid");

    if (shots.length === 0) {
        container.innerHTML =
            '<p class="placeholder">Noch keine Screenshots vorhanden.</p>';
        return;
    }

    const cacheBuster = Date.now();
    container.innerHTML = shots
        .map(
            (s) => `
            <div class="screenshot-thumb" draggable="true" data-name="${escapeAttr(s.name)}" onclick="openScreenshot(event, '${s.path}?t=${cacheBuster}')">
                <img src="${s.path}?t=${cacheBuster}" alt="${escapeHtml(s.name)}" loading="lazy">
                <div class="name">${escapeHtml(s.name)}</div>
            </div>
        `
        )
        .join("");
    applyScreenshotOrder(container);
    setupScreenshotDragDrop(container);
}

function openScreenshot(e, url) {
    if (e && e.target && e.target.closest(".screenshot-thumb")?.classList.contains("dragging")) return;
    window.open(url, "_blank");
}

// ========== Modal ==========

function closeModal(id) {
    document.getElementById(id).style.display = "none";
}

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        document.querySelectorAll(".modal").forEach((m) => (m.style.display = "none"));
    }
});

document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal")) {
        e.target.style.display = "none";
    }
});

// ========== Jira-Integration ==========

async function loadJiraConfig() {
    try {
        const config = await api("/api/jira/config");
        if (config.base_url) document.getElementById("jiraBaseUrl").value = config.base_url;
        if (config.email) document.getElementById("jiraEmail").value = config.email;
        if (config.api_token) document.getElementById("jiraApiToken").value = config.api_token; // "***" wenn gesetzt
        if (config.project_key) document.getElementById("jiraProjectKey").value = config.project_key;
        if (config.issue_type) document.getElementById("jiraIssueType").value = config.issue_type;

        // Jira-Sektion automatisch oeffnen falls konfiguriert
        if (config.base_url) {
            document.getElementById("jiraSection").open = true;
        }
    } catch (e) {
        // Jira nicht konfiguriert – kein Fehler
    }
}

async function saveJiraConfig() {
    const config = {
        base_url: document.getElementById("jiraBaseUrl").value.trim(),
        email: document.getElementById("jiraEmail").value.trim(),
        api_token: document.getElementById("jiraApiToken").value.trim(),
        project_key: document.getElementById("jiraProjectKey").value.trim().toUpperCase(),
        issue_type: document.getElementById("jiraIssueType").value.trim() || "Bug",
    };

    const status = document.getElementById("jiraStatus");
    status.textContent = "Wird gespeichert...";

    const result = await api("/api/jira/config", {
        method: "POST",
        body: JSON.stringify(config),
    });

    status.textContent = result.ok ? "Gespeichert." : `Fehler: ${result.error}`;
    status.style.color = result.ok ? "var(--success)" : "var(--danger)";
}

async function testJiraConnection() {
    const status = document.getElementById("jiraStatus");
    setBtnLoading("btnJiraTest", true);
    status.textContent = "Verbindung wird getestet...";
    status.style.color = "var(--text-muted)";

    // Erst speichern, dann testen
    await saveJiraConfig();

    const result = await api("/api/jira/test-connection");
    if (result.ok) {
        status.textContent = `Verbindung OK — eingeloggt als: ${result.user}`;
        status.style.color = "var(--success)";
    } else {
        status.textContent = `Fehler: ${result.error}`;
        status.style.color = "var(--danger)";
    }
    setBtnLoading("btnJiraTest", false);
}

function openJiraExportModal() {
    const modal = document.getElementById("jiraExportModal");
    const listEl = document.getElementById("jiraExportList");
    const summaryEl = document.getElementById("jiraExportSummary");
    const statusEl = document.getElementById("jiraExportStatus");

    // Fehlgeschlagene Tests aus der Ergebnisliste ermitteln
    const failedItems = document.querySelectorAll("#testList .test-item.failed");
    const count = failedItems.length;

    summaryEl.innerHTML = count === 0
        ? "Keine fehlgeschlagenen Tests gefunden."
        : `<label class="jira-select-all"><input type="checkbox" id="jiraSelectAll" checked onchange="toggleJiraSelectAll()">Alle ${count} auswaehlen</label>`;

    listEl.innerHTML = Array.from(failedItems).map((item, i) => {
        const name = item.querySelector(".name")?.textContent || "";
        const suite = item.querySelector(".suite-tag")?.textContent || "";
        return `<label class="jira-export-row">
            <input type="checkbox" class="jira-test-cb" data-index="${i}" checked>
            <span class="jira-icon-fail">${ICON_X}</span>
            <span class="jira-export-name">${escapeHtml(name)}</span>
            <span class="suite-tag ${suite.toLowerCase()}">${escapeHtml(suite)}</span>
        </label>`;
    }).join("") || '<p class="jira-export-empty">Keine fehlgeschlagenen Tests.</p>';

    updateJiraCreateBtn();
    statusEl.textContent = "";
    modal.style.display = "flex";

    // Checkboxen ueberwachen
    listEl.querySelectorAll(".jira-test-cb").forEach(cb => {
        cb.addEventListener("change", updateJiraCreateBtn);
    });
}

function toggleJiraSelectAll() {
    const checked = document.getElementById("jiraSelectAll").checked;
    document.querySelectorAll(".jira-test-cb").forEach(cb => { cb.checked = checked; });
    updateJiraCreateBtn();
}

function updateJiraCreateBtn() {
    const selected = document.querySelectorAll(".jira-test-cb:checked").length;
    const total = document.querySelectorAll(".jira-test-cb").length;
    const btn = document.getElementById("btnJiraCreate");
    btn.disabled = selected === 0;
    btn.textContent = selected === 0
        ? "Tickets erstellen"
        : `${selected} Ticket${selected === 1 ? "" : "s"} erstellen`;

    // "Alle"-Checkbox synchron halten
    const selectAll = document.getElementById("jiraSelectAll");
    if (selectAll) selectAll.checked = selected === total;
}

function getSelectedFailedTestNames() {
    const checkboxes = document.querySelectorAll(".jira-test-cb:checked");
    const failedItems = document.querySelectorAll("#testList .test-item.failed");
    const names = [];
    checkboxes.forEach(cb => {
        const idx = parseInt(cb.dataset.index, 10);
        const item = failedItems[idx];
        if (item) {
            const nameEl = item.querySelector(".name");
            if (nameEl) names.push(nameEl.textContent.trim());
        }
    });
    return names;
}

async function createJiraTickets() {
    if (!currentRunId) return;

    const selectedNames = getSelectedFailedTestNames();
    if (selectedNames.length === 0) return;

    const statusEl = document.getElementById("jiraExportStatus");
    setBtnLoading("btnJiraCreate", true);
    statusEl.style.color = "var(--text-muted)";
    statusEl.textContent = `${selectedNames.length} Ticket${selectedNames.length === 1 ? " wird" : "s werden"} erstellt...`;

    const projectKey = document.getElementById("jiraProjectKey").value.trim().toUpperCase();
    const issueType = document.getElementById("jiraIssueType").value.trim() || "Bug";
    const url = document.getElementById("urlInput").value.trim();

    const result = await api("/api/jira/create-tickets", {
        method: "POST",
        body: JSON.stringify({
            run_id: currentRunId,
            project_key: projectKey || null,
            issue_type: issueType,
            url: url,
            selected_tests: selectedNames,
        }),
    });

    if (!result.ok) {
        statusEl.textContent = `Fehler: ${result.error}`;
        statusEl.style.color = "var(--danger)";
        setBtnLoading("btnJiraCreate", false);
        return;
    }

    const tickets = result.tickets || [];
    const succeeded = tickets.filter(t => t.ok);
    const failed = tickets.filter(t => !t.ok);

    let html = "";
    if (succeeded.length > 0) {
        html += succeeded.map(t =>
            `<div><span class="jira-icon-ok">${ICON_CHECK}</span> <a href="${escapeHtml(t.url)}" target="_blank" rel="noopener">${escapeHtml(t.key)}</a> — ${escapeHtml(t.test_name)}</div>`
        ).join("");
    }
    if (failed.length > 0) {
        html += failed.map(t =>
            `<div class="jira-icon-fail">${ICON_X} ${escapeHtml(t.test_name)}: ${escapeHtml(t.error)}</div>`
        ).join("");
    }

    document.getElementById("jiraExportList").innerHTML = html || "Keine Tickets erstellt.";
    statusEl.textContent = `${succeeded.length} Ticket${succeeded.length === 1 ? "" : "s"} erstellt${failed.length > 0 ? `, ${failed.length} fehlgeschlagen` : ""}.`;
    statusEl.style.color = failed.length > 0 ? "var(--warning)" : "var(--success)";
    setBtnLoading("btnJiraCreate", false);
}

// ========== Mode-Switcher ==========

function switchMode(mode) {
    document.querySelectorAll(".mode-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.mode === mode);
    });
    ["chatbot", "website", "hilfe"].forEach(m => {
        const el = document.getElementById("mode-" + m);
        if (el) el.style.display = m === mode ? "block" : "none";
    });
    localStorage.setItem("ep_test_mode", mode);
}

function scrollToHelp(id) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Restore mode on load
(function() {
    const saved = localStorage.getItem("ep_test_mode");
    if (saved === "website") {
        // defer to after DOM ready
        document.addEventListener("DOMContentLoaded", () => switchMode("website"));
    }
})();

// ========== Website-Scan ==========

let scanRunId = null;
let scanEventSource = null;

async function startWebsiteScan() {
    const url = document.getElementById("scanUrlInput").value.trim();
    if (!url) {
        alert("Bitte eine URL eingeben.");
        return;
    }

    const checks = [];
    document.querySelectorAll(".scan-checks input[type=checkbox]:checked").forEach(cb => {
        checks.push(cb.value);
    });
    if (checks.length === 0) {
        alert("Bitte mindestens eine Kategorie auswählen.");
        return;
    }

    // UI reset
    document.getElementById("scanResultsSection").style.display = "block";
    document.getElementById("scanProgressBar").style.display = "block";
    document.getElementById("scanProgressFill").className = "progress-fill indeterminate";
    document.getElementById("scanResultsSummary").textContent = "";
    document.getElementById("btnStartScan").style.display = "none";
    document.getElementById("btnCancelScan").style.display = "inline-flex";
    setConnectionStatus("scanning");
    const reportBtn = document.getElementById("btnScanReport");
    if (reportBtn) reportBtn.style.display = "none";

    // Clear previous results
    ["scanListAll", "scanListAccessibility", "scanListPerformance", "scanListLinks", "scanListResponsive", "scanListSeo"].forEach(id => {
        document.getElementById(id).innerHTML = "";
    });
    document.getElementById("scanScreenshotGrid").innerHTML = "";
    document.getElementById("scanScreenshotsSection").style.display = "none";

    try {
        const login_url = document.getElementById("scanLoginUrlInput").value.trim() || undefined;
        const username = document.getElementById("scanUsernameInput").value.trim() || undefined;
        const password = document.getElementById("scanPasswordInput").value.trim() || undefined;
        const pre_actions = getPreActions();

        const resp = await fetch("/api/website-scan/run", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url, checks, login_url, username, password, pre_actions}),
        });
        const data = await resp.json();
        if (data.error) {
            alert(data.error);
            onScanFinished();
            return;
        }
        scanRunId = data.run_id;
        startScanStream(scanRunId);
    } catch (e) {
        alert("Fehler beim Starten: " + e.message);
        onScanFinished();
    }
}

function startScanStream(runId) {
    if (scanEventSource) scanEventSource.close();
    scanEventSource = new EventSource(`/api/website-scan/stream/${runId}`);

    scanEventSource.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.error) {
            onScanFinished();
            return;
        }
        if (msg.type === "result") {
            addScanResult(msg.data);
        } else if (msg.type === "done") {
            onScanDone(msg.data);
            scanEventSource.close();
        }
    };

    scanEventSource.onerror = () => {
        scanEventSource.close();
        onScanFinished();
    };
}

function addScanResult(result) {
    const html = renderScanResult(result);

    // Add to "All" tab
    document.getElementById("scanListAll").insertAdjacentHTML("beforeend", html);

    // Add to category tab
    const catMap = {
        accessibility: "scanListAccessibility",
        performance: "scanListPerformance",
        links: "scanListLinks",
        responsive: "scanListResponsive",
        seo: "scanListSeo",
    };
    const listId = catMap[result.category];
    if (listId) {
        document.getElementById(listId).insertAdjacentHTML("beforeend", html);
    }

    // Screenshot zur Gallery hinzufügen
    if (result.screenshot) {
        const grid = document.getElementById("scanScreenshotGrid");
        const section = document.getElementById("scanScreenshotsSection");
        section.style.display = "block";
        const label = result.viewport ? result.viewport.charAt(0).toUpperCase() + result.viewport.slice(1) : result.name;
        grid.insertAdjacentHTML("beforeend", `
            <div class="screenshot-item" onclick="window.open('${escapeAttr(result.screenshot)}')">
                <img src="${escapeAttr(result.screenshot)}" alt="${escapeAttr(label)}" loading="lazy">
                <span class="screenshot-label">${escapeHtml(label)}</span>
            </div>
        `);
    }
}

function renderScanResult(r) {
    const icons = {passed: ICON_CHECK, failed: ICON_X, warning: ICON_WARNING, info: ICON_INFO};
    const classes = {passed: "passed", failed: "failed", warning: "warning", info: "info"};
    const icon = icons[r.status] || "•";
    const cls = classes[r.status] || "";

    let extra = "";
    if (r.screenshot) {
        extra = `<div class="scan-screenshot"><img src="${escapeHtml(r.screenshot)}" alt="${escapeHtml(r.viewport || '')}" onclick="window.open(this.src)"></div>`;
    }
    if (r.help_url) {
        extra += ` <a href="${escapeHtml(r.help_url)}" target="_blank" rel="noopener" class="help-link">Mehr Info</a>`;
    }

    const sevTip = severityTooltip(r.severity);
    return `<div class="test-item ${cls}">
        <span class="test-icon">${icon}</span>
        <div class="test-info">
            <span class="test-name">${escapeHtml(r.name)}</span>
            <span class="severity-badge ${r.severity}" data-tooltip="${escapeAttr(sevTip)}" tabindex="0">${escapeHtml(r.severity)}</span>
            <div class="test-details">${escapeHtml(r.details)}</div>
            ${extra}
        </div>
        <span class="test-tag">${escapeHtml(r.category)}</span>
    </div>`;
}

function onScanDone(data) {
    const summary = `${data.passed || 0} bestanden, ${data.failed || 0} fehlgeschlagen, ${data.warnings || 0} Warnungen`;
    document.getElementById("scanResultsSummary").textContent = summary;

    // Report-Button anzeigen wenn Report generiert wurde
    const reportBtn = document.getElementById("btnScanReport");
    if (reportBtn && data.report) {
        reportBtn.style.display = "inline-flex";
        reportBtn.onclick = () => showReport(data.report);
    }

    onScanFinished();
    loadReports();
}

function onScanFinished() {
    document.getElementById("scanProgressBar").style.display = "none";
    document.getElementById("btnStartScan").style.display = "inline-flex";
    document.getElementById("btnCancelScan").style.display = "none";
    setConnectionStatus("idle");
}

async function cancelWebsiteScan() {
    if (!scanRunId) return;
    await fetch(`/api/website-scan/cancel/${scanRunId}`, {method: "POST"});
    if (scanEventSource) scanEventSource.close();
    onScanFinished();
}

function switchScanTab(tabName) {
    // Deactivate all scan tabs
    document.querySelectorAll("#scanResultsSection .tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll("#scanResultsSection .tab-content").forEach(c => c.classList.remove("active"));

    // Activate selected
    document.querySelector(`#scanResultsSection .tab[data-tab="${tabName}"]`).classList.add("active");
    document.getElementById(`tab-${tabName}`).classList.add("active");
}

// ========== Vor-Aktionen ==========

let detectedData = null;

function getPreActions() {
    const actions = [];

    // Erkannte Felder mit eingegebenen Werten
    document.querySelectorAll(".detected-field-row").forEach(row => {
        const label = row.dataset.label;
        const value = row.querySelector(".df-value").value.trim();
        if (value) {
            actions.push({type: "fill", label, value});
        }
    });

    // Ausgewählte Buttons
    document.querySelectorAll(".detected-btn-row input:checked").forEach(cb => {
        actions.push({type: "click", label: cb.dataset.label});
        // Kurz warten nach Klick
        actions.push({type: "wait", value: "2000"});
    });

    return actions;
}

async function detectPageElements() {
    const url = document.getElementById("scanUrlInput").value.trim();
    if (!url) { alert("Bitte zuerst eine URL eingeben."); return; }

    setBtnLoading("btnDetect", true);
    setConnectionStatus("discovering");

    try {
        const resp = await fetch("/api/website-scan/detect", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url}),
        });
        const data = await resp.json();
        if (data.error) { alert(data.error); return; }
        detectedData = data;
        renderDetectedForm(data);
    } catch (e) {
        alert("Fehler: " + e.message);
    } finally {
        setBtnLoading("btnDetect", false);
        setConnectionStatus("idle");
    }
}

function renderDetectedForm(data) {
    const fieldsContainer = document.getElementById("detectedFields");
    const buttonsContainer = document.getElementById("detectedButtons");
    const section = document.getElementById("preActionsDetected");
    fieldsContainer.innerHTML = "";
    buttonsContainer.innerHTML = "";

    const inputs = data.inputs || [];
    const buttons = data.buttons || [];

    if (inputs.length === 0 && buttons.length === 0) {
        fieldsContainer.innerHTML = '<p class="detected-empty">Keine interaktiven Elemente gefunden.</p>';
        section.style.display = "block";
        return;
    }

    // Eingabefelder als echte Formularzeilen anzeigen
    inputs.forEach(inp => {
        const label = inp.placeholder || inp.label || inp.name || "Unbenannt";
        const inputType = inp.type === "password" ? "password" : "text";
        const row = document.createElement("div");
        row.className = "detected-field-row";
        row.dataset.label = label;
        row.innerHTML = `
            <label class="df-label">${escapeHtml(label)}</label>
            <input type="${inputType}" class="text-input df-value" placeholder="Wert eingeben (leer = überspringen)">
        `;
        fieldsContainer.appendChild(row);
    });

    // Buttons als Checkboxen anzeigen
    buttons.forEach(b => {
        const row = document.createElement("label");
        row.className = "detected-btn-row";
        row.innerHTML = `
            <input type="checkbox" data-label="${escapeAttr(b.text)}">
            <span>${escapeHtml(b.text)}</span>
        `;
        buttonsContainer.appendChild(row);
    });

    section.style.display = "block";
}

// ========== Theme-Toggle (Dark Mode) ==========

function toggleTheme() {
    const cur = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("ep_theme", next); } catch (e) {}
    syncThemeToggleState();
}

function syncThemeToggleState() {
    const btn = document.getElementById("themeToggle");
    if (!btn) return;
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    btn.setAttribute("aria-pressed", String(isDark));
    btn.title = isDark ? "Zum hellen Modus wechseln" : "Zum dunklen Modus wechseln";
}

// ========== Run-History + Sparkline ==========

const HISTORY_KEY = "ep_test_history";
const HISTORY_MAX = 5;

function getRunHistory() {
    try {
        const raw = localStorage.getItem(HISTORY_KEY);
        if (!raw) return [];
        const arr = JSON.parse(raw);
        return Array.isArray(arr) ? arr : [];
    } catch (e) { return []; }
}

function addRunToHistory(run) {
    const list = getRunHistory();
    list.push({ pct: run.pct, passed: run.passed, failed: run.failed, total: run.total, ts: Date.now() });
    while (list.length > HISTORY_MAX) list.shift();
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(list)); } catch (e) {}
}

function renderAllSparklines() {
    renderSparkline("cardLastRun",     r => r.pct,                                                  { fixedMin: 0, fixedMax: 100, label: "Pass-Rate-Trend",  fmt: v => `${Math.round(v)}%` });
    renderSparkline("cardDuration",    r => (r.duration_ms != null ? r.duration_ms : null),         { label: "Dauer-Trend",       fmt: v => formatDuration(v) });
    renderSparkline("cardErrorRate",   r => r.total > 0 ? (r.failed / r.total) * 100 : 0,           { fixedMin: 0, fixedMax: 100, label: "Fehlerraten-Trend", fmt: v => `${Math.round(v)}%` });
}

function renderSparkline(cardId, getValue, opts = {}) {
    const card = document.getElementById(cardId);
    if (!card) return;
    let svg = card.querySelector(".stat-sparkline");
    let empty = card.querySelector(".stat-sparkline-empty");

    const history = getRunHistory();
    const values = history.map(getValue).filter(v => v != null && !isNaN(v));

    if (values.length < 2) {
        if (svg) svg.remove();
        if (!empty) {
            empty = document.createElement("span");
            empty.className = "stat-sparkline-empty";
            empty.textContent = "Trend ab 2 Läufen";
            card.appendChild(empty);
        }
        return;
    }
    if (empty) empty.remove();

    const w = 80, h = 28, pad = 2;
    const min = opts.fixedMin !== undefined ? Math.min(...values, opts.fixedMin) : Math.min(...values);
    const max = opts.fixedMax !== undefined ? Math.max(...values, opts.fixedMax) : Math.max(...values);
    const range = max - min || 1;
    const stepX = (w - pad * 2) / (values.length - 1);
    const points = values.map((v, i) => {
        const x = pad + i * stepX;
        const y = h - pad - ((v - min) / range) * (h - pad * 2);
        return [x, y];
    });
    const linePath = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
    const areaPath = `${linePath} L${points[points.length-1][0].toFixed(1)} ${h - pad} L${points[0][0].toFixed(1)} ${h - pad} Z`;
    const last = points[points.length - 1];

    if (!svg) {
        svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("class", "stat-sparkline");
        svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
        svg.setAttribute("aria-label", opts.label || "Trend");
        card.appendChild(svg);
    }
    svg.innerHTML = `
        <path class="area" d="${areaPath}"></path>
        <path class="line" d="${linePath}"></path>
        <circle cx="${last[0].toFixed(1)}" cy="${last[1].toFixed(1)}" r="2.5"></circle>
    `;
    const fmt = opts.fmt || (v => v);
    svg.setAttribute("title", values.map(fmt).join(" → "));
}

// Beibehalten als Alias, falls noch irgendwo referenziert
function renderRunSparkline() {
    renderAllSparklines();
}

// Vergleich der letzten beiden Läufe
function diffRuns(currentResults, previousResults) {
    const prevMap = new Map((previousResults || []).map(r => [r.name, r.outcome]));
    const curMap = new Map((currentResults || []).map(r => [r.name, r.outcome]));

    const newlyFailed = [];
    const newlyPassed = [];
    const stillFailing = [];
    const newTests = [];

    for (const cur of currentResults || []) {
        const prev = prevMap.get(cur.name);
        if (prev === undefined) {
            newTests.push(cur);
        } else if (cur.outcome === "failed" && prev !== "failed") {
            newlyFailed.push(cur);
        } else if (cur.outcome === "passed" && prev === "failed") {
            newlyPassed.push(cur);
        } else if (cur.outcome === "failed" && prev === "failed") {
            stillFailing.push(cur);
        }
    }

    const removedTests = (previousResults || []).filter(p => !curMap.has(p.name));

    return { newlyFailed, newlyPassed, stillFailing, newTests, removedTests };
}

function openDiffModal() {
    const history = getRunHistory();
    if (history.length < 2) return;

    const current = history[history.length - 1];
    const previous = history[history.length - 2];
    const diff = diffRuns(current.results || [], previous.results || []);

    const summaryEl = document.getElementById("diffSummary");
    const contentEl = document.getElementById("diffContent");

    summaryEl.innerHTML = `
        <div class="diff-summary-row">
            <span class="diff-stat diff-newly-failed">${diff.newlyFailed.length} neu fehlgeschlagen</span>
            <span class="diff-stat diff-newly-passed">${diff.newlyPassed.length} neu bestanden</span>
            <span class="diff-stat diff-still-failing">${diff.stillFailing.length} weiter fehlgeschlagen</span>
            <span class="diff-stat diff-new-tests">${diff.newTests.length} neu</span>
            <span class="diff-stat diff-removed-tests">${diff.removedTests.length} entfernt</span>
        </div>
        <div class="diff-meta">
            Vergleich: ${new Date(previous.ts).toLocaleString("de-DE")} → ${new Date(current.ts).toLocaleString("de-DE")}
        </div>
    `;

    const renderSection = (title, tests, cls) => {
        if (!tests.length) return "";
        const items = tests.map(t => {
            const name = t.name.replace("test_", "").replace(/_/g, " ").replace(/^\w/, c => c.toUpperCase());
            const suite = t.suite ? `<span class="suite-tag ${t.suite}">${t.suite.toUpperCase()}</span>` : "";
            return `<li class="diff-item ${cls}"><span class="name">${escapeHtml(name)}</span>${suite}</li>`;
        }).join("");
        return `<div class="diff-section"><h3>${title} (${tests.length})</h3><ul class="diff-list">${items}</ul></div>`;
    };

    contentEl.innerHTML =
        renderSection("Neu fehlgeschlagen", diff.newlyFailed, "newly-failed") +
        renderSection("Neu bestanden", diff.newlyPassed, "newly-passed") +
        renderSection("Weiterhin fehlgeschlagen", diff.stillFailing, "still-failing") +
        renderSection("Neue Tests", diff.newTests, "new-tests") +
        renderSection("Nicht mehr ausgeführt", diff.removedTests, "removed-tests") ||
        '<p class="diff-empty">Keine Unterschiede zwischen den Läufen.</p>';

    document.getElementById("diffModal").style.display = "flex";
}

// Initial-State der Stat-Cards aus History befüllen
function applyLatestRunToCards() {
    const history = getRunHistory();
    if (history.length === 0) return;
    const last = history[history.length - 1];
    const total = last.total || 0;
    const failed = last.failed || 0;
    document.getElementById("lastRunStatus").textContent = `${last.pct}% bestanden`;
    document.getElementById("lastRunDuration").textContent = formatDuration(last.duration_ms);
    document.getElementById("lastRunErrorRate").textContent = total > 0 ? `${Math.round((failed / total) * 100)}%` : "--";
}

// ========== Screenshot Drag&Drop ==========

const SCREENSHOT_ORDER_KEY = "ep_screenshot_order";

function getScreenshotOrder() {
    try {
        const raw = localStorage.getItem(SCREENSHOT_ORDER_KEY);
        if (!raw) return [];
        const arr = JSON.parse(raw);
        return Array.isArray(arr) ? arr : [];
    } catch (e) { return []; }
}

function saveScreenshotOrder(grid) {
    const names = Array.from(grid.querySelectorAll(".screenshot-thumb")).map(t => t.dataset.name);
    try { localStorage.setItem(SCREENSHOT_ORDER_KEY, JSON.stringify(names)); } catch (e) {}
}

function applyScreenshotOrder(grid) {
    const order = getScreenshotOrder();
    if (!order.length) return;
    const thumbs = Array.from(grid.querySelectorAll(".screenshot-thumb"));
    thumbs.sort((a, b) => {
        const ia = order.indexOf(a.dataset.name);
        const ib = order.indexOf(b.dataset.name);
        if (ia === -1 && ib === -1) return 0;
        if (ia === -1) return 1;
        if (ib === -1) return -1;
        return ia - ib;
    });
    thumbs.forEach(t => grid.appendChild(t));
}

let dragSrc = null;

function setupScreenshotDragDrop(grid) {
    const thumbs = grid.querySelectorAll(".screenshot-thumb");
    thumbs.forEach(t => {
        t.addEventListener("dragstart", (e) => {
            dragSrc = t;
            t.classList.add("dragging");
            e.dataTransfer.effectAllowed = "move";
            try { e.dataTransfer.setData("text/plain", t.dataset.name || ""); } catch (err) {}
        });
        t.addEventListener("dragend", () => {
            t.classList.remove("dragging");
            grid.querySelectorAll(".drag-over").forEach(el => el.classList.remove("drag-over"));
            dragSrc = null;
        });
        t.addEventListener("dragover", (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = "move";
            if (dragSrc && dragSrc !== t) t.classList.add("drag-over");
        });
        t.addEventListener("dragleave", () => {
            t.classList.remove("drag-over");
        });
        t.addEventListener("drop", (e) => {
            e.preventDefault();
            t.classList.remove("drag-over");
            if (!dragSrc || dragSrc === t) return;
            const all = Array.from(grid.children);
            const srcIdx = all.indexOf(dragSrc);
            const tgtIdx = all.indexOf(t);
            if (srcIdx < tgtIdx) t.after(dragSrc);
            else t.before(dragSrc);
            saveScreenshotOrder(grid);
        });
    });
}
