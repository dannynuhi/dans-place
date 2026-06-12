#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
BASE_URL = "https://dannynuhi.github.io/dans-place"


@dataclass
class Page:
    lang: str
    path: Path
    title: str
    description: str
    category: str
    article: str
    related: str


def safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as tmp:
        tmp.write(content)
        name = Path(tmp.name)
    name.replace(path)


def text_from_html(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", "", value, flags=re.S | re.I)
    value = re.sub(r"<style\b.*?</style>", "", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def match_one(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.S | re.I)
    return html.unescape(match.group(1)).strip() if match else default


def clean_article(article: str, lang: str) -> str:
    article = article.replace("<h2>Start here</h2>", "<h2>Empieza aqui</h2>") if lang == "es" else article
    article = article.replace("<h2>What to check next</h2>", "<h2>Que revisar despues</h2>") if lang == "es" else article
    article = article.replace("<h3>Safety note</h3>", "<h3>Nota de seguridad</h3>") if lang == "es" else article
    article = article.replace(
        "Move slowly and test after each step. If one change helps, stop there and keep the setup simple.",
        "Avanza con calma y prueba despues de cada paso. Si un cambio ayuda, detenlo ahi y conserva la configuracion simple.",
    ) if lang == "es" else article
    return article


def category_for(title: str, slug: str) -> str:
    blob = f"{title} {slug}".lower()
    if any(token in blob for token in ["wi-fi", "wifi", "network", "router", "bluetooth", "hotspot", "red"]):
        return "network"
    if any(token in blob for token in ["login", "sign in", "password", "account", "contrasena", "sesion", "cuenta"]):
        return "auth"
    if any(token in blob for token in ["browser", "chrome", "navegador"]):
        return "browser"
    if any(token in blob for token in ["windows", "mac", "chromebook", "software update", "os", "actualizacion"]):
        return "os"
    if any(token in blob for token in ["printer", "impresora"]):
        return "printer"
    return "device"


def build_slug_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for en_path in sorted((DOCS / "en").glob("*.html")):
        raw = en_path.read_text(encoding="utf-8")
        alt = match_one(r'<a class="pill" href="(../es/[^"]+)"', raw)
        if not alt:
            alt = match_one(r'<nav[^>]*aria-label="Language"[^>]*>.*?<a href="(../es/[^"]+)"', raw)
        if alt:
            aliases[Path(alt).name] = en_path.name
    return aliases


def mirror_spanish_slugs(aliases: dict[str, str]) -> None:
    es_dir = DOCS / "es"
    temp_dir = DOCS / ".es_mirror_tmp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    en_names = {path.name for path in (DOCS / "en").glob("*.html")}
    moved: set[str] = set()
    for old_name, new_name in aliases.items():
        source = es_dir / old_name
        if not source.exists():
            source = es_dir / new_name
        if source.exists():
            shutil.copy2(source, temp_dir / new_name)
            moved.add(new_name)
    for source in sorted(es_dir.glob("*.html")):
        if source.name in en_names and source.name not in moved:
            shutil.copy2(source, temp_dir / source.name)
            moved.add(source.name)
    if len(moved) != 3750:
        raise SystemExit(f"Spanish mirror count is {len(moved)}, expected 3750")
    for source in es_dir.glob("*.html"):
        source.unlink()
    for source in temp_dir.glob("*.html"):
        source.replace(es_dir / source.name)
    temp_dir.rmdir()


def rewrite_related_hrefs(related: str, aliases: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        name = Path(match.group(1)).name
        return f'href="{aliases.get(name, name)}"'
    return re.sub(r'href="([^"]+)"', repl, related)


def related_from_page(raw: str, aliases: dict[str, str]) -> str:
    related = match_one(r'<aside class="related"[^>]*>.*?<ul>(.*?)</ul>.*?</aside>', raw)
    if not related:
        related = match_one(r'<section class="related-section"[^>]*>.*?<ul>(.*?)</ul>.*?</section>', raw)
    return rewrite_related_hrefs(related or "", aliases)


def scan_pages() -> list[Page]:
    aliases = build_slug_aliases()
    mirror_spanish_slugs(aliases)
    pages: list[Page] = []
    for lang in ("en", "es"):
        for path in sorted((DOCS / lang).glob("*.html")):
            raw = path.read_text(encoding="utf-8")
            title = match_one(r"<h1>(.*?)</h1>", raw) or path.stem.replace("-", " ").title()
            description = match_one(r'<meta name="description" content="(.*?)"', raw)
            article = match_one(r'<article class="[^"]*\barticle\b[^"]*"[^>]*>(.*?)</article>', raw)
            if not article:
                article = f"<h1>{html.escape(title)}</h1><p>{html.escape(description)}</p>"
            article = clean_article(article, lang)
            category = category_for(title, path.stem)
            pages.append(Page(lang, path, title, description, category, article, related_from_page(raw, aliases)))
    return pages


def css() -> str:
    return """:root {
  --ink: #171427;
  --muted: #696579;
  --line: #e8e3ef;
  --surface: #ffffff;
  --surface-soft: #f7f5fa;
  --purple: #6a1b9a;
  --purple-2: #4f46e5;
  --violet: #a78bfa;
  --teal: #0f9f8f;
  --shadow-sm: 0 8px 22px rgba(40, 28, 63, 0.08);
  --shadow-md: 0 18px 42px rgba(54, 37, 87, 0.13);
  --shadow-lg: 0 26px 70px rgba(70, 35, 120, 0.18);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  min-height: 100vh;
  color: var(--ink);
  background: linear-gradient(180deg, #fff 0%, #fbfaff 45%, #fff 100%);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.62;
}
a { color: var(--purple); text-decoration-thickness: 1px; text-underline-offset: 3px; }
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 72px;
  padding: 16px clamp(18px, 4vw, 48px);
  background: rgba(255,255,255,.88);
  border-bottom: 1px solid rgba(232,227,239,.9);
  backdrop-filter: blur(18px);
}
.brand { display: inline-flex; align-items: center; gap: 12px; color: var(--ink); text-decoration: none; font-weight: 760; }
.brand-mark {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: #fff;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--purple), var(--purple-2) 58%, var(--violet));
  box-shadow: 0 12px 30px rgba(106, 27, 154, .26), inset 0 1px 0 rgba(255,255,255,.32);
}
.brand small { display: block; color: var(--muted); font-size: 12px; font-weight: 600; }
.nav-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.pill {
  display: inline-flex;
  align-items: center;
  min-height: 38px;
  padding: 8px 13px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fff;
  color: var(--ink);
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  box-shadow: var(--shadow-sm);
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.pill:hover, .card-link:hover, .result-link:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.hero {
  position: relative;
  overflow: hidden;
  padding: clamp(48px, 9vw, 96px) 20px 36px;
  border-bottom: 1px solid var(--line);
}
.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 50% 0%, rgba(106,27,154,.16), transparent 34%),
    linear-gradient(135deg, rgba(106,27,154,.06), rgba(79,70,229,.05) 44%, rgba(255,255,255,0) 78%);
  pointer-events: none;
}
.hero-inner { position: relative; max-width: 980px; margin: 0 auto; text-align: center; }
.eyebrow {
  display: inline-flex;
  padding: 7px 11px;
  border-radius: 999px;
  color: var(--purple);
  background: rgba(106,27,154,.08);
  font-size: 13px;
  font-weight: 800;
}
h1 { margin: 14px 0 12px; font-size: clamp(38px, 7vw, 72px); line-height: 1.02; letter-spacing: 0; }
.hero p { max-width: 650px; margin: 0 auto 28px; color: var(--muted); font-size: clamp(17px, 2vw, 20px); }
.search-shell {
  max-width: 760px;
  margin: 0 auto;
  padding: 10px;
  border: 1px solid rgba(106,27,154,.18);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(250,248,255,.96));
  box-shadow: var(--shadow-lg), inset 0 1px 0 rgba(255,255,255,.8);
}
.search-row { display: flex; align-items: center; gap: 10px; }
.search-icon { width: 44px; height: 44px; display: grid; place-items: center; color: var(--purple); }
.search-input {
  width: 100%;
  min-height: 54px;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--ink);
  font: inherit;
  font-size: 18px;
}
.search-results { display: grid; gap: 10px; margin-top: 10px; text-align: left; }
.result-link, .browse-item {
  display: block;
  padding: 13px 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  color: var(--ink);
  text-decoration: none;
  transition: transform .18s ease, box-shadow .18s ease;
}
.result-link[aria-selected="true"] { border-color: rgba(106,27,154,.48); box-shadow: var(--shadow-md); }
.result-meta { display: flex; gap: 8px; margin-top: 4px; color: var(--muted); font-size: 13px; }
mark { padding: 0 2px; border-radius: 4px; background: rgba(167,139,250,.3); color: inherit; }
.section { max-width: 1120px; margin: 0 auto; padding: 44px 20px; }
.section-head { display: flex; justify-content: space-between; gap: 16px; align-items: end; margin-bottom: 18px; }
.section h2 { margin: 0; font-size: clamp(24px, 4vw, 34px); line-height: 1.15; }
.section p { color: var(--muted); }
.category-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 16px; }
.card-link {
  min-height: 156px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background:
    linear-gradient(145deg, rgba(255,255,255,.96), rgba(247,245,250,.92)),
    radial-gradient(circle at top right, rgba(106,27,154,.14), transparent 40%);
  color: var(--ink);
  text-decoration: none;
  box-shadow: var(--shadow-sm);
  transition: transform .18s ease, box-shadow .18s ease;
}
.card-icon { display: grid; width: 42px; height: 42px; place-items: center; margin-bottom: 18px; border-radius: 13px; background: linear-gradient(135deg, rgba(106,27,154,.14), rgba(79,70,229,.12)); color: var(--purple); font-weight: 900; }
.card-link strong { display: block; margin-bottom: 6px; font-size: 18px; }
.card-link span { color: var(--muted); font-size: 14px; }
.browse-panel {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: #fff;
  box-shadow: var(--shadow-sm);
}
.browse-toggle {
  width: 100%;
  padding: 18px 20px;
  border: 0;
  border-radius: 20px;
  background: transparent;
  color: var(--ink);
  font: inherit;
  font-weight: 800;
  text-align: left;
  cursor: pointer;
}
.browse-content { display: none; padding: 0 20px 20px; }
.browse-panel[data-open="true"] .browse-content { display: block; }
.browse-controls { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.browse-list { display: grid; gap: 8px; }
.shell { max-width: 1180px; margin: 0 auto; padding: 24px 20px 56px; }
.breadcrumbs { margin: 10px 0 18px; color: var(--muted); font-size: 14px; }
.page-grid { display: grid; grid-template-columns: minmax(0, 1fr) 310px; gap: 24px; align-items: start; }
.article, .side-panel, .related-section {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(255,255,255,.96);
  box-shadow: var(--shadow-sm);
}
.article { padding: clamp(24px, 4vw, 42px); }
.article h1 { font-size: clamp(32px, 5vw, 52px); }
.article h2 { margin-top: 30px; font-size: 24px; }
.article h3 { margin-top: 20px; font-size: 18px; }
.article ol { padding-left: 24px; }
.article li { margin: 9px 0; }
.note { margin-top: 24px; padding: 16px 18px; border-left: 4px solid var(--teal); border-radius: 12px; background: var(--surface-soft); }
.warning { border-left-color: var(--purple); }
.side-panel { position: sticky; top: 92px; padding: 20px; }
.side-panel h2 { margin: 0 0 12px; font-size: 17px; }
.quick-list, .cause-list { padding-left: 20px; color: var(--muted); font-size: 14px; }
.related-section { margin-top: 24px; padding: 24px; }
.related-section ul { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; padding: 0; list-style: none; }
.related-section a { display: block; height: 100%; padding: 14px; border: 1px solid var(--line); border-radius: 14px; background: var(--surface-soft); text-decoration: none; }
.site-footer { max-width: 1120px; margin: 0 auto; padding: 28px 20px 44px; color: var(--muted); border-top: 1px solid var(--line); }
.fade-in { animation: fadeIn .34s ease both; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 860px) {
  .topbar { position: static; align-items: flex-start; flex-direction: column; }
  .category-grid, .page-grid, .related-section ul { grid-template-columns: 1fr; }
  .side-panel { position: static; }
  .search-row { align-items: flex-start; }
  .search-input { font-size: 16px; }
}
"""


def js() -> str:
    return """(() => {
  const state = { index: [], active: -1, browsePage: 0, browseCategory: 'all', lang: localStorage.getItem('dp_lang') || 'all' };
  const maxResults = 50;
  const pageSize = 50;
  const labels = {
    all: 'All languages',
    en: 'English',
    es: 'Espanol'
  };
  const categoryLabels = {
    all: 'All categories',
    network: 'WiFi / Network issues',
    auth: 'Login / Authentication',
    browser: 'Chrome / Browser errors',
    os: 'Windows / OS issues',
    device: 'Device issues',
    printer: 'Printer issues'
  };
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value) => value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char]));
  const normalize = (value) => value.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
  const score = (item, query) => {
    const hay = normalize(`${item.title} ${item.category} ${item.slug}`);
    const q = normalize(query.trim());
    if (!q) return 0;
    if (hay.includes(q)) return 100 - Math.min(hay.indexOf(q), 30);
    let cursor = 0;
    let points = 0;
    for (const ch of q) {
      const found = hay.indexOf(ch, cursor);
      if (found === -1) return 0;
      points += Math.max(1, 12 - (found - cursor));
      cursor = found + 1;
    }
    return points;
  };
  const highlight = (title, query) => {
    const q = query.trim().replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
    if (!q) return escapeHtml(title);
    return escapeHtml(title).replace(new RegExp(`(${q})`, 'ig'), '<mark>$1</mark>');
  };
  const itemUrl = (item) => `${item.lang}/${item.slug}.html`;
  const renderResults = (query) => {
    const box = $('search-results');
    if (!box) return;
    state.active = -1;
    if (!query.trim()) {
      box.innerHTML = '';
      return;
    }
    const results = state.index
      .map((item) => ({ item, points: score(item, query) }))
      .filter((entry) => entry.points > 0 && (state.lang === 'all' || entry.item.lang === state.lang))
      .sort((a, b) => b.points - a.points || a.item.title.localeCompare(b.item.title))
      .slice(0, maxResults);
    box.innerHTML = results.map(({ item }, index) => `
      <a class="result-link fade-in" id="result-${index}" href="${itemUrl(item)}" role="option" aria-selected="false">
        <strong>${highlight(item.title, query)}</strong>
        <span class="result-meta"><span>${labels[item.lang]}</span><span>${categoryLabels[item.category]}</span></span>
      </a>
    `).join('') || '<p>No close matches yet. Try fewer words.</p>';
  };
  const moveActive = (delta) => {
    const options = Array.from(document.querySelectorAll('.result-link'));
    if (!options.length) return;
    state.active = (state.active + delta + options.length) % options.length;
    options.forEach((option, index) => option.setAttribute('aria-selected', String(index === state.active)));
    options[state.active].scrollIntoView({ block: 'nearest' });
  };
  const renderBrowse = () => {
    const list = $('browse-list');
    const count = $('browse-count');
    if (!list) return;
    const filtered = state.index.filter((item) =>
      (state.browseCategory === 'all' || item.category === state.browseCategory) &&
      (state.lang === 'all' || item.lang === state.lang)
    );
    const start = state.browsePage * pageSize;
    const visible = filtered.slice(start, start + pageSize);
    list.innerHTML = visible.map((item) => `
      <a class="browse-item" href="${itemUrl(item)}">
        <strong>${escapeHtml(item.title)}</strong>
        <span class="result-meta"><span>${labels[item.lang]}</span><span>${categoryLabels[item.category]}</span></span>
      </a>
    `).join('');
    if (count) count.textContent = `${filtered.length} fixes, showing ${visible.length}`;
    const prev = $('browse-prev');
    const next = $('browse-next');
    if (prev) prev.disabled = state.browsePage === 0;
    if (next) next.disabled = start + pageSize >= filtered.length;
  };
  const setup = async () => {
    const response = await fetch('assets/search-index.json');
    state.index = await response.json();
    const input = $('help-search');
    const lang = $('language-filter');
    const category = $('browse-category');
    if (lang) {
      lang.value = state.lang;
      lang.addEventListener('change', () => {
        state.lang = lang.value;
        localStorage.setItem('dp_lang', state.lang);
        renderResults(input ? input.value : '');
        renderBrowse();
      });
    }
    if (input) {
      let timer = 0;
      input.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(() => renderResults(input.value), 110);
      });
      input.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowDown') { event.preventDefault(); moveActive(1); }
        if (event.key === 'ArrowUp') { event.preventDefault(); moveActive(-1); }
        if (event.key === 'Enter' && state.active >= 0) {
          const selected = document.getElementById(`result-${state.active}`);
          if (selected) selected.click();
        }
      });
      input.focus({ preventScroll: true });
    }
    document.querySelectorAll('[data-category]').forEach((link) => {
      link.addEventListener('click', () => {
        state.browseCategory = link.getAttribute('data-category') || 'all';
        state.browsePage = 0;
        const panel = $('browse-panel');
        if (panel) panel.dataset.open = 'true';
        if (category) category.value = state.browseCategory;
        renderBrowse();
      });
    });
    const toggle = $('browse-toggle');
    if (toggle) toggle.addEventListener('click', () => {
      const panel = $('browse-panel');
      if (panel) panel.dataset.open = panel.dataset.open === 'true' ? 'false' : 'true';
      renderBrowse();
    });
    if (category) category.addEventListener('change', () => {
      state.browseCategory = category.value;
      state.browsePage = 0;
      renderBrowse();
    });
    const prev = $('browse-prev');
    const next = $('browse-next');
    if (prev) prev.addEventListener('click', () => { state.browsePage = Math.max(0, state.browsePage - 1); renderBrowse(); });
    if (next) next.addEventListener('click', () => { state.browsePage += 1; renderBrowse(); });
    renderBrowse();
  };
  setup().catch(() => {
    const box = $('search-results');
    if (box) box.innerHTML = '<p>Search is not available right now. Browse by category below.</p>';
  });
})();
"""


def common_causes(page: Page) -> list[str]:
    if page.lang == "es":
        return ["Ajuste desactivado por accidente", "Conexion o sesion atascada", "Actualizacion pendiente"]
    return ["A setting was turned off by accident", "A connection or session is stuck", "A pending update needs attention"]


def quick_steps(article: str) -> list[str]:
    steps = re.findall(r"<li>(.*?)</li>", article, flags=re.S | re.I)
    return [text_from_html(step) for step in steps[:4]]


def page_shell(page: Page) -> str:
    rel = f"{page.lang}/{page.path.name}"
    canonical = f"{BASE_URL}/{rel}"
    desc = page.description or text_from_html(page.article)[:150]
    lang_label = "ES" if page.lang == "en" else "EN"
    alt_lang = "es" if page.lang == "en" else "en"
    alt = f"../{alt_lang}/{page.path.name}"
    crumb_label = "Fixes" if page.lang == "en" else "Soluciones"
    causes = "".join(f"<li>{html.escape(item)}</li>" for item in common_causes(page))
    quick = "".join(f"<li>{html.escape(item)}</li>" for item in quick_steps(page.article))
    related = page.related or ""
    related_block = f"""
    <section class="related-section" aria-label="Related fixes">
      <h2>{'Related fixes' if page.lang == 'en' else 'Soluciones relacionadas'}</h2>
      <ul>{related}</ul>
    </section>""" if related else ""
    return f"""<!doctype html>
<html lang="{page.lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,follow">
  <title>{html.escape(page.title)} | Dan's Place</title>
  <meta name="description" content="{html.escape(desc[:155])}">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="../assets/css/site.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="../index.html" aria-label="Dan's Place home">
      <span class="brand-mark">D</span>
      <span><strong>Dan's Place</strong><small>Simple fixes. Clear answers.</small></span>
    </a>
    <nav class="nav-actions" aria-label="Primary">
      <a class="pill" href="../index.html#search">Search</a>
      <a class="pill" href="../index.html#categories">Categories</a>
      <a class="pill" href="{html.escape(alt)}">{lang_label}</a>
    </nav>
  </header>
  <main class="shell">
    <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../index.html">Dan's Place</a> / <span>{crumb_label}</span> / <span>{html.escape(page.title)}</span></nav>
    <div class="page-grid">
      <article class="article fade-in">{page.article}</article>
      <aside class="side-panel" aria-label="Fast help">
        <h2>{'Quick fix steps' if page.lang == 'en' else 'Pasos rapidos'}</h2>
        <ol class="quick-list">{quick}</ol>
        <h2>{'Common causes' if page.lang == 'en' else 'Causas comunes'}</h2>
        <ul class="cause-list">{causes}</ul>
      </aside>
    </div>
{related_block}
  </main>
  <footer class="site-footer">Dan's Place keeps troubleshooting calm, practical, and easy to scan.</footer>
</body>
</html>
"""


def homepage(pages: list[Page]) -> str:
    counts = {cat: sum(1 for p in pages if p.category == cat) for cat in ["network", "auth", "browser", "os", "device", "printer"]}
    cards = [
        ("network", "WiFi / Network issues", "Connection drops, router trouble, Bluetooth pairing", "Wi"),
        ("auth", "Login / Authentication", "Passwords, sign-in loops, account access", "Li"),
        ("browser", "Chrome / Browser errors", "Browser crashes, tabs, downloads, page errors", "Br"),
        ("os", "Windows / OS issues", "Updates, settings, system behavior", "OS"),
        ("device", "Device issues", "Cameras, audio, storage, keyboards, screens", "Dv"),
        ("printer", "Printer issues", "Wireless printers, office printers, print errors", "Pr"),
    ]
    card_html = "\n".join(
        f"""<a class="card-link" href="#browse" data-category="{key}">
          <span class="card-icon">{icon}</span>
          <strong>{label}</strong>
          <span>{desc}. {counts.get(key, 0)} fixes.</span>
        </a>"""
        for key, label, desc, icon in cards
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,follow">
  <title>Dan's Place | Simple fixes. Clear answers.</title>
  <meta name="description" content="Search calm troubleshooting guides in English and Spanish.">
  <link rel="stylesheet" href="assets/css/site.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="index.html" aria-label="Dan's Place home">
      <span class="brand-mark">D</span>
      <span><strong>Dan's Place</strong><small>Simple fixes. Clear answers.</small></span>
    </a>
    <nav class="nav-actions" aria-label="Primary">
      <a class="pill" href="#search">Search</a>
      <a class="pill" href="#categories">Categories</a>
      <a class="pill" href="#browse">Browse</a>
    </nav>
  </header>
  <main>
    <section class="hero" id="search">
      <div class="hero-inner">
        <span class="eyebrow">Troubleshooting help center</span>
        <h1>Dan's Place</h1>
        <p>Calm troubleshooting assistant for software and device problems. Search first, choose a category second, browse only when you want to explore.</p>
        <div class="search-shell" role="search">
          <div class="search-row">
            <span class="search-icon" aria-hidden="true">S</span>
            <input id="help-search" class="search-input" type="search" autocomplete="off" placeholder="Search Wi-Fi, login, printer, Windows, browser..." aria-label="Search all fixes">
            <select id="language-filter" class="pill" aria-label="Language filter">
              <option value="all">All</option>
              <option value="en">EN</option>
              <option value="es">ES</option>
            </select>
          </div>
          <div id="search-results" class="search-results" role="listbox" aria-label="Search results"></div>
        </div>
      </div>
    </section>
    <section class="section" id="categories">
      <div class="section-head">
        <div>
          <h2>Start with the kind of problem</h2>
          <p>Shortcuts keep the path simple when you already know what feels broken.</p>
        </div>
      </div>
      <div class="category-grid">{card_html}</div>
    </section>
    <section class="section" id="browse">
      <div class="browse-panel" id="browse-panel" data-open="false">
        <button class="browse-toggle" id="browse-toggle" type="button">Browse the full index without loading everything at once</button>
        <div class="browse-content">
          <div class="browse-controls">
            <select class="pill" id="browse-category" aria-label="Browse category">
              <option value="all">All categories</option>
              <option value="network">WiFi / Network issues</option>
              <option value="auth">Login / Authentication</option>
              <option value="browser">Chrome / Browser errors</option>
              <option value="os">Windows / OS issues</option>
              <option value="device">Device issues</option>
              <option value="printer">Printer issues</option>
            </select>
            <button class="pill" id="browse-prev" type="button">Previous</button>
            <button class="pill" id="browse-next" type="button">Next</button>
            <span class="pill" id="browse-count">{len(pages)} fixes</span>
          </div>
          <div id="browse-list" class="browse-list" aria-live="polite"></div>
        </div>
      </div>
    </section>
  </main>
  <footer class="site-footer">Dan's Place is built for fast answers, clear steps, and low-stress troubleshooting.</footer>
  <script src="assets/js/help-center.js" defer></script>
</body>
</html>
"""


def write_sitemap(pages: list[Page]) -> None:
    urls = [
        f"{BASE_URL}/{page.lang}/{page.path.name}"
        for page in sorted(pages, key=lambda item: (item.lang, item.path.name))
    ]
    body = "\n".join(
        f"  <url><loc>{html.escape(url)}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>"
        for url in urls
    )
    safe_write(DOCS / "sitemap.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
""")


def write_seo_summary(pages: list[Page]) -> None:
    counts: dict[str, int] = {}
    for page in pages:
        counts[page.category] = counts.get(page.category, 0) + 1
    safe_write(DOCS / "seo/summary.json", json.dumps({
        "site": "Dan's Place",
        "pages": len(pages),
        "languages": {
            "en": sum(1 for page in pages if page.lang == "en"),
            "es": sum(1 for page in pages if page.lang == "es"),
        },
        "categories": counts,
        "source": "/docs",
    }, indent=2, ensure_ascii=False))


def main() -> None:
    pages = scan_pages()
    index = [
        {
            "title": page.title,
            "slug": page.path.stem,
            "category": page.category,
            "lang": page.lang,
        }
        for page in pages
    ]
    safe_write(DOCS / "assets/css/site.css", css())
    safe_write(DOCS / "assets/js/help-center.js", js())
    safe_write(DOCS / "assets/search-index.json", json.dumps(index, ensure_ascii=False, separators=(",", ":")))
    safe_write(DOCS / "index.html", homepage(pages))
    for page in pages:
        safe_write(page.path, page_shell(page))
    write_sitemap(pages)
    write_seo_summary(pages)
    staging = PROJECT / "deploy_staging"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DOCS, staging)
    print(f"upgraded_pages={len(pages)}")


if __name__ == "__main__":
    main()
