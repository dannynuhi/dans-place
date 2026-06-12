#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
GENERATED = PROJECT / "generated/html"


def normalized(text: str) -> str:
    return text.replace("/dans-place/", "./")


def html_files(root: Path, lang: str) -> list[Path]:
    return sorted((root / lang).glob("*.html"))


def main() -> int:
    issues: list[str] = []
    if not GENERATED.exists():
        issues.append("missing generated/html")
    for required in [DOCS / "index.html", DOCS / "en", DOCS / "es"]:
        if not required.exists():
            issues.append(f"missing {required.relative_to(PROJECT)}")
    if issues:
        print("\n".join(issues))
        return 1

    for lang in ("en", "es"):
        generated_pages = html_files(GENERATED, lang)
        docs_pages = html_files(DOCS, lang)
        generated_names = {path.name for path in generated_pages}
        docs_names = {path.name for path in docs_pages}
        if len(generated_pages) != len(docs_pages):
            issues.append(f"{lang} count mismatch: generated={len(generated_pages)} docs={len(docs_pages)}")
        if generated_names != docs_names:
            issues.append(f"{lang} filename mirror mismatch")
        for source in generated_pages:
            target = DOCS / lang / source.name
            if not target.exists():
                continue
            source_text = normalized(source.read_text(encoding="utf-8"))
            target_text = target.read_text(encoding="utf-8")
            if source_text != target_text:
                issues.append(f"{target.relative_to(PROJECT)} differs from generated/html mirror")
            if "<h1>" not in target_text:
                issues.append(f"{target.relative_to(PROJECT)} missing h1")
            if "{{" in target_text or "}}" in target_text:
                issues.append(f"{target.relative_to(PROJECT)} has template placeholder")

    source_index = GENERATED / "index.html"
    docs_index = DOCS / "index.html"
    if source_index.exists():
        if normalized(source_index.read_text(encoding="utf-8")) != docs_index.read_text(encoding="utf-8"):
            issues.append("docs/index.html differs from generated/html/index.html mirror")
    else:
        if "<h1>Missing Index</h1>" not in docs_index.read_text(encoding="utf-8"):
            issues.append("docs/index.html fallback marker missing")

    if issues:
        print("\n".join(issues[:100]))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
