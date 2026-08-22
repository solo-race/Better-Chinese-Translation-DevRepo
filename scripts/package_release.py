#!/usr/bin/env python3
"""Package the release submodule into a distributable zip file."""

from __future__ import annotations

import sys
import zipfile
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = REPO_ROOT / "release"
OUTPUT_DIR = REPO_ROOT / "scripts/reports"
OUTPUT_ZIP = OUTPUT_DIR / "BetterChineseTrans.zip"

RELEASE_SOURCE_TOP_LEVEL = (
    "content",
    "text",
    "illustrations",
    "plugins",
    "modinfo.json",
    "workshopdata.json",
    "thumbnail.png",
)


def collect_release_files() -> list[Path]:
    files: list[Path] = []
    for name in RELEASE_SOURCE_TOP_LEVEL:
        path = RELEASE_DIR / name
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.is_file()))
        elif path.is_file():
            files.append(path)
    return files


def build_zip() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in collect_release_files():
            arcname = Path("BetterChineseTrans") / path.relative_to(RELEASE_DIR)
            zf.write(path, arcname)
    return OUTPUT_ZIP


def main(argv: Sequence[str] | None = None) -> int:
    if not RELEASE_DIR.is_dir():
        print(f"[ERROR] release submodule not found: {RELEASE_DIR}", file=sys.stderr)
        return 2
    try:
        output = build_zip()
    except (OSError, RuntimeError) as error:
        print(f"[ERROR] failed to package release: {error}", file=sys.stderr)
        return 2
    print(f"Packaged {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
