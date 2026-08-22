#!/usr/bin/env python3
"""Compare the official English and Chinese raw-text file inventories."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = "scripts/reports/official_file_count_report.txt"

# The dating-sim directory is official English-only content and is intentionally
# excluded because no official Chinese counterpart exists.
SOURCE_GROUPS = (
    (
        "base-game-text",
        "Dev/Raw-texts/base-game-text/text/text_eng",
        "Dev/Raw-texts/base-game-text/text/text_chi",
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
        "Dev/Raw-texts/moreslugcats texts/text_eng",
        "Dev/Raw-texts/moreslugcats texts/text_chi",
    ),
    (
        "watcher",
        "Dev/Raw-texts/watcher/text_eng",
        "Dev/Raw-texts/watcher/text_chi",
    ),
)


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


def collect_inventory(raw_path: str) -> dict[str, Path]:
    """Return normalized relative names mapped to official text files."""
    anchor = resolve_repo_path(raw_path)
    if not anchor.exists():
        raise FileNotFoundError(anchor)

    if anchor.is_dir():
        files = sorted(
            (path for path in anchor.rglob("*.txt") if path.is_file()),
            key=lambda path: path.as_posix(),
        )
        return {
            path.relative_to(anchor).as_posix(): path
            for path in files
        }

    if not anchor.is_file():
        raise OSError(f"official text source is not a file or directory: {anchor}")
    if anchor.suffix.lower() != ".txt":
        raise ValueError(f"official text source is not a .txt file: {anchor}")

    # Expedition and Jolly Co-op use strings_CN.txt for Chinese, but the two
    # files occupy the same logical strings.txt role.
    key = "strings.txt" if anchor.name == "strings_CN.txt" else anchor.name
    return {key: anchor}


def build_report(group_results: list[dict[str, object]]) -> str:
    english_total = sum(len(result["english"]) for result in group_results)
    chinese_total = sum(len(result["chinese"]) for result in group_results)
    english_only = [
        (result["label"], result["english"][key])
        for result in group_results
        for key in result["english_only"]
    ]
    chinese_only = [
        (result["label"], result["chinese"][key])
        for result in group_results
        for key in result["chinese_only"]
    ]

    lines = [
        "Official text-file count comparison",
        "",
        f"English total files: {english_total}",
        f"Chinese total files: {chinese_total}",
        f"English minus Chinese: {english_total - chinese_total}",
        "Excluded: Dev/Raw-texts/moreslugcats texts/dating sim "
        "(official English-only; not compared)",
        "",
        "Per source group:",
    ]
    for result in group_results:
        lines.extend(
            (
                f"[{result['label']}]",
                f"  English files: {len(result['english'])}",
                f"  Chinese files: {len(result['chinese'])}",
                f"  English-only files: {len(result['english_only'])}",
                f"  Chinese-only files: {len(result['chinese_only'])}",
                "",
            )
        )

    lines.append(f"English-only files ({len(english_only)}):")
    if english_only:
        lines.extend(
            f"  {display_path(path)} [{label}]" for label, path in english_only
        )
    else:
        lines.append("  (none)")

    lines.append(f"Chinese-only files ({len(chinese_only)}):")
    if chinese_only:
        lines.extend(
            f"  {display_path(path)} [{label}]" for label, path in chinese_only
        )
    else:
        lines.append("  (none)")

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare official English and Chinese raw-text file counts."
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
        group_results: list[dict[str, object]] = []
        for label, english_source, chinese_source in SOURCE_GROUPS:
            english = collect_inventory(english_source)
            chinese = (
                collect_inventory(chinese_source) if chinese_source is not None else {}
            )
            english_only = sorted(set(english) - set(chinese))
            chinese_only = sorted(set(chinese) - set(english))
            group_results.append(
                {
                    "label": label,
                    "english": english,
                    "chinese": chinese,
                    "english_only": english_only,
                    "chinese_only": chinese_only,
                }
            )
        report = build_report(group_results)
    except (OSError, ValueError) as error:
        print(f"[ERROR] could not inspect official text files: {error}", file=sys.stderr)
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
    has_difference = any(
        result["english_only"] or result["chinese_only"]
        for result in group_results
    )
    return 1 if has_difference else 0


if __name__ == "__main__":
    raise SystemExit(main())