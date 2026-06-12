#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable
from urllib.parse import quote


SITE_NAME = "Dan's Place"
TAGLINE = "Simple fixes. Clear answers."
PROJECT_NAME = "dans-place"
BASE_URL = "https://dannynuhi.github.io/dans-place"


SOFTWARE = [
    "Wi-Fi", "Bluetooth", "email", "printer", "browser", "password reset",
    "video call", "camera", "microphone", "keyboard", "touchpad", "cloud sync",
    "file download", "software update", "app install", "backup", "screen sharing",
    "notifications", "calendar sync", "contacts sync", "storage", "battery charging",
    "audio output", "display brightness", "account sign in",
]

DEVICES = [
    "Windows laptop", "Mac", "Chromebook", "iPhone", "iPad", "Android phone",
    "Android tablet", "home router", "smart TV", "wireless printer",
    "Bluetooth headphones", "USB microphone", "webcam", "desktop PC",
    "gaming console", "streaming stick", "smart speaker", "external monitor",
    "USB drive", "SD card", "NAS drive", "work laptop", "school laptop",
    "office printer", "mesh router", "LTE hotspot", "drawing tablet",
    "mechanical keyboard", "wireless mouse", "smartwatch",
]

SYMPTOMS = [
    "is not working", "keeps disconnecting", "runs slowly",
    "shows an error", "will not connect",
]

ES_SOFTWARE = {
    "Wi-Fi": "Wi-Fi",
    "Bluetooth": "Bluetooth",
    "email": "correo electronico",
    "printer": "impresora",
    "browser": "navegador",
    "password reset": "restablecimiento de contrasena",
    "video call": "videollamada",
    "camera": "camara",
    "microphone": "microfono",
    "keyboard": "teclado",
    "touchpad": "panel tactil",
    "cloud sync": "sincronizacion en la nube",
    "file download": "descarga de archivos",
    "software update": "actualizacion de software",
    "app install": "instalacion de aplicaciones",
    "backup": "copia de seguridad",
    "screen sharing": "pantalla compartida",
    "notifications": "notificaciones",
    "calendar sync": "sincronizacion del calendario",
    "contacts sync": "sincronizacion de contactos",
    "storage": "almacenamiento",
    "battery charging": "carga de bateria",
    "audio output": "salida de audio",
    "display brightness": "brillo de pantalla",
    "account sign in": "inicio de sesion",
}

ES_DEVICES = {
    "Windows laptop": "portatil Windows",
    "Mac": "Mac",
    "Chromebook": "Chromebook",
    "iPhone": "iPhone",
    "iPad": "iPad",
    "Android phone": "telefono Android",
    "Android tablet": "tableta Android",
    "home router": "router de casa",
    "smart TV": "televisor inteligente",
    "wireless printer": "impresora inalambrica",
    "Bluetooth headphones": "audifonos Bluetooth",
    "USB microphone": "microfono USB",
    "webcam": "camara web",
    "desktop PC": "computadora de escritorio",
    "gaming console": "consola de videojuegos",
    "streaming stick": "dispositivo de streaming",
    "smart speaker": "altavoz inteligente",
    "external monitor": "monitor externo",
    "USB drive": "unidad USB",
    "SD card": "tarjeta SD",
    "NAS drive": "unidad NAS",
    "work laptop": "portatil de trabajo",
    "school laptop": "portatil escolar",
    "office printer": "impresora de oficina",
    "mesh router": "router de malla",
    "LTE hotspot": "punto de acceso LTE",
    "drawing tablet": "tableta de dibujo",
    "mechanical keyboard": "teclado mecanico",
    "wireless mouse": "raton inalambrico",
    "smartwatch": "reloj inteligente",
}

ES_SYMPTOMS = {
    "is not working": "no funciona",
    "keeps disconnecting": "se desconecta continuamente",
    "runs slowly": "funciona lentamente",
    "shows an error": "muestra un error",
    "will not connect": "no se conecta",
}


