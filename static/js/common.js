/**
 * UI/UX-Testing-Tool: Gemeinsame Helper (zustandslos)
 * Wird vor app.js geladen — alle Funktionen/Konstanten leben im globalen Scope.
 */

// ========== SVG-Icons (Feather/Lucide-Stil, currentColor) ==========

const ICON_EDIT = '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"></path></svg>';
const ICON_TRASH = '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path><path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"></path></svg>';
const ICON_CHECK = '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
const ICON_X = '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
const ICON_WARNING = '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
const ICON_INFO = '<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';

// ========== Escape-Helpers ==========

function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}

// ========== API-Aufrufe ==========

async function api(url, options = {}) {
    const resp = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    return resp.json();
}

// ========== Button-Loading-Spinner ==========

function setBtnLoading(btnOrId, loading) {
    const btn = typeof btnOrId === "string" ? document.getElementById(btnOrId) : btnOrId;
    if (!btn) return;
    if (loading) {
        btn.classList.add("is-loading");
        btn.disabled = true;
    } else {
        btn.classList.remove("is-loading");
        btn.disabled = false;
    }
}

// ========== Connection-Status-Indikator ==========

function setConnectionStatus(state, customLabel) {
    const states = {
        idle:        { cls: "idle",        text: "Bereit" },
        running:     { cls: "running",     text: "Tests laufen..." },
        discovering: { cls: "discovering", text: "Discovery läuft..." },
        scanning:    { cls: "scanning",    text: "Scan läuft..." },
        error:       { cls: "error",       text: "Fehler" },
        cancelled:   { cls: "cancelled",   text: "Abgebrochen" },
        success:     { cls: "success",     text: "Bereit" },
    };
    const s = states[state] || states.idle;
    const label = customLabel || s.text;
    const el = document.getElementById("connectionStatus");
    if (!el) return;
    el.innerHTML = `<span class="status-dot ${s.cls}"></span> ${escapeHtml(label)}`;
}

// ========== Severity-Tooltips ==========

function severityTooltip(severity) {
    const tips = {
        critical: "Kritisch — blockiert Nutzer komplett, sofort beheben.\nz.B. fehlender Alt-Text bei funktionalen Bildern, Tastaturfalle, Seite lädt nicht.",
        serious:  "Schwerwiegend — beeinträchtigt viele Nutzer, hohe Priorität.\nz.B. fehlendes Form-Label, broken Link, kein H1, fehlender <title>, fehlender Login-Button.",
        moderate: "Mittel — Verbesserung empfohlen, kein direkter Blocker.\nz.B. unklare Linktexte, niedriger Kontrast, fehlende Meta-Description, horizontaler Overflow.",
        minor:    "Gering — kosmetisch oder Edge-Case, niedrige Priorität.\nz.B. unbenötigtes ARIA-Attribut, Performance-Wert nicht messbar.",
        info:     "Info — Hinweis ohne Bewertung, kein Handlungsbedarf.\nz.B. Anzahl Links auf der Seite, gefundene Open-Graph-Tags, Heading-Struktur.",
        warning:  "Warnung — auffällig, aber kein harter Fehler.\nz.B. langsame Ladezeit, kleine SEO-Optimierung möglich, Pre-Action-Fehler.",
    };
    return tips[severity] || "";
}

// ========== Konsole zeilenweise mit Severity-Klassen rendern ==========

function classifyConsoleLine(line) {
    if (/\b(error|fail(ed)?|exception|traceback|assert(ionerror)?)\b|\bE \b|✗/i.test(line)) return "error";
    if (/\b(warn(ing)?|deprecat)/i.test(line)) return "warn";
    if (/\b(passed|ok|success)\b|✓/i.test(line)) return "success";
    return "info";
}

function renderConsoleOutput(lines) {
    const out = document.getElementById("consoleOutput");
    if (!out) return;
    out.innerHTML = lines.map(line => {
        const cls = classifyConsoleLine(line);
        return `<span class="console-line-${cls}">${escapeHtml(line)}</span>`;
    }).join("\n");
    out.scrollTop = out.scrollHeight;
}

// ========== Dauer-Formatierung ==========

function formatDuration(ms) {
    if (ms == null || isNaN(ms) || ms < 0) return "--";
    const totalSec = Math.round(ms / 1000);
    if (totalSec < 60) return `${totalSec}s`;
    const min = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    if (min < 60) return `${min}m ${sec.toString().padStart(2, "0")}s`;
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${h}h ${m.toString().padStart(2, "0")}m`;
}
