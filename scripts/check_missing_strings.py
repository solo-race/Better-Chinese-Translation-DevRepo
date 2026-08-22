#!/usr/bin/env python3
"""Report official localization tags that are absent from the dev strings file."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_FILES = (
    "Dev/Raw-texts/base-game-text/text/text_chi/strings.txt",
    "Dev/Raw-texts/expedition/strings_CN.txt",
    "Dev/Raw-texts/jolly coop/strings_CN.txt",
    "Dev/Raw-texts/moreslugcats texts/text_chi/strings.txt",
    "Dev/Raw-texts/watcher/text_chi/strings.txt",
)
DEV_FILE = "Dev/Dev-texts/text_chi/strings.txt"
DEFAULT_OUT = "scripts/reports/missing_strings_report.txt"


EntryMap = dict[str, str]
WarningList = list[tuple[int, str]]


def parse_entries(path: Path) -> tuple[EntryMap, WarningList]:
    """Parse TAG|value lines, retaining the first value for each tag."""
    entries: EntryMap = {}
    warnings: WarningList = []

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        if "|" not in raw_line:
            warnings.append((line_number, raw_line))
            continue
        tag, value = raw_line.split("|", 1)
        if tag not in entries:
            entries[tag] = value

    return entries, warnings


def resolve_repo_path(raw_path: str | Path) -> Path:
    """Resolve relative CLI/default paths from the repository root."""
    path = Path(raw_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def display_path(path: Path) -> str:
    """Use a repository-relative POSIX path when possible."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_official() -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Load official entries and report differing cross-file duplicates."""
    official: dict[str, tuple[str, str]] = {}
    duplicate_messages: list[str] = []

    for relative_path in OFFICIAL_FILES:
        path = resolve_repo_path(relative_path)
        entries, warnings = parse_entries(path)
        for line_number, raw_line in warnings:
            print(
                f"[WARN] {relative_path}:{line_number}: "
                f"unparseable non-empty line: {raw_line!r}",
                file=sys.stderr,
            )

        for tag, value in entries.items():
            if tag not in official:
                official[tag] = (value, relative_path)
                continue
            first_value, first_source = official[tag]
            if value != first_value:
                duplicate_messages.append(
                    f"[INFO] tag {tag} also in {relative_path} "
                    f"(value kept from {first_source})"
                )

    return official, duplicate_messages


def deterministic_timestamp(paths: Sequence[Path]) -> str:
    """Return a stable UTC timestamp derived from the current input snapshot."""
    newest_mtime = max(path.stat().st_mtime for path in paths)
    return (
        datetime.fromtimestamp(newest_mtime, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def build_report(
    official: dict[str, tuple[str, str]],
    dev: EntryMap,
    missing: list[str],
    dev_path: Path,
) -> str:
    """Build the deterministic human-readable report."""
    input_paths = [resolve_repo_path(path) for path in OFFICIAL_FILES]
    input_paths.append(dev_path)
    missing_lines: list[str] = []
    for tag in missing:
        value, source = official[tag]
        missing_lines.extend(
            (
                f"[MISSING] {tag}",
                f"    official value : {value}",
                f"    source         : {source}",
                "",
            )
        )

    dev_only_count = len(set(dev) - set(official))
    lines = [
        f"Official tags: {len(official)} | Dev tags: {len(dev)} | "
        f"Missing: {len(missing)}",
        f"Generated: {deterministic_timestamp(input_paths)}",
        "Input files:",
    ]
    lines.extend(f"  official: {path}" for path in OFFICIAL_FILES)
    lines.append(f"  dev: {display_path(dev_path)}")
    lines.append("")
    lines.extend(missing_lines)
    lines.extend(
        (
            f"[INFO] Dev has {dev_only_count} tags not present in official sources "
            "(not flagged by this check)",
            f"Missing: {len(missing)} / Official: {len(official)} / "
            f"Dev: {len(dev)}",
        )
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find official localization tags missing from the dev strings file."
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        default=DEFAULT_OUT,
        help=f"report path (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--dev",
        metavar="PATH",
        default=DEV_FILE,
        help=f"dev strings path (default: {DEV_FILE})",
    )
    parser.add_argument(
        "--no-file",
        action="store_true",
        help="print the report without writing an output file",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dev_path = resolve_repo_path(args.dev)

    try:
        official, duplicate_messages = load_official()
        dev, warnings = parse_entries(dev_path)
    except (OSError, UnicodeError) as error:
        print(f"[ERROR] could not read strings file: {error}", file=sys.stderr)
        return 2

    for line_number, raw_line in warnings:
        print(
            f"[WARN] {display_path(dev_path)}:{line_number}: "
            f"unparseable non-empty line: {raw_line!r}",
            file=sys.stderr,
        )
    for message in duplicate_messages:
        print(message, file=sys.stderr)

    missing = sorted(tag for tag in official if tag not in dev)
    try:
        report = build_report(official, dev, missing, dev_path)
    except (OSError, ValueError) as error:
        print(f"[ERROR] could not build report: {error}", file=sys.stderr)
        return 2

    if not args.no_file:
        output_path = resolve_repo_path(args.out)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
        except OSError as error:
            print(f"[ERROR] could not write report {output_path}: {error}", file=sys.stderr)
            return 2

    sys.stdout.write(report)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