@dataclass(frozen=True)
class Topic:
    issue: str
    device: str
    symptom: str
    index: int


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.open_tags: list[str] = []
        self.has_h1 = False
        self.has_list = False
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "h1":
            self.has_h1 = True
        if tag in {"ol", "ul"}:
            self.has_list = True
        if tag not in {"meta", "link", "br", "img", "input", "hr"}:
            self.open_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"meta", "link", "br", "img", "input", "hr"}:
            return
        if not self.open_tags:
            self.errors.append(f"unexpected closing tag: {tag}")
            return
        last = self.open_tags.pop()
        if last != tag:
            self.errors.append(f"tag mismatch: expected {last}, got {tag}")


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as tmp:
        tmp.write(content)
        temp_name = Path(tmp.name)
    temp_name.replace(path)


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def topics() -> Iterable[Topic]:
    index = 0
    for issue in SOFTWARE:
        for device in DEVICES:
            for symptom in SYMPTOMS:
                index += 1
                yield Topic(issue=issue, device=device, symptom=symptom, index=index)


def translated(topic: Topic) -> tuple[str, str, str]:
    return (
        ES_SOFTWARE[topic.issue],
        ES_DEVICES[topic.device],
        ES_SYMPTOMS[topic.symptom],
    )


def page_text(topic: Topic, lang: str) -> dict[str, str | list[str]]:
    if lang == "en":
        title = f"How to fix {topic.issue} when your {topic.device} {topic.symptom}"
        intro = (
            f"If {topic.issue} on your {topic.device} {topic.symptom}, start with the simple checks below. "
            "These steps are calm, reversible, and meant to help you narrow the cause before trying anything advanced."
        )
        steps = [
            f"Confirm the {topic.device} has power, is awake, and is close enough to any needed accessory or network.",
            f"Close the app or settings screen related to {topic.issue}, then open it again and try the same action once.",
            "Turn the affected connection or feature off for ten seconds, then turn it back on.",
            f"Restart the {topic.device}. A clean restart often clears stuck background tasks without changing your files.",
            f"Check for a pending system or app update if {topic.issue} still {topic.symptom}. Install only updates from trusted settings or app stores.",
            "Try one known-good comparison, such as another cable, another network, another account, or another device.",
            "If the problem continues, write down the exact error text and any recent change before asking for support.",
        ]
        note = (
            "Avoid deleting accounts, resetting the whole device, or changing advanced network settings until you have a backup "
            "and a clear reason to do so."
        )
        keywords = [topic.issue, topic.device, topic.symptom, "troubleshooting", "simple fix", SITE_NAME]
        related_heading = "Related fixes"
        related_label = "Related troubleshooting pages"
        alt_label = "ES"
        start_heading = "Start here"
        next_heading = "What to check next"
        next_text = "Move slowly and test after each step. If one change helps, stop there and keep the setup simple."
        safety_heading = "Safety note"
    else:
        issue, device, symptom = translated(topic)
        title = f"Como arreglar {issue} cuando tu {device} {symptom}"
        intro = (
            f"Si {issue} en tu {device} {symptom}, empieza con estas revisiones sencillas. "
            "Los pasos son tranquilos, reversibles y ayudan a encontrar la causa antes de intentar algo avanzado."
        )
        steps = [
            f"Confirma que el {device} tenga energia, este activo y este cerca del accesorio o la red que necesita.",
            f"Cierra la aplicacion o pantalla de ajustes relacionada con {issue}, vuelve a abrirla y prueba una vez mas.",
            "Apaga la conexion o funcion afectada durante diez segundos y luego activala otra vez.",
            f"Reinicia el {device}. Un reinicio limpio suele liberar procesos atascados sin cambiar tus archivos.",
            f"Busca una actualizacion pendiente del sistema o de la aplicacion si {issue} todavia {symptom}. Instala solo desde ajustes o tiendas confiables.",
            "Prueba una comparacion conocida, como otro cable, otra red, otra cuenta u otro dispositivo.",
            "Si el problema continua, anota el texto exacto del error y cualquier cambio reciente antes de pedir soporte.",
        ]
        note = (
            "Evita borrar cuentas, restablecer todo el dispositivo o cambiar ajustes avanzados de red hasta tener una copia "
            "de seguridad y una razon clara."
        )
        keywords = [issue, device, symptom, "solucion de problemas", "arreglo simple", SITE_NAME]
        related_heading = "Soluciones relacionadas"
        related_label = "Paginas relacionadas"
        alt_label = "EN"
        start_heading = "Empieza aqui"
        next_heading = "Que revisar despues"
        next_text = "Avanza con calma y prueba despues de cada paso. Si un cambio ayuda, detenlo ahi y conserva la configuracion simple."
        safety_heading = "Nota de seguridad"
    return {
        "title": title,
        "intro": intro,
        "steps": steps,
        "note": note,
        "keywords": keywords,
        "related_heading": related_heading,
        "related_label": related_label,
        "alt_label": alt_label,
        "start_heading": start_heading,
        "next_heading": next_heading,
        "next_text": next_text,
        "safety_heading": safety_heading,
    }


