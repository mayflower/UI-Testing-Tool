/**
 * UI/UX-Testing-Tool: Frontend-Logik
 */

let currentRunId = null;
let eventSource = null;
let savedEnvironments = {};
let editingEnvName = null;

// ========== Initialisierung ==========

document.addEventListener("DOMContentLoaded", () => {
    restoreFormFields();
    loadEnvironments();
    loadSelectors();
    loadReports();
    loadScreenshots();
    loadJiraConfig();

    // Enter-Taste im URL-Feld startet Tests
    document.getElementById("urlInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") runTests();
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

// ========== API-Aufrufe ==========

async function api(url, options = {}) {
    const resp = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    return resp.json();
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
                    <button class="env-chip-action env-chip-edit" onclick="editEnvironment('${escapeHtml(name)}')" title="Bearbeiten">&#9998;</button>
                    <button class="env-chip-action env-chip-delete" onclick="deleteEnvironment('${escapeHtml(name)}')" title="Entfernen">&times;</button>
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
    const btn = document.getElementById("btnRunTests");
    btn.disabled = true;
    btn.textContent = "Laeuft...";
    document.getElementById("btnCancel").style.display = "";
    document.getElementById("connectionStatus").innerHTML =
        '<span class="status-dot running"></span> Tests laufen...';

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
            document.getElementById("consoleOutput").textContent =
                status.output.join("\n");
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
}

function addTestResult(result) {
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
    const btn = document.getElementById("btnRunTests");
    btn.disabled = false;
    btn.textContent = "Tests starten";

    const cancelBtn = document.getElementById("btnCancel");
    cancelBtn.style.display = "none";
    cancelBtn.disabled = false;
    cancelBtn.textContent = "Abbrechen";

    const cancelled = data.status === "cancelled";
    document.getElementById("connectionStatus").innerHTML =
        cancelled
            ? '<span class="status-dot"></span> Abgebrochen'
            : '<span class="status-dot"></span> Bereit';

    const fill = document.getElementById("progressFill");
    fill.className = "progress-fill";
    fill.style.width = "100%";

    const total = (data.passed || 0) + (data.failed || 0) + (data.skipped || 0);
    const pct = total > 0 ? Math.round(((data.passed || 0) / total) * 100) : 0;
    document.getElementById("lastRunStatus").textContent = `${pct}% bestanden`;

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
        document.getElementById("consoleOutput").textContent =
            status.output.join("\n");
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
    statusEl.textContent = "Discovery wird durchgefuehrt...";
    resultsEl.innerHTML = "";

    document.getElementById("btnDiscover").disabled = true;

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
            html += `<div class="discovery-item" style="margin-top:0.75rem;"><span class="label" style="font-weight:600;">DOM-Inspektion (Nachrichten-Container)</span></div>`;
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
                        <span class="value" style="font-family:monospace;font-size:0.75rem;">${info}${text}</span>
                    </div>
                `;
            });
        }

        resultsEl.innerHTML = html;

        loadSelectors();
    } catch (e) {
        statusEl.textContent = `Fehler: ${e.message}`;
    } finally {
        document.getElementById("btnDiscover").disabled = false;
    }
}

// ========== Reports ==========

async function loadReports() {
    const reports = await api("/api/reports");
    const container = document.getElementById("reportList");

    if (reports.length === 0) {
        container.innerHTML = '<p class="placeholder">Noch keine Reports vorhanden.</p>';
        return;
    }

    container.innerHTML = reports
        .map((r) => {
            const date = new Date(r.modified).toLocaleString("de-DE");
            return `
                <div class="report-item" onclick="showReport('${escapeHtml(r.name)}')">
                    <span class="report-name">${escapeHtml(r.name)}</span>
                    <span class="report-date">${date}</span>
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
            <div class="screenshot-thumb" onclick="window.open('${s.path}?t=${cacheBuster}', '_blank')">
                <img src="${s.path}?t=${cacheBuster}" alt="${escapeHtml(s.name)}" loading="lazy">
                <div class="name">${escapeHtml(s.name)}</div>
            </div>
        `
        )
        .join("");
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
    const btn = document.getElementById("btnJiraTest");
    btn.disabled = true;
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
    btn.disabled = false;
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
        : `<label style="cursor:pointer;user-select:none;"><input type="checkbox" id="jiraSelectAll" checked onchange="toggleJiraSelectAll()" style="margin-right:0.4rem;">Alle ${count} auswaehlen</label>`;

    listEl.innerHTML = Array.from(failedItems).map((item, i) => {
        const name = item.querySelector(".name")?.textContent || "";
        const suite = item.querySelector(".suite-tag")?.textContent || "";
        return `<label style="display:flex;align-items:center;padding:0.35rem 0;border-bottom:1px solid var(--border);font-size:0.85rem;cursor:pointer;gap:0.4rem;">
            <input type="checkbox" class="jira-test-cb" data-index="${i}" checked>
            <span style="color:var(--danger);">&#10007;</span>
            <span style="flex:1;">${escapeHtml(name)}</span>
            <span class="suite-tag ${suite.toLowerCase()}">${escapeHtml(suite)}</span>
        </label>`;
    }).join("") || '<p style="color:var(--text-muted);font-size:0.85rem;">Keine fehlgeschlagenen Tests.</p>';

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
    const btn = document.getElementById("btnJiraCreate");
    btn.disabled = true;
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
        btn.disabled = false;
        return;
    }

    const tickets = result.tickets || [];
    const succeeded = tickets.filter(t => t.ok);
    const failed = tickets.filter(t => !t.ok);

    let html = "";
    if (succeeded.length > 0) {
        html += succeeded.map(t =>
            `<div>&#10003; <a href="${escapeHtml(t.url)}" target="_blank" rel="noopener">${escapeHtml(t.key)}</a> — ${escapeHtml(t.test_name)}</div>`
        ).join("");
    }
    if (failed.length > 0) {
        html += failed.map(t =>
            `<div style="color:var(--danger);">&#10007; ${escapeHtml(t.test_name)}: ${escapeHtml(t.error)}</div>`
        ).join("");
    }

    document.getElementById("jiraExportList").innerHTML = html || "Keine Tickets erstellt.";
    statusEl.textContent = `${succeeded.length} Ticket${succeeded.length === 1 ? "" : "s"} erstellt${failed.length > 0 ? `, ${failed.length} fehlgeschlagen` : ""}.`;
    statusEl.style.color = failed.length > 0 ? "var(--warning)" : "var(--success)";
}

// ========== Hilfsfunktionen ==========

function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
