/**
 * EP-Testing-Tool: Frontend-Logik
 */

let currentRunId = null;
let eventSource = null;

// ========== Initialisierung ==========

document.addEventListener("DOMContentLoaded", () => {
    loadEnvironments();
    loadSelectors();
    loadReports();
    loadScreenshots();
});

// ========== API-Aufrufe ==========

async function api(url, options = {}) {
    const resp = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    return resp.json();
}

// ========== Umgebungen ==========

async function loadEnvironments() {
    const envs = await api("/api/environments");
    const select = document.getElementById("envSelect");
    select.innerHTML = "";

    const names = Object.keys(envs);
    document.getElementById("envCount").textContent = names.length;

    names.forEach((name) => {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = `${name} — ${envs[name].description || envs[name].url}`;
        select.appendChild(opt);
    });
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
    const env = document.getElementById("envSelect").value;
    const suite = document.getElementById("suiteSelect").value || null;

    // UI-Status aktualisieren
    const btn = document.getElementById("btnRunTests");
    btn.disabled = true;
    btn.textContent = "Laeuft...";
    document.querySelector(".status-dot").classList.add("running");
    document.getElementById("connectionStatus").querySelector("span:last-child") ||
        (document.getElementById("connectionStatus").innerHTML =
            '<span class="status-dot running"></span> Tests laufen...');

    // Ergebnisse zuruecksetzen
    clearResults();
    document.getElementById("resultsSection").style.display = "block";
    document.getElementById("progressBar").style.display = "block";
    document.getElementById("progressFill").className = "progress-fill indeterminate";

    // Testlauf starten
    const data = await api("/api/tests/run", {
        method: "POST",
        body: JSON.stringify({ environment: env, suite: suite }),
    });

    currentRunId = data.run_id;

    // SSE-Stream fuer Live-Updates
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
        // Bei Fehler: Polling als Fallback
        eventSource.close();
        eventSource = null;
        pollStatus(runId);
    };
}

async function pollStatus(runId) {
    const interval = setInterval(async () => {
        const status = await api(`/api/tests/status/${runId}`);

        // Neue Ergebnisse anzeigen
        const displayed = document.querySelectorAll(".test-item").length;
        if (status.results.length > displayed) {
            for (let i = displayed; i < status.results.length; i++) {
                addTestResult(status.results[i]);
            }
        }

        // Konsolen-Output
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

    // Zur Gesamtliste hinzufuegen
    document.getElementById("testList").insertAdjacentHTML("beforeend", html);

    // Zur Suite-Liste hinzufuegen
    const suiteMap = { ui: "testListUI", ux: "testListUX", a11y: "testListA11y" };
    const suiteList = suiteMap[result.suite];
    if (suiteList) {
        document.getElementById(suiteList).insertAdjacentHTML("beforeend", html);
    }

    // Zusammenfassung aktualisieren
    updateSummary();

    // Auto-Scroll
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

    // Fortschrittsbalken
    const fill = document.getElementById("progressFill");
    fill.className = "progress-fill";
    fill.style.width = "100%";

    // Letzter Lauf
    const total = (data.passed || 0) + (data.failed || 0) + (data.skipped || 0);
    const pct = total > 0 ? Math.round(((data.passed || 0) / total) * 100) : 0;
    document.getElementById("lastRunStatus").textContent = `${pct}% bestanden`;

    // Reports und Screenshots neu laden
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

    // Konsolen-Output laden wenn Tab gewechselt wird
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
    const env = document.getElementById("envSelect").value;
    const modal = document.getElementById("discoveryModal");
    const statusEl = document.getElementById("discoveryStatus");
    const resultsEl = document.getElementById("discoveryResults");

    modal.style.display = "flex";
    statusEl.textContent = "Discovery wird durchgefuehrt...";
    resultsEl.innerHTML = "";

    document.getElementById("btnDiscover").disabled = true;

    try {
        const data = await api("/api/discovery/run", {
            method: "POST",
            body: JSON.stringify({ environment: env }),
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

        // Selektoren-Anzeige aktualisieren
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

// ========== Screenshots ==========

async function loadScreenshots() {
    const shots = await api("/api/screenshots");
    const container = document.getElementById("screenshotGrid");

    if (shots.length === 0) {
        container.innerHTML =
            '<p class="placeholder">Noch keine Screenshots vorhanden.</p>';
        return;
    }

    container.innerHTML = shots
        .map(
            (s) => `
            <div class="screenshot-thumb" onclick="window.open('${s.path}', '_blank')">
                <img src="${s.path}" alt="${escapeHtml(s.name)}" loading="lazy">
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

// Escape-Taste schliesst Modals
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        document.querySelectorAll(".modal").forEach((m) => (m.style.display = "none"));
    }
});

// Klick ausserhalb des Modals schliesst es
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