def article_html(data: dict[str, str | list[str]]) -> str:
    steps = "\n".join(f"        <li>{html.escape(step)}</li>" for step in data["steps"])  # type: ignore[index]
    return f"""<h1>{html.escape(str(data["title"]))}</h1>
      <p>{html.escape(str(data["intro"]))}</p>
      <h2>{html.escape(str(data["start_heading"]))}</h2>
      <ol>
{steps}
      </ol>
      <h2>{html.escape(str(data["next_heading"]))}</h2>
      <p>{html.escape(str(data["next_text"]))}</p>
      <div class="note warning">
        <h3>{html.escape(str(data["safety_heading"]))}</h3>
        <p>{html.escape(str(data["note"]))}</p>
      </div>"""


def related_links(topic: Topic, lang: str) -> str:
    nearby = [
        Topic(topic.issue, topic.device, SYMPTOMS[(SYMPTOMS.index(topic.symptom) + 1) % len(SYMPTOMS)], topic.index),
        Topic(topic.issue, DEVICES[(DEVICES.index(topic.device) + 1) % len(DEVICES)], topic.symptom, topic.index),
        Topic(SOFTWARE[(SOFTWARE.index(topic.issue) + 1) % len(SOFTWARE)], topic.device, topic.symptom, topic.index),
    ]
    links = []
    for item in nearby:
        slug = slug_for(item, lang)
        label = page_text(item, lang)["title"]
        links.append(f'<li><a href="{slug}.html">{html.escape(str(label))}</a></li>')
    return "\n        ".join(links)


def slug_for(topic: Topic, lang: str) -> str:
    return slugify(f"{topic.issue}-{topic.device}-{topic.symptom}")


def validate(rendered: str, lang: str) -> tuple[bool, int, list[str]]:
    reasons: list[str] = []
    parser = StructureParser()
    parser.feed(rendered)
    parser.close()
    text = re.sub(r"<[^>]+>", "", rendered)
    length = len(text.strip())
    if not parser.has_h1:
        reasons.append("missing h1")
    if length <= 300:
        reasons.append("content too short")
    if "{{" in rendered or "}}" in rendered:
        reasons.append("template tag remains")
    if parser.open_tags or parser.errors:
        reasons.append("html structure problem")
    if lang not in {"en", "es"}:
        reasons.append("unsupported language")
    if re.search(r">\s*<", rendered) is None:
        reasons.append("empty or malformed html")
    size_score = min(length / 300, 5)
    score = int(max(1, min(10, round(size_score + (3 if parser.has_h1 else 0) + (2 if parser.has_list else 0)))))
    if score < 6:
        reasons.append("score below acceptance threshold")
    return not reasons, score, reasons


def validate_file(path: Path, lang: str) -> tuple[bool, list[str]]:
    content = path.read_text(encoding="utf-8")
    ok, _score, reasons = validate(content, lang)
    if "<ol>" not in content or "</ol>" not in content:
        reasons.append("missing troubleshooting steps")
    if lang == "en" and '<html lang="en">' not in content:
        reasons.append("wrong page language")
    if lang == "es" and '<html lang="es">' not in content:
        reasons.append("wrong page language")
    if lang == "es" and any(text in content for text in ["Start here", "What to check next", "Safety note"]):
        reasons.append("english labels in spanish page")
    if lang == "en" and any(text in content for text in ["Empieza aqui", "Que revisar despues", "Nota de seguridad"]):
        reasons.append("spanish labels in english page")
    return not reasons, reasons


def local_links(content: str) -> list[str]:
    links = re.findall(r'(?:href|src)="([^"#?]+)', content)
    return [link for link in links if not re.match(r"^[a-z]+:", link) and not link.startswith("//")]


