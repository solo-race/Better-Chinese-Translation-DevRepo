#!/usr/bin/env python3
"""Check repeated Expedition item/creature names for Chinese consistency."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = "scripts/reports/item_translation_consistency_report.txt"
ENTITY_TAG_PREFIXES = ("objecttype-", "creaturetype-")
CHARACTER_NAME_VALUES = frozenset(
    {
        "five pebbles",
        "looks to the moon",
        "the watcher",
        "the survivor",
        "the monk",
        "the hunter",
        "the artificer",
        "the gourmand",
        "the rivulet",
        "the spearmaster",
        "the saint",
        "the chieftain",
        "the wanderer",
        "the outlaw",
        "the friend",
        "the martyr",
        "the mother",
        "the nomad",
        "the pilgrim",
        "the scholar",
        "the journey",
        "survivor",
        "monk",
        "hunter",
        "artificer",
        "gourmand",
        "rivulet",
        "spearmaster",
        "saint",
        "chieftain",
        "wanderer",
        "outlaw",
        "friend",
        "martyr",
        "mother",
        "nomad",
        "pilgrim",
        "scholar",
        "journey",
    }
)
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
SOURCE_ORDER = {label: index for index, (label, _, _) in enumerate(STRING_SOURCES)}
Entry = tuple[str, int]


@dataclass
class ParsedStrings:
    entries: dict[str, Entry]
    warnings: list[tuple[int, str]]
    duplicates: list[tuple[str, int, str]]


@dataclass(frozen=True)
class Occurrence:
    source: str
    english_path: Path
    chinese_path: Path
    tag: str
    english_value: str
    english_line: int
    chinese_value: str | None
    chinese_line: int | None


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


def find_repeated_items(
    loaded_sources: list[tuple[str, Path, Path, ParsedStrings, ParsedStrings]],
) -> tuple[int, int, dict[str, list[Occurrence]]]:
    canonical_values = {
        value.casefold()
        for _, _, _, english, _ in loaded_sources
        for tag, (value, _) in english.entries.items()
        if tag.lower().startswith(ENTITY_TAG_PREFIXES)
    }
    candidate_values = canonical_values | CHARACTER_NAME_VALUES
    grouped: dict[str, list[Occurrence]] = defaultdict(list)
    for source, english_path, chinese_path, english, chinese in loaded_sources:
        for tag, (english_value, english_line) in english.entries.items():
            normalized_value = english_value.casefold()
            if normalized_value not in candidate_values:
                continue
            chinese_entry = chinese.entries.get(tag)
            chinese_value = chinese_entry[0] if chinese_entry is not None else None
            chinese_line = chinese_entry[1] if chinese_entry is not None else None
            grouped[normalized_value].append(
                Occurrence(
                    source=source,
                    english_path=english_path,
                    chinese_path=chinese_path,
                    tag=tag,
                    english_value=english_value,
                    english_line=english_line,
                    chinese_value=chinese_value,
                    chinese_line=chinese_line,
                )
            )

    repeated_expedition: dict[str, list[Occurrence]] = {}
    for normalized_value, occurrences in grouped.items():
        source_names = {occurrence.source for occurrence in occurrences}
        if "expedition" not in source_names or len(source_names) < 2:
            continue
        repeated_expedition[normalized_value] = sorted(
            occurrences,
            key=lambda occurrence: (
                SOURCE_ORDER[occurrence.source],
                occurrence.tag,
            ),
        )
    return len(canonical_values), len(CHARACTER_NAME_VALUES), repeated_expedition


def is_inconsistent(occurrences: list[Occurrence]) -> bool:
    return any(
        occurrence.chinese_value is None for occurrence in occurrences
    ) or len({occurrence.chinese_value for occurrence in occurrences}) > 1


def build_report(
    canonical_count: int,
    character_count: int,
    groups: dict[str, list[Occurrence]],
) -> str:
    inconsistent = {
        value: occurrences
        for value, occurrences in groups.items()
        if is_inconsistent(occurrences)
    }
    consistent = {
        value: occurrences
        for value, occurrences in groups.items()
        if value not in inconsistent
    }
    lines = [
        "Expedition repeated item/creature/character translation consistency",
        "",
        "Detection rule: group case-insensitive English display names when the "
        "name is a canonical objecttype-/creaturetype- entity or a configured "
        "character name; report groups that include Expedition and another "
        "official strings source.",
        f"Canonical English entity names: {canonical_count}",
        f"Configured character name values: {character_count}",
        f"Repeated Expedition names: {len(groups)}",
        f"Inconsistent translations: {len(inconsistent)}",
        f"Consistent translations: {len(consistent)}",
        "",
    ]

    for heading, selected in (
        ("INCONSISTENT", inconsistent),
        ("CONSISTENT", consistent),
    ):
        for normalized_value in sorted(
            selected,
            key=lambda value: selected[value][0].english_value.casefold(),
        ):
            display_name = selected[normalized_value][0].english_value
            lines.append(f"[{heading}] {display_name}")
            for occurrence in selected[normalized_value]:
                chinese_value = (
                    occurrence.chinese_value
                    if occurrence.chinese_value is not None
                    else "<MISSING IN CHINESE>"
                )
                lines.extend(
                    (
                        f"  {occurrence.source} | tag: {occurrence.tag}",
                        f"    English value : {occurrence.english_value}",
                        f"    Chinese value : {chinese_value}",
                        f"    English source: "
                        f"{display_path(occurrence.english_path)}:{occurrence.english_line}",
                    )
                )
                if occurrence.chinese_line is not None:
                    lines.append(
                        f"    Chinese source: "
                        f"{display_path(occurrence.chinese_path)}:{occurrence.chinese_line}"
                    )
            lines.append("")

    lines.extend(
        (
            "Summary:",
            f"  Repeated Expedition names: {len(groups)}",
            f"  Inconsistent translations: {len(inconsistent)}",
            f"  Consistent translations: {len(consistent)}",
        )
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check repeated Expedition item/creature translations."
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    loaded_sources: list[tuple[str, Path, Path, ParsedStrings, ParsedStrings]] = []
    try:
        for source, english_raw, chinese_raw in STRING_SOURCES:
            english_path = resolve_repo_path(english_raw)
            chinese_path = resolve_repo_path(chinese_raw)
            english = parse_entries(english_path)
            chinese = parse_entries(chinese_path)
            print_parse_diagnostics(english_path, english)
            print_parse_diagnostics(chinese_path, chinese)
            loaded_sources.append(
                (source, english_path, chinese_path, english, chinese)
            )
        canonical_count, character_count, groups = find_repeated_items(loaded_sources)
        report = build_report(canonical_count, character_count, groups)
    except (OSError, UnicodeError, ValueError) as error:
        print(
            f"[ERROR] could not check item translation consistency: {error}",
            file=sys.stderr,
        )
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
    return 1 if any(is_inconsistent(rows) for rows in groups.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
