#!/usr/bin/env python3
"""Scan Dev dialogue texts for character-name spelling inconsistency."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = "scripts/reports/dev_dialogue_character_names_report.txt"
DEV_TEXT_ROOT = "Dev/Dev-texts/text_chi"
DEV_STRINGS = "Dev/Dev-texts/text_chi/strings.txt"

NUMBERED_DIALOGUE_RE = re.compile(
    r"^\s*(\d+)\s*:\s*(.+?)\s*:\s*(.+?)\s*$"
)
NAMED_DIALOGUE_RE = re.compile(r"^\s*([^:：\[\]【】<>{}\d][^:：]{0,24})\s*：\s*(.+)$")
EXCLUDED_PREFIXES = (
    "SPECEVENT :",
    "PEBBLESWAIT :",
    "源节点追踪：",
    "消息内容：",
    "设备清单：",
    "致命异常：",
    "汉化组注释：",
    "瞧啊：",
    "请想象：",
    "当初你来时对我说：",
    "设想：",
    "现在：",
)
SYSTEM_ACTION_TAGS = ("<", ">", "[")

# Canonical group: English label -> accepted Chinese dialogue spellings.
# The first spelling is the canonical UI/reference spelling; the remaining
# entries are recognized dialogue aliases. Add future speaker names here with
# their accepted Chinese spellings.
CHARACTER_GROUPS = {
    "Five Pebbles": ("五块卵石", "五卵石"),
    "Looks to the Moon": (
        "仰望皓月",
        "望月",
        "皓月",
        "月亮大姐",
        "月亮大姐姐",
        "月姐",
    ),
    "No Significant Harassment": ("无稽烦忧",),
    "Seven Red Suns": ("七轮红日",),
    "Chasing Wind": ("追逐清风",),
    "Wandering Omen": ("徘徊预兆",),
    "Sliver of Straw": ("茅草裂片",),
    "Era of Clouds and Fog": ("云雾纪元",),
    "Gazing Stars": ("凝望群星",),
    "Secluded Instinct": ("隔绝本能",),
    "Pleading Intellect": ("申辩智能",),
    "Half of One Leg": ("局部地狱",),
    "Erratic Pulse": ("不稳脉冲",),
    "Unfortunate Evolution": ("不安乞儿",),
    "No Godly Indignation": ("嫌弃靛蓝",),
    "Half Forest": ("半片森林",),
}

# Known independent developer-commentary speaker names (not in-game
# characters). They should not be reported as unmapped dialogue names.
DEVELOPER_SPEAKERS = frozenset(
    {"Andrew", "Will", "Norgad", "Dakras", "Screams", "Slugitar", "Cappin"}
)

# Deliberately misspelled character names found in Dev dialogue. These are
# always reported even though no canonical English-literal mapping is inferred.
KNOWN_TYPOS = {
    "五瓶百石": "Five Pebbles",
}


@dataclass(frozen=True)
class DialogueRecord:
    path: Path
    line_number: int
    raw_line: str
    speaker_raw: str
    speaker_display: str
    text: str


@dataclass(frozen=True)
class NameVariant:
    character: str
    alias: str
    canonical: str
    source: str
    path: Path
    line_number: int


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


def parse_entries(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw_line.strip() or "|" not in raw_line:
            continue
        tag, value = raw_line.split("|", 1)
        if tag not in entries:
            entries[tag] = value
    return entries


def build_alias_maps() -> tuple[dict[str, tuple[str, ...]], dict[str, str]]:
    """Return English->aliases and Chinese-alias->English maps."""
    english_aliases: dict[str, tuple[str, ...]] = {}
    alias_to_english: dict[str, str] = {}

    for character, aliases in CHARACTER_GROUPS.items():
        english_aliases[character] = aliases
        for alias in aliases:
            alias_to_english[alias] = character

    for alias, character in KNOWN_TYPOS.items():
        alias_to_english[alias] = character
        if character not in english_aliases:
            english_aliases[character] = (alias,)

    return english_aliases, alias_to_english


def extract_numeric_dialogue(
    path: Path, line_number: int, raw_line: str
) -> DialogueRecord | None:
    match = NUMBERED_DIALOGUE_RE.match(raw_line)
    if not match:
        return None
    first, middle, last = (part.strip() for part in match.groups())
    middle_is_number = middle.lstrip("-").isdigit()
    last_is_number = last.lstrip("-").isdigit()
    if middle_is_number and not last_is_number:
        speaker = first
        text = last
    elif last_is_number and not middle_is_number:
        speaker = first
        text = middle
    else:
        return None

    if text.startswith("<") or text.endswith(">"):
        return None
    if any(raw_line.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return None
    return DialogueRecord(
        path=path,
        line_number=line_number,
        raw_line=raw_line,
        speaker_raw=speaker,
        speaker_display=speaker,
        text=text,
    )


def extract_named_dialogue(
    path: Path, line_number: int, raw_line: str
) -> DialogueRecord | None:
    if any(raw_line.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return None
    match = NAMED_DIALOGUE_RE.match(raw_line)
    if not match:
        return None
    speaker_raw, text = (part.strip() for part in match.groups())
    if not speaker_raw or not text:
        return None
    return DialogueRecord(
        path=path,
        line_number=line_number,
        raw_line=raw_line,
        speaker_raw=speaker_raw,
        speaker_display=speaker_raw,
        text=text,
    )


def dialogue_records(path: Path) -> list[DialogueRecord]:
    records: list[DialogueRecord] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        if raw_line.startswith("0-") and line_number == 1:
            continue
        if raw_line.startswith("【"):
            continue
        named = extract_named_dialogue(path, line_number, raw_line)
        if named is not None and not any(
            token in named.text for token in SYSTEM_ACTION_TAGS
        ):
            records.append(named)
            continue
        numeric = extract_numeric_dialogue(path, line_number, raw_line)
        if numeric is not None:
            records.append(numeric)
    return records


def report_variants(records: list[DialogueRecord]) -> list[NameVariant]:
    variants: list[NameVariant] = []
    _, alias_to_english = build_alias_maps()

    for record in records:
        speaker_clean = record.speaker_raw.rstrip("：:")
        if speaker_clean in alias_to_english:
            character = alias_to_english[speaker_clean]
            aliases = CHARACTER_GROUPS.get(character, (speaker_clean,))
            canonical = aliases[0]
            if canonical != speaker_clean:
                variants.append(
                    NameVariant(
                        character=character,
                        alias=speaker_clean,
                        canonical=canonical,
                        source=record.raw_line,
                        path=record.path,
                        line_number=record.line_number,
                    )
                )
            continue

        # Numeric dialogue lines do not have a speaker name. Search only the
        # body for known misspellings or aliases that differ from canonical.
        if record.speaker_raw.isdigit():
            for alias, character in alias_to_english.items():
                aliases = CHARACTER_GROUPS.get(character, (alias,))
                canonical = aliases[0]
                if alias in record.text and canonical != alias:
                    variants.append(
                        NameVariant(
                            character=character,
                            alias=alias,
                            canonical=canonical,
                            source=record.raw_line,
                            path=record.path,
                            line_number=record.line_number,
                        )
                    )
            continue

        # Unmapped named speakers that are not developer commentary are
        # reported separately by the caller.
    return variants


def unmapped_named_speakers(records: list[DialogueRecord]) -> list[DialogueRecord]:
    _, alias_to_english = build_alias_maps()
    unmapped = []
    for record in records:
        speaker_clean = record.speaker_raw.rstrip("：:")
        if record.speaker_raw.isdigit():
            continue
        if speaker_clean in alias_to_english:
            continue
        if speaker_clean in DEVELOPER_SPEAKERS:
            continue
        unmapped.append(record)
    return unmapped


def build_report(
    variants: list[NameVariant],
    unmapped_speakers: list[DialogueRecord],
    scanned_files: int,
    dialogue_count: int,
) -> str:
    groups: dict[tuple[str, str], list[NameVariant]] = defaultdict(list)
    for row in variants:
        groups[(row.character, row.alias)].append(row)

    lines = [
        "Dev dialogue character-name consistency",
        "",
        f"Scanned files: {scanned_files}",
        f"Dialogue records: {dialogue_count}",
        f"Character alias variants: {len(variants)}",
        f"Unmapped named speakers: {len(unmapped_speakers)}",
        "",
    ]

    lines.append("Character alias variants:")
    for (character, alias), rows in sorted(
        groups.items(), key=lambda item: (item[0][0], item[0][1])
    ):
        canonical = rows[0].canonical
        lines.append(
            f"[VARIANT] {character} | alias: {alias} | canonical: {canonical}"
        )
        for row in rows:
            lines.append(
                f"    {display_path(row.path)}:{row.line_number} | {row.source}"
            )
        lines.append("")

    lines.append("Unmapped named speakers:")
    if unmapped_speakers:
        for record in unmapped_speakers:
            lines.append(
                f"[UNMAPPED] {record.speaker_display} | "
                f"{display_path(record.path)}:{record.line_number} "
                f"| {record.raw_line}"
            )
    else:
        lines.append("  (none)")

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan Dev dialogue texts for character-name spelling inconsistency."
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
    try:
        root = resolve_repo_path(DEV_TEXT_ROOT)
        # Resolve DEV_STRINGS so a missing/misconfigured file is surfaced, but
        # the current scanner uses explicit CHARACTER_GROUPS rather than the
        # strings table. This also keeps a future strings-derived mode available.
        resolve_repo_path(DEV_STRINGS)

        files = sorted(
            path for path in root.glob("*.txt") if path.name != "strings.txt"
        )
        variants: list[NameVariant] = []
        unmapped: list[DialogueRecord] = []
        dialogue_count = 0

        for path in files:
            records = dialogue_records(path)
            dialogue_count += len(records)
            variants.extend(report_variants(records))
            unmapped.extend(unmapped_named_speakers(records))

        report = build_report(variants, unmapped, len(files), dialogue_count)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"[ERROR] could not scan dev dialogues: {error}", file=sys.stderr)
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
    return 1 if variants or unmapped else 0


if __name__ == "__main__":
    raise SystemExit(main())