def build_sitemap_from_scan(site_root: Path) -> list[str]:
    pages = sorted(
        path for lang in ("en", "es")
        for path in (site_root / lang).glob("*.html")
    )
    urls = []
    for page in pages:
        rel = page.relative_to(site_root).as_posix()
        urls.append(f"{BASE_URL}/{quote(rel)}")
    today = date.today().isoformat()
    sitemap_items = "\n".join(
        f"  <url><loc>{html.escape(url)}</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>"
        for url in urls
    )
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_items}
</urlset>
"""
    safe_write(site_root / "sitemap.xml", sitemap)
    return urls


def validate_site(site_root: Path, target: int) -> tuple[bool, list[str]]:
    issues: list[str] = []
    en_pages = sorted((site_root / "en").glob("*.html"))
    es_pages = sorted((site_root / "es").glob("*.html"))
    if len(en_pages) != target // 2:
        issues.append(f"english page count is {len(en_pages)}")
    if len(es_pages) != target // 2:
        issues.append(f"spanish page count is {len(es_pages)}")
    if len(en_pages) + len(es_pages) != target:
        issues.append(f"total page count is {len(en_pages) + len(es_pages)}")
    en_slugs = {path.name for path in en_pages}
    es_slugs = {path.name for path in es_pages}
    if en_slugs != es_slugs:
        issues.append("language slug parity mismatch")
    required = [
        site_root / "index.html",
        site_root / "sitemap.xml",
        site_root / "assets/css/site.css",
        site_root / "seo",
    ]
    for path in required:
        if not path.exists():
            issues.append(f"missing {path.relative_to(site_root)}")
    checked_pages = en_pages + es_pages
    for page in checked_pages:
        lang = page.parent.name
        ok, reasons = validate_file(page, lang)
        if not ok:
            issues.append(f"{page.relative_to(site_root)}: {', '.join(reasons)}")
        content = page.read_text(encoding="utf-8")
        for link in local_links(content):
            target_path = (page.parent / link).resolve()
            try:
                target_path.relative_to(site_root.resolve())
            except ValueError:
                issues.append(f"{page.relative_to(site_root)}: link leaves docs: {link}")
                continue
            if not target_path.exists():
                issues.append(f"{page.relative_to(site_root)}: broken link {link}")
    sitemap = site_root / "sitemap.xml"
    if sitemap.exists():
        sitemap_text = sitemap.read_text(encoding="utf-8")
        urls = re.findall(r"<loc>(.*?)</loc>", sitemap_text)
        if len(urls) != target:
            issues.append(f"sitemap url count is {len(urls)}")
        if len(set(urls)) != len(urls):
            issues.append("sitemap has duplicate urls")
        if not all("/en/" in url or "/es/" in url for url in urls):
            issues.append("sitemap has url without language prefix")
    if issues:
        return False, issues[:50]
    return True, []


def render_page(template: str, topic: Topic, lang: str, robots: str) -> tuple[str, dict[str, str | int | list[str]]]:
    data = page_text(topic, lang)
    slug = slug_for(topic, lang)
    alt_lang = "es" if lang == "en" else "en"
    alt_url = f"../{alt_lang}/{slug_for(topic, alt_lang)}.html"
    canonical = f"{BASE_URL}/{quote(lang)}/{quote(slug)}.html"
    meta_title = f"{data['title']} | {SITE_NAME}"
    meta_description = f"{data['intro']} {TAGLINE}"
    replacements = {
        "{{LANG}}": lang,
        "{{ROBOTS}}": robots,
        "{{META_TITLE}}": html.escape(str(meta_title)),
        "{{META_DESCRIPTION}}": html.escape(str(meta_description[:155])),
        "{{KEYWORDS}}": html.escape(", ".join(data["keywords"])),  # type: ignore[arg-type]
        "{{CANONICAL_URL}}": html.escape(canonical),
        "{{ALT_URL}}": html.escape(alt_url),
        "{{ALT_LABEL}}": html.escape(str(data["alt_label"])),
        "{{CONTENT}}": article_html(data),
        "{{RELATED_LABEL}}": html.escape(str(data["related_label"])),
        "{{RELATED_HEADING}}": html.escape(str(data["related_heading"])),
        "{{INTERNAL_LINKS}}": related_links(topic, lang),
    }
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    record = {
        "site": SITE_NAME,
        "project": PROJECT_NAME,
        "tagline": TAGLINE,
        "lang": lang,
        "slug": slug,
        "title": str(data["title"]),
        "meta_title": str(meta_title),
        "meta_description": str(meta_description[:155]),
        "keywords": data["keywords"],
        "canonical_url": canonical,
        "robots": robots,
    }
    return rendered, record


def write_index(site_root: Path) -> None:
    index = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,follow">
  <title>Dan's Place | Simple fixes. Clear answers.</title>
  <meta name="description" content="Dan's Place provides calm troubleshooting pages in English and Spanish.">
  <link rel="stylesheet" href="assets/css/site.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="index.html" aria-label="Dan's Place home">
      <span class="brand-mark">D</span>
      <span><strong>Dan's Place</strong><small>Simple fixes. Clear answers.</small></span>
    </a>
  </header>
  <main class="page-shell">
    <article class="article">
      <h1>Dan's Place</h1>
      <p>Simple fixes. Clear answers.</p>
      <p>This local build contains validated troubleshooting pages in English and Spanish.</p>
      <ul>
        <li><a href="en/wi-fi-windows-laptop-is-not-working.html">Browse English fixes</a></li>
        <li><a href="es/wi-fi-windows-laptop-is-not-working.html">Ver soluciones en espanol</a></li>
      </ul>
    </article>
  </main>
</body>
</html>
"""
    safe_write(site_root / "index.html", index)


