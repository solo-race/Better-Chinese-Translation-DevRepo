#!/usr/bin/env python3
"""Compare official English and Chinese strings.txt tag tables."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = "scripts/reports/official_strings_comparison.txt"
STRING_SOURCES = (
    (
        "base-game-text",
        "Dev/Raw-texts/base-game-text/text/text_eng/strings.txt",
        "Dev/Raw-texts/base-game-text/text/text_chi/strings.txt",
    ),
    (
        "expedition",
        "Dev/Raw-texts/expedition/strings.txt",
        "Dev/Raw-texts/expedition/strings_CN.txt",
    ),
    (
        "jolly coop",
        "Dev/Raw-texts/jolly coop/strings.txt",
        "Dev/Raw-texts/jolly coop/strings_CN.txt",
    ),
    (
        "moreslugcats texts",
        "Dev/Raw-texts/moreslugcats texts/text_eng/strings.txt",
        "Dev/Raw-texts/moreslugcats texts/text_chi/strings.txt",
    ),
    (
        "watcher",
        "Dev/Raw-texts/watcher/text_eng/strings.txt",
        "Dev/Raw-texts/watcher/text_chi/strings.txt",
    ),
)

Entry = tuple[str, int]


@dataclass
class ParsedStrings:
    entries: dict[str, Entry]
    warnings: list[tuple[int, str]]
    duplicates: list[tuple[str, int, str]]


@dataclass
class Comparison:
    label: str
    english_path: Path
    chinese_path: Path
    english: dict[str, Entry]
    chinese: dict[str, Entry]
    english_only: list[str]
    chinese_only: list[str]
    changed: list[str]
    unchanged: list[str]


def resolve_repo_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def parse_entries(path: Path) -> ParsedStrings:
    entries: dict[str, Entry] = {}
    warnings: list[tuple[int, str]] = []
    duplicates: list[tuple[str, int, str]] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        if "|" not in raw_line:
            warnings.append((line_number, raw_line))
            continue
        tag, value = raw_line.split("|", 1)
        if tag in entries:
            duplicates.append((tag, line_number, raw_line))
            continue
        entries[tag] = (value, line_number)
    return ParsedStrings(entries, warnings, duplicates)


def compare_source(
    label: str, english_path: Path, chinese_path: Path
) -> Comparison:
    english = parse_entries(english_path)
    chinese = parse_entries(chinese_path)
    english_tags = set(english.entries)
    chinese_tags = set(chinese.entries)
    common = english_tags & chinese_tags
    changed = sorted(
        tag
        for tag in common
        if english.entries[tag][0] != chinese.entries[tag][0]
    )
    unchanged = sorted(
        tag
        for tag in common
        if english.entries[tag][0] == chinese.entries[tag][0]
    )
    return Comparison(
        label=label,
        english_path=english_path,
        chinese_path=chinese_path,
        english=english.entries,
        chinese=chinese.entries,
        english_only=sorted(english_tags - chinese_tags),
        chinese_only=sorted(chinese_tags - english_tags),
        changed=changed,
        unchanged=unchanged,
    )


def print_parse_diagnostics(path: Path, parsed: ParsedStrings) -> None:
    for line_number, raw_line in parsed.warnings:
        print(
            f"[WARN] {display_path(path)}:{line_number}: "
            f"unparseable non-empty line: {raw_line!r}",
            file=sys.stderr,
        )
    for tag, line_number, raw_line in parsed.duplicates:
        print(
            f"[INFO] {display_path(path)}:{line_number}: duplicate tag {tag!r}; "
            "first occurrence kept",
            file=sys.stderr,
        )


def build_report(comparisons: list[Comparison], show_value_differences: bool) -> str:
    english_total = sum(len(item.english) for item in comparisons)
    chinese_total = sum(len(item.chinese) for item in comparisons)
    english_only_total = sum(len(item.english_only) for item in comparisons)
    chinese_only_total = sum(len(item.chinese_only) for item in comparisons)
    changed_total = sum(len(item.changed) for item in comparisons)
    unchanged_total = sum(len(item.unchanged) for item in comparisons)

    lines = [
        "Official English/Chinese strings comparison",
        "",
        "Pairwise totals (unique tags per strings file):",
        f"  English entries: {english_total}",
        f"  Chinese entries: {chinese_total}",
        f"  English-only tags: {english_only_total}",
        f"  Chinese-only tags: {chinese_only_total}",
        f"  Different display values: {changed_total}",
        f"  Identical display values (informational): {unchanged_total}",
        "",
        "Per source:",
    ]
    for item in comparisons:
        lines.extend(
            (
                f"[{item.label}]",
                f"  English: {display_path(item.english_path)} ({len(item.english)} tags)",
                f"  Chinese: {display_path(item.chinese_path)} ({len(item.chinese)} tags)",
                f"  English-only: {len(item.english_only)}",
                f"  Chinese-only: {len(item.chinese_only)}",
                f"  Different values: {len(item.changed)}",
                f"  Identical values: {len(item.unchanged)}",
                "",
            )
        )

    lines.append(f"English-only tags ({english_only_total}):")
    for item in comparisons:
        for tag in item.english_only:
            value, line_number = item.english[tag]
            lines.extend(
                (
                    f"[ENGLISH-ONLY] {item.label} | {tag}",
                    f"    English value : {value}",
                    f"    source        : {display_path(item.english_path)}:{line_number}",
                    "",
                )
            )
    if not english_only_total:
        lines.append("  (none)")

    lines.append(f"Chinese-only tags ({chinese_only_total}):")
    for item in comparisons:
        for tag in item.chinese_only:
            value, line_number = item.chinese[tag]
            lines.extend(
                (
                    f"[CHINESE-ONLY] {item.label} | {tag}",
                    f"    Chinese value : {value}",
                    f"    source        : {display_path(item.chinese_path)}:{line_number}",
                    "",
                )
            )
    if not chinese_only_total:
        lines.append("  (none)")

    lines.append(f"Identical display values ({unchanged_total}, informational):")
    for item in comparisons:
        for tag in item.unchanged:
            value, line_number = item.english[tag]
            lines.extend(
                (
                    f"[UNCHANGED] {item.label} | {tag}",
                    f"    value         : {value}",
                    f"    English source: {display_path(item.english_path)}:{line_number}",
                    "",
                )
            )
    if not unchanged_total:
        lines.append("  (none)")

    if show_value_differences:
        lines.append(f"Different display values ({changed_total}):")
        for item in comparisons:
            for tag in item.changed:
                english_value, english_line = item.english[tag]
                chinese_value, chinese_line = item.chinese[tag]
                lines.extend(
                    (
                        f"[VALUE-DIFFERENCE] {item.label} | {tag}",
                        f"    English value : {english_value}",
                        f"    Chinese value : {chinese_value}",
                        f"    English source: {display_path(item.english_path)}:{english_line}",
                        f"    Chinese source: {display_path(item.chinese_path)}:{chinese_line}",
                        "",
                    )
                )

    lines.extend(
        (
            "Summary:",
            f"  English-only: {english_only_total}",
            f"  Chinese-only: {chinese_only_total}",
            f"  Different values: {changed_total}",
            f"  Identical values: {unchanged_total}",
        )
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare official English and Chinese strings tables."
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        default=DEFAULT_OUT,
        help=f"report path (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--no-file",
        action="store_true",
        help="print the report without writing an output file",
    )
    parser.add_argument(
        "--show-value-differences",
        action="store_true",
        help="include every common tag whose English and Chinese values differ",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    comparisons: list[Comparison] = []
    try:
        for label, english_raw, chinese_raw in STRING_SOURCES:
            english_path = resolve_repo_path(english_raw)
            chinese_path = resolve_repo_path(chinese_raw)
            english_parsed = parse_entries(english_path)
            chinese_parsed = parse_entries(chinese_path)
            print_parse_diagnostics(english_path, english_parsed)
            print_parse_diagnostics(chinese_path, chinese_parsed)
            english_tags = set(english_parsed.entries)
            chinese_tags = set(chinese_parsed.entries)
            common = english_tags & chinese_tags
            comparisons.append(
                Comparison(
                    label=label,
                    english_path=english_path,
                    chinese_path=chinese_path,
                    english=english_parsed.entries,
                    chinese=chinese_parsed.entries,
                    english_only=sorted(english_tags - chinese_tags),
                    chinese_only=sorted(chinese_tags - english_tags),
                    changed=sorted(
                        tag
                        for tag in common
                        if english_parsed.entries[tag][0]
                        != chinese_parsed.entries[tag][0]
                    ),
                    unchanged=sorted(
                        tag
                        for tag in common
                        if english_parsed.entries[tag][0]
                        == chinese_parsed.entries[tag][0]
                    ),
                )
            )
        report = build_report(comparisons, args.show_value_differences)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"[ERROR] could not compare official strings: {error}", file=sys.stderr)
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
    has_key_difference = any(
        item.english_only or item.chinese_only for item in comparisons
    )
    return 1 if has_key_difference else 0


if __name__ == "__main__":
    raise SystemExit(main())
