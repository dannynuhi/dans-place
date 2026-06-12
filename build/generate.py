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
BASE_URL = "https://example.com"


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
        alt_label = "Espanol"
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
        alt_label = "English"
    return {
        "title": title,
        "intro": intro,
        "steps": steps,
        "note": note,
        "keywords": keywords,
        "related_heading": related_heading,
        "related_label": related_label,
        "alt_label": alt_label,
    }


def article_html(data: dict[str, str | list[str]]) -> str:
    steps = "\n".join(f"        <li>{html.escape(step)}</li>" for step in data["steps"])  # type: ignore[index]
    return f"""<h1>{html.escape(str(data["title"]))}</h1>
      <p>{html.escape(str(data["intro"]))}</p>
      <h2>Start here</h2>
      <ol>
{steps}
      </ol>
      <h2>What to check next</h2>
      <p>Move slowly and test after each step. If one change helps, stop there and keep the setup simple.</p>
      <div class="note warning">
        <h3>Safety note</h3>
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
    if lang == "en":
        return slugify(f"{topic.issue}-{topic.device}-{topic.symptom}")
    issue, device, symptom = translated(topic)
    return slugify(f"{issue}-{device}-{symptom}")


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


def write_index(project: Path) -> None:
    index = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,follow">
  <title>Dan's Place | Simple fixes. Clear answers.</title>
  <meta name="description" content="Dan's Place provides calm troubleshooting pages in English and Spanish.">
  <link rel="stylesheet" href="/assets/css/site.css">
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
        <li><a href="es/wi-fi-portatil-windows-no-funciona.html">Ver soluciones en espanol</a></li>
      </ul>
    </article>
  </main>
</body>
</html>
"""
    safe_write(project / "generated/html/index.html", index)


def generate(project: Path, target: int) -> int:
    template = (project / "templates/page.html").read_text(encoding="utf-8")
    for folder in ["generated/html/en", "generated/html/es", "generated/json/en", "generated/json/es", "content/en", "content/es"]:
        path = project / folder
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    accepted = 0
    rejected = 0
    urls: list[str] = []
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
            safe_write(project / f"generated/html/{lang}/{slug}.html", rendered)
            safe_write(project / f"generated/json/{lang}/{slug}.json", json.dumps(record, indent=2, ensure_ascii=False))
            safe_write(
                project / f"content/{lang}/{slug}.md",
                f"# {record['title']}\n\n{page_text(topic, lang)['intro']}\n",
            )
            urls.append(str(record["canonical_url"]))
            record["status"] = "accepted"
            report_rows.append(record)
            accepted += 1
        if accepted >= target:
            break

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
    safe_write(project / "seo/sitemaps/sitemap.xml", sitemap)
    safe_write(project / "generated/xml/sitemap.xml", sitemap)

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
    safe_write(project / "seo/reports/summary.json", json.dumps(summary, indent=2))
    safe_write(project / "validation/report.json", json.dumps(report_rows, indent=2, ensure_ascii=False))
    safe_write(project / "logs/generation.log", json.dumps(summary, indent=2))
    write_index(project)
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
