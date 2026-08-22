#!/usr/bin/env python3
"""Sync approved Dev translations and dating-sim source into release submodule."""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_TEXT_DIR = REPO_ROOT / "Dev/Dev-texts/text_chi"
DATING_SIM_DIR = REPO_ROOT / "Dev/Raw-texts/moreslugcats texts/dating sim"
RELEASE_TEXT_DIR = REPO_ROOT / "release/text/text_chi"
RELEASE_CONTENT_DIR = REPO_ROOT / "release/content/text_chi"

# Release-only artifacts that should never be removed by sync.
RELEASE_ONLY_SET = frozenset({})


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_text_files(root: Path) -> dict[str, Path]:
    return {
        path.name: path
        for path in root.glob("*.txt")
        if path.is_file()
    }


def sync_directory(dev_dir: Path, release_dir: Path) -> tuple[list[str], list[str], list[str]]:
    dev_files = collect_text_files(dev_dir)
    release_files = collect_text_files(release_dir)
    missing_in_release = sorted(set(dev_files) - set(release_files))
    extra_in_release = sorted(set(release_files) - set(dev_files))
    changed_files: list[str] = []

    release_dir.mkdir(parents=True, exist_ok=True)
    for name in sorted(dev_files):
        source = dev_files[name]
        target = release_dir / name
        if not target.exists() or sha256_bytes(source.read_bytes()) != sha256_bytes(
            target.read_bytes()
        ):
            target.write_bytes(source.read_bytes())
            changed_files.append(name)

    extra = [
        name for name in extra_in_release if name not in RELEASE_ONLY_SET
    ]
    return changed_files, missing_in_release, extra


def main(argv: Sequence[str] | None = None) -> int:
    if not DEV_TEXT_DIR.is_dir():
        print(f"[ERROR] Dev text directory not found: {DEV_TEXT_DIR}", file=sys.stderr)
        return 2
    if not DATING_SIM_DIR.is_dir():
        print(f"[ERROR] dating-sim directory not found: {DATING_SIM_DIR}", file=sys.stderr)
        return 2
    if not (REPO_ROOT / "release" / ".git").exists():
        print("[ERROR] release submodule is not initialized", file=sys.stderr)
        return 2

    text_changed, text_missing, text_extra = sync_directory(
        DEV_TEXT_DIR, RELEASE_TEXT_DIR
    )
    content_changed, content_missing, content_extra = sync_directory(
        DATING_SIM_DIR, RELEASE_CONTENT_DIR
    )

    total_changed = len(text_changed) + len(content_changed)
    print("Release sync summary")
    print(f"  Dev text files: {len(collect_text_files(DEV_TEXT_DIR))}")
    print(f"  Dating-sim files: {len(collect_text_files(DATING_SIM_DIR))}")
    print(f"  Release text files: {len(collect_text_files(RELEASE_TEXT_DIR))}")
    print(f"  Release content files: {len(collect_text_files(RELEASE_CONTENT_DIR))}")
    print(f"  Changed text files: {len(text_changed)}")
    print(f"  Changed content files: {len(content_changed)}")
    print(f"  Missing in release (text): {len(text_missing)}")
    print(f"  Missing in release (content): {len(content_missing)}")
    print(f"  Extra in release (text): {len(text_extra)}")
    print(f"  Extra in release (content): {len(content_extra)}")

    if text_missing or content_missing:
        for name in text_missing:
            print(f"[WARN] missing in release text: {name}", file=sys.stderr)
        for name in content_missing:
            print(f"[WARN] missing in release content: {name}", file=sys.stderr)
        return 1

    if text_extra or content_extra:
        for name in text_extra:
            print(f"[WARN] extra in release text: {name}", file=sys.stderr)
        for name in content_extra:
            print(f"[WARN] extra in release content: {name}", file=sys.stderr)
        return 1

    if total_changed:
        print(f"Synced {total_changed} files.")
    else:
        print("No files changed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
