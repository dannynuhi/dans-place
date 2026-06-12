#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "docs"
TARGET = 7500


def local_links(content: str) -> list[str]:
    links = re.findall(r'(?:href|src)="([^"#?]+)', content)
    return [link for link in links if not re.match(r"^[a-z]+:", link) and not link.startswith("//")]


def main() -> int:
    issues: list[str] = []
    en = sorted((ROOT / "en").glob("*.html"))
    es = sorted((ROOT / "es").glob("*.html"))
    if len(en) != 3750:
        issues.append(f"EN count is {len(en)}")
    if len(es) != 3750:
        issues.append(f"ES count is {len(es)}")
    if len(en) + len(es) != TARGET:
        issues.append(f"total page count is {len(en) + len(es)}")
    if {p.name for p in en} != {p.name for p in es}:
        issues.append("EN/ES slug parity mismatch")
    for required in [ROOT / "index.html", ROOT / "sitemap.xml", ROOT / "assets/css/site.css", ROOT / "seo"]:
        if not required.exists():
            issues.append(f"missing {required.relative_to(ROOT)}")
    for page in en + es:
        text = page.read_text(encoding="utf-8")
        if "<h1>" not in text:
            issues.append(f"{page.relative_to(ROOT)} missing h1")
        if "<ol>" not in text:
            issues.append(f"{page.relative_to(ROOT)} missing troubleshooting steps")
        if "{{" in text or "}}" in text:
            issues.append(f"{page.relative_to(ROOT)} has template placeholder")
        for link in local_links(text):
            target = (page.parent / link).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                issues.append(f"{page.relative_to(ROOT)} link leaves docs: {link}")
                continue
            if not target.exists():
                issues.append(f"{page.relative_to(ROOT)} broken link: {link}")
    sitemap = ROOT / "sitemap.xml"
    if sitemap.exists():
        urls = re.findall(r"<loc>(.*?)</loc>", sitemap.read_text(encoding="utf-8"))
        if len(urls) != TARGET:
            issues.append(f"sitemap URL count is {len(urls)}")
        if len(set(urls)) != len(urls):
            issues.append("sitemap has duplicates")
        if not all("/en/" in url or "/es/" in url for url in urls):
            issues.append("sitemap URL missing language prefix")
    if issues:
        print("\n".join(issues[:100]))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
