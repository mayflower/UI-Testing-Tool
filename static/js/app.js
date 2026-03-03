/**
 * EP-Testing-Tool: Frontend-Logik
 */

let currentRunId = null;
let eventSource = null;
let savedEnvironments = {};

// ========== Initialisierung ==========

document.addEventListener("DOMContentLoaded", () => {
    restoreFormFields();
    loadEnvironments();
    loadSelectors();
    loadReports();
    loadScreenshots();

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
                <button class="env-chip" onclick="selectEnvironment('${escapeHtml(name)}')" title="${escapeHtml(env.url)}">
                    <span class="env-chip-name">${escapeHtml(name)}${hasLogin}</span>
                    <span class="env-chip-desc">${escapeHtml(env.url)}${desc}</span>
                </button>
                <button class="env-chip-delete" onclick="deleteEnvironment('${escapeHtml(name)}')" title="Entfernen">&times;</button>
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

    document.getElementById("saveEnvUrl").value = url;
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

    await api("/api/environments", {
        method: "POST",
        body: JSON.stringify({ name, url, description, login_url, username, password }),
    });

    closeModal("saveEnvModal");
    loadEnvironments();
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
    startEventStream(data.run_id);
}

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

function onTestsCompleted(data) {
    const btn = document.getElementById("btnRunTests");
    btn.disabled = false;
    btn.textContent = "Tests starten";

    document.getElementById("connectionStatus").innerHTML =
        '<span class="status-dot"></span> Bereit';

    const fill = document.getElementById("progressFill");
    fill.className = "progress-fill";
    fill.style.width = "100%";

    const total = (data.passed || 0) + (data.failed || 0) + (data.skipped || 0);
    const pct = total > 0 ? Math.round(((data.passed || 0) / total) * 100) : 0;
    document.getElementById("lastRunStatus").textContent = `${pct}% bestanden`;

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

// ========== Hilfsfunktionen ==========

function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
