"""Website-Scanner: Umfassende Prüfung beliebiger Websites."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import requests
from playwright.sync_api import sync_playwright

from config.settings import SCREENSHOTS_DIR, HEADLESS, SLOW_MO


# Performance-Schwellwerte (in ms)
_PERF_THRESHOLDS = {
    "ttfb": {"good": 800, "moderate": 1800},
    "fcp": {"good": 1800, "moderate": 3000},
    "lcp": {"good": 2500, "moderate": 4000},
    "dom_load": {"good": 2000, "moderate": 4000},
    "total_load": {"good": 3000, "moderate": 6000},
}

_VIEWPORTS = [
    {"name": "mobile", "width": 375, "height": 812},
    {"name": "tablet", "width": 768, "height": 1024},
    {"name": "desktop", "width": 1440, "height": 900},
]


def _rate(value_ms: float, key: str) -> str:
    """Bewerte einen Performance-Wert."""
    t = _PERF_THRESHOLDS.get(key, {"good": 2000, "moderate": 4000})
    if value_ms <= t["good"]:
        return "passed"
    if value_ms <= t["moderate"]:
        return "warning"
    return "failed"


class WebsiteScanner:
    """Führt umfassende Checks auf einer beliebigen URL aus."""

    def __init__(
        self,
        url: str,
        checks: list[str] | None = None,
        login_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        pre_actions: list[dict] | None = None,
    ):
        self.url = url
        self.checks = checks or ["accessibility", "performance", "links", "responsive", "seo"]
        self.login_url = login_url
        self.username = username
        self.password = password
        self.pre_actions = pre_actions or []
        self.results: list[dict] = []
        self.status = "pending"
        self._cancel = False

    def _perform_login(self, page):
        """Login durchführen falls Credentials vorhanden."""
        if not self.username and not self.password:
            return
        from utils.login_helper import perform_login, perform_login_on_page, has_login_form, needs_login
        if not needs_login(self.username, self.password):
            return

        if self.login_url:
            perform_login(page, self.login_url, self.username, self.password)
        elif has_login_form(page, wait_seconds=5):
            perform_login_on_page(page, self.username, self.password)
            page.wait_for_load_state("networkidle")

    def _take_screenshot(self, page, name: str, label: str):
        """Screenshot aufnehmen und als Ergebnis hinzufügen."""
        scan_dir = SCREENSHOTS_DIR / "website_scan"
        scan_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        domain = urlparse(self.url).netloc.replace(".", "_")
        filename = f"{domain}_{name}_{ts}.png"
        path = scan_dir / filename
        try:
            page.screenshot(path=str(path), full_page=True)
            self._add("screenshots", name, "info", "info", label,
                       screenshot=f"/static_screenshots/website_scan/{filename}",
                       viewport=label)
        except Exception:
            pass

    def _execute_pre_actions(self, page):
        """Führe Vor-Aktionen aus (fill, click, wait).

        Felder werden per Label/Placeholder-Text identifiziert,
        Buttons per sichtbarem Text.
        """
        for action in self.pre_actions:
            act_type = action.get("type")
            label = action.get("label", "")
            value = action.get("value", "")
            selector = action.get("selector", "")

            try:
                if act_type == "fill":
                    el = self._find_input(page, label, selector)
                    el.click()
                    el.fill(value)
                elif act_type == "click":
                    el = self._find_button(page, label, selector)
                    el.click()
                    page.wait_for_timeout(500)
                elif act_type == "wait":
                    ms = int(value) if value else 1000
                    page.wait_for_timeout(ms)
            except Exception as e:
                self._add("general", "pre_action_error", "warning", "moderate",
                          f"Vor-Aktion fehlgeschlagen: {act_type} '{label or selector}' — {e}")

    @staticmethod
    def _find_input(page, label: str, selector: str = ""):
        """Finde ein Eingabefeld per Placeholder, Label-Text oder Selektor."""
        if selector:
            return page.locator(selector)
        # Versuche verschiedene Strategien
        # 1. Placeholder enthält den Text
        el = page.locator(f'input[placeholder*="{label}" i], textarea[placeholder*="{label}" i]')
        if el.count() > 0:
            return el.first
        # 2. Label-Element mit passendem Text
        el = page.locator(f'label:has-text("{label}") + input, label:has-text("{label}") + textarea')
        if el.count() > 0:
            return el.first
        # 3. aria-label
        el = page.locator(f'input[aria-label*="{label}" i], textarea[aria-label*="{label}" i]')
        if el.count() > 0:
            return el.first
        # 4. name-Attribut
        el = page.locator(f'input[name*="{label}" i]')
        if el.count() > 0:
            return el.first
        raise ValueError(f"Eingabefeld '{label}' nicht gefunden")

    @staticmethod
    def _find_button(page, label: str, selector: str = ""):
        """Finde einen Button per Text oder Selektor."""
        if selector:
            return page.locator(selector)
        # 1. Button/Link mit exaktem oder enthaltenem Text
        el = page.locator(f'button:has-text("{label}"), a:has-text("{label}"), input[type="submit"][value*="{label}" i]')
        if el.count() > 0:
            return el.first
        # 2. role=button
        el = page.locator(f'[role="button"]:has-text("{label}")')
        if el.count() > 0:
            return el.first
        raise ValueError(f"Button '{label}' nicht gefunden")

    def run(self):
        """Führe alle ausgewählten Checks aus."""
        self.status = "running"
        dispatch = {
            "accessibility": self._check_accessibility,
            "performance": self._check_performance,
            "links": self._check_links,
            "responsive": self._check_responsive,
            "seo": self._check_seo,
        }
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
            context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="de-DE")
            page = context.new_page()
            try:
                # Login falls konfiguriert
                if self.login_url:
                    self._perform_login(page)

                page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass  # Seiten mit Websockets/Polling werden nie "idle"
                # Warten auf SPA-Hydration (React, Vue, etc.)
                page.wait_for_timeout(3000)

                # Falls kein separater Login-URL aber Credentials vorhanden:
                # prüfe ob auf der Zielseite ein Login-Formular ist
                if not self.login_url and self.username:
                    self._perform_login(page)

                # Screenshot der Startseite
                self._take_screenshot(page, "startseite", "Startseite")

                # Vor-Aktionen ausführen (Formular ausfüllen, Buttons klicken etc.)
                if self.pre_actions:
                    self._execute_pre_actions(page)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    # Screenshot nach Vor-Aktionen
                    self._take_screenshot(page, "nach_aktionen", "Nach Vor-Aktionen")

            except Exception as e:
                self._add("general", "page_load", "failed", "critical",
                          f"Seite konnte nicht geladen werden: {e}")
                self.status = "error"
                browser.close()
                return

            for check_name in self.checks:
                if self._cancel:
                    self.status = "cancelled"
                    break
                fn = dispatch.get(check_name)
                if fn:
                    try:
                        fn(page, context, browser)
                    except Exception as e:
                        self._add(check_name, f"{check_name}_error", "failed", "serious",
                                  f"Fehler bei {check_name}: {e}")

            if self.status == "running":
                self.status = "completed"
            browser.close()

    def cancel(self):
        self._cancel = True

    def _add(self, category: str, name: str, status: str, severity: str, details: str, **extra):
        result = {
            "category": category,
            "name": name,
            "status": status,
            "severity": severity,
            "details": details,
            **extra,
        }
        self.results.append(result)

    # ------------------------------------------------------------------
    # Accessibility
    # ------------------------------------------------------------------
    def _check_accessibility(self, page, context, browser):
        from axe_playwright_python.sync_playwright import Axe
        axe = Axe()
        results = axe.run(page)
        violations = results.response.get("violations", [])

        if not violations:
            self._add("accessibility", "wcag_audit", "passed", "info",
                       "Keine WCAG-Violations gefunden")
            return

        for v in violations:
            impact = v.get("impact", "minor")
            node_count = len(v.get("nodes", []))
            self._add(
                "accessibility",
                v["id"],
                "failed" if impact in ("critical", "serious") else "warning",
                impact,
                f"{v['description']} ({node_count} Element{'e' if node_count != 1 else ''} betroffen)",
                help_url=v.get("helpUrl", ""),
            )

    # ------------------------------------------------------------------
    # Performance
    # ------------------------------------------------------------------
    def _check_performance(self, page, context, browser):
        metrics = page.evaluate("""() => {
            const nav = performance.getEntriesByType('navigation')[0] || {};
            const paint = performance.getEntriesByType('paint');
            const fcp = paint.find(e => e.name === 'first-contentful-paint');
            return {
                ttfb: nav.responseStart ? Math.round(nav.responseStart - nav.requestStart) : null,
                dom_load: nav.domContentLoadedEventEnd ? Math.round(nav.domContentLoadedEventEnd - nav.startTime) : null,
                total_load: nav.loadEventEnd ? Math.round(nav.loadEventEnd - nav.startTime) : null,
                fcp: fcp ? Math.round(fcp.startTime) : null,
                transfer_size: nav.transferSize || null,
            }
        }""")

        # LCP via PerformanceObserver (kurz warten)
        lcp = page.evaluate("""() => new Promise(resolve => {
            let lcp = null;
            const obs = new PerformanceObserver(list => {
                const entries = list.getEntries();
                if (entries.length) lcp = Math.round(entries[entries.length - 1].startTime);
            });
            try { obs.observe({type: 'largest-contentful-paint', buffered: true}); } catch(e) {}
            setTimeout(() => { obs.disconnect(); resolve(lcp); }, 500);
        })""")

        labels = {
            "ttfb": "Time to First Byte",
            "fcp": "First Contentful Paint",
            "lcp": "Largest Contentful Paint",
            "dom_load": "DOM Content Loaded",
            "total_load": "Page Load Complete",
        }
        values = {**metrics, "lcp": lcp}

        for key, label in labels.items():
            val = values.get(key)
            if val is None:
                self._add("performance", key, "warning", "minor", f"{label}: nicht messbar")
                continue
            status = _rate(val, key)
            self._add("performance", key, status, "info" if status == "passed" else "moderate",
                       f"{label}: {val} ms", value_ms=val)

        # Seitengröße
        size = metrics.get("transfer_size")
        if size:
            size_kb = round(size / 1024)
            status = "passed" if size_kb < 2000 else ("warning" if size_kb < 5000 else "failed")
            self._add("performance", "page_size", status, "info",
                       f"Transfer-Größe: {size_kb} KB", value_kb=size_kb)

    # ------------------------------------------------------------------
    # Broken Links
    # ------------------------------------------------------------------
    def _check_links(self, page, context, browser):
        urls = page.evaluate("""() => {
            const links = new Set();
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href;
                if (href && !href.startsWith('javascript:') && !href.startsWith('mailto:') && !href.startsWith('tel:'))
                    links.add(href);
            });
            document.querySelectorAll('img[src]').forEach(img => links.add(img.src));
            return [...links];
        }""")

        if not urls:
            self._add("links", "no_links", "passed", "info", "Keine Links auf der Seite gefunden")
            return

        broken = []
        checked = 0

        def check_url(url):
            try:
                r = requests.head(url, timeout=10, allow_redirects=True,
                                  headers={"User-Agent": "Mozilla/5.0 WebsiteScanner"})
                return url, r.status_code
            except requests.RequestException:
                return url, 0

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {pool.submit(check_url, u): u for u in urls[:100]}  # Max 100 Links
            for future in as_completed(futures):
                if self._cancel:
                    return
                url_checked, status_code = future.result()
                checked += 1
                if status_code >= 400 or status_code == 0:
                    broken.append((url_checked, status_code))

        if broken:
            for url_b, code in broken[:20]:  # Max 20 anzeigen
                label = f"HTTP {code}" if code else "Nicht erreichbar"
                self._add("links", "broken_link", "failed", "serious",
                           f"{label}: {url_b}", url=url_b, status_code=code)
        else:
            self._add("links", "all_links_ok", "passed", "info",
                       f"Alle {checked} Links sind erreichbar")

        self._add("links", "link_summary", "info", "info",
                   f"{checked} Links geprüft, {len(broken)} fehlerhaft",
                   total=checked, broken=len(broken))

    # ------------------------------------------------------------------
    # Responsive
    # ------------------------------------------------------------------
    def _check_responsive(self, page, context, browser):
        scan_dir = SCREENSHOTS_DIR / "website_scan"
        scan_dir.mkdir(parents=True, exist_ok=True)

        ts = int(time.time())
        domain = urlparse(self.url).netloc.replace(".", "_")

        for vp in _VIEWPORTS:
            if self._cancel:
                return
            page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            page.wait_for_timeout(500)

            filename = f"{domain}_{vp['name']}_{ts}.png"
            path = scan_dir / filename
            page.screenshot(path=str(path), full_page=True)

            has_overflow = page.evaluate(
                "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )

            status = "warning" if has_overflow else "passed"
            self._add(
                "responsive", f"viewport_{vp['name']}", status,
                "moderate" if has_overflow else "info",
                f"{vp['name'].capitalize()} ({vp['width']}x{vp['height']})"
                + (" — horizontaler Overflow!" if has_overflow else " — OK"),
                screenshot=f"/static_screenshots/website_scan/{filename}",
                viewport=vp["name"],
            )

        # Viewport zurücksetzen und Seite neu laden für sauberen DOM-State
        page.set_viewport_size({"width": 1440, "height": 900})
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

    # ------------------------------------------------------------------
    # SEO
    # ------------------------------------------------------------------
    def _check_seo(self, page, context, browser):
        # Sicherstellen dass SPA-Frameworks (React etc.) fertig gemountet haben
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)
        seo = page.evaluate("""() => {
            const meta = (name) => {
                const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                return el ? el.content : null;
            };
            const headings = {};
            for (let i = 1; i <= 6; i++) {
                const els = document.querySelectorAll('h' + i);
                if (els.length) headings['h' + i] = els.length;
            }
            const imgs = document.querySelectorAll('img');
            let missingAlt = 0;
            imgs.forEach(img => { if (!img.alt || !img.alt.trim()) missingAlt++; });
            return {
                title: document.title || null,
                titleLength: (document.title || '').length,
                description: meta('description'),
                descLength: (meta('description') || '').length,
                canonical: (document.querySelector('link[rel="canonical"]') || {}).href || null,
                ogTitle: meta('og:title'),
                ogDescription: meta('og:description'),
                ogImage: meta('og:image'),
                headings: headings,
                h1Count: (document.querySelectorAll('h1') || []).length,
                totalImages: imgs.length,
                missingAlt: missingAlt,
                lang: document.documentElement.lang || null,
            };
        }""")

        # Title
        if seo["title"]:
            length = seo["titleLength"]
            if 30 <= length <= 60:
                self._add("seo", "title", "passed", "info", f"Title vorhanden ({length} Zeichen): {seo['title']}")
            else:
                self._add("seo", "title", "warning", "moderate",
                           f"Title-Länge suboptimal ({length} Zeichen, ideal: 30-60): {seo['title']}")
        else:
            self._add("seo", "title", "failed", "serious", "Kein <title> Tag gefunden")

        # Meta Description
        if seo["description"]:
            length = seo["descLength"]
            if 120 <= length <= 160:
                self._add("seo", "meta_description", "passed", "info",
                           f"Meta-Description vorhanden ({length} Zeichen)")
            else:
                self._add("seo", "meta_description", "warning", "moderate",
                           f"Meta-Description Länge suboptimal ({length} Zeichen, ideal: 120-160)")
        else:
            self._add("seo", "meta_description", "failed", "serious", "Keine Meta-Description gefunden")

        # Canonical
        if seo["canonical"]:
            self._add("seo", "canonical", "passed", "info", f"Canonical URL: {seo['canonical']}")
        else:
            self._add("seo", "canonical", "warning", "moderate", "Kein Canonical-Link gefunden")

        # Open Graph
        og_fields = {"og:title": seo["ogTitle"], "og:description": seo["ogDescription"], "og:image": seo["ogImage"]}
        missing_og = [k for k, v in og_fields.items() if not v]
        if not missing_og:
            self._add("seo", "open_graph", "passed", "info", "Alle Open-Graph Tags vorhanden")
        else:
            self._add("seo", "open_graph", "warning", "moderate",
                       f"Fehlende OG-Tags: {', '.join(missing_og)}")

        # Headings
        h1 = seo["h1Count"]
        if h1 == 1:
            self._add("seo", "h1", "passed", "info", "Genau ein H1-Tag vorhanden")
        elif h1 == 0:
            self._add("seo", "h1", "failed", "serious", "Kein H1-Tag gefunden")
        else:
            self._add("seo", "h1", "warning", "moderate", f"{h1} H1-Tags gefunden (ideal: genau 1)")

        if seo["headings"]:
            hierarchy = ", ".join(f"{k.upper()}: {v}" for k, v in sorted(seo["headings"].items()))
            self._add("seo", "heading_structure", "info", "info", f"Heading-Struktur: {hierarchy}")

        # Alt-Texte
        if seo["totalImages"] > 0:
            missing = seo["missingAlt"]
            if missing == 0:
                self._add("seo", "img_alt", "passed", "info",
                           f"Alle {seo['totalImages']} Bilder haben Alt-Texte")
            else:
                self._add("seo", "img_alt", "failed", "serious",
                           f"{missing} von {seo['totalImages']} Bildern ohne Alt-Text")

        # Lang-Attribut
        if seo["lang"]:
            self._add("seo", "lang", "passed", "info", f"Sprach-Attribut gesetzt: {seo['lang']}")
        else:
            self._add("seo", "lang", "warning", "moderate", "Kein lang-Attribut auf <html>")