def generate(project: Path, target: int) -> int:
    template = (project / "templates/page.html").read_text(encoding="utf-8")
    if target % 2 != 0:
        raise SystemExit("target must be even for bilingual parity")
    staging = project / "deploy_staging"
    docs = project / "docs"
    reset_dir(staging)
    for folder in ["en", "es", "seo", "json/en", "json/es"]:
        (staging / folder).mkdir(parents=True, exist_ok=True)
    shutil.copytree(project / "assets", staging / "assets", dirs_exist_ok=True)

    accepted = 0
    rejected = 0
    report_rows: list[dict[str, str | int | list[str]]] = []
    robots = "noindex,follow"

    for topic in topics():
        for lang in ("en", "es"):
            if accepted >= target:
                break
            rendered, record = render_page(template, topic, lang, robots)
            is_valid, score, reasons = validate(rendered, lang)
            record["score"] = score
            if not is_valid:
                rejected += 1
                record["status"] = "rejected"
                record["reasons"] = reasons
                report_rows.append(record)
                continue
            slug = str(record["slug"])
            safe_write(staging / f"{lang}/{slug}.html", rendered)
            safe_write(staging / f"json/{lang}/{slug}.json", json.dumps(record, indent=2, ensure_ascii=False))
            record["status"] = "accepted"
            report_rows.append(record)
            accepted += 1
        if accepted >= target:
            break

    if accepted != target:
        raise SystemExit(f"accepted {accepted}, expected {target}")

    today = date.today().isoformat()
    urls = build_sitemap_from_scan(staging)

    summary = {
        "site": SITE_NAME,
        "project": PROJECT_NAME,
        "tagline": TAGLINE,
        "target": target,
        "accepted": accepted,
        "rejected": rejected,
        "languages": ["en", "es"],
        "robots": robots,
        "generated_at": today,
        "phase": "Phase 1: generated and validated silently; noindex is active for controlled rollout.",
    }
    safe_write(staging / "seo/summary.json", json.dumps(summary, indent=2))
    safe_write(staging / "seo/validation-report.json", json.dumps(report_rows, indent=2, ensure_ascii=False))
    write_index(staging)
    ok, issues = validate_site(staging, target)
    if not ok:
        safe_write(project / "logs/deployment-failure.json", json.dumps({"issues": issues}, indent=2))
        raise SystemExit("staging validation failed")

    replacement = project / ".docs_next"
    if replacement.exists():
        shutil.rmtree(replacement)
    shutil.copytree(staging, replacement)
    old_docs = project / ".docs_old"
    if old_docs.exists():
        shutil.rmtree(old_docs)
    if docs.exists():
        docs.replace(old_docs)
    replacement.replace(docs)
    if old_docs.exists():
        shutil.rmtree(old_docs)

    ok, issues = validate_site(docs, target)
    if not ok:
        safe_write(project / "logs/deployment-failure.json", json.dumps({"issues": issues}, indent=2))
        raise SystemExit("docs validation failed")
    if sorted(p.relative_to(staging).as_posix() for p in staging.rglob("*") if p.is_file()) != sorted(
        p.relative_to(docs).as_posix() for p in docs.rglob("*") if p.is_file()
    ):
        raise SystemExit("staging and docs file lists differ")
    safe_write(project / "logs/generation.log", json.dumps(summary, indent=2))
    return accepted


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Dan's Place troubleshooting pages.")
    parser.add_argument("--target", type=int, default=7500)
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    if args.target < 1:
        raise SystemExit("target must be positive")
    accepted = generate(args.project.expanduser().resolve(), args.target)
    print(f"accepted={accepted}")


if __name__ == "__main__":
    main()
