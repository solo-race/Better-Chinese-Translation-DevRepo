# Project Memory

This file records the current state of the Rain World Chinese localization project for future developers and maintainers. It is not a user manual; see `scripts/操作指南.md` for script usage.

## Repository overview

- Project: Rain World Chinese localization improvement mod.
- The repository contains official raw game text, development translation text, release-ready mod content, and comparison automation scripts.
- Git branch: `main`.
- No commit history is assumed to be authoritative; the working tree is the current development state.

## Directory roles

- `Dev/Raw-texts/`: official decrypted game text.
  - Must remain read-only and authoritative.
  - Contains base game, Expedition, Jolly Co-op, More Slugcats, Watcher, and English-only dating-sim text.
  - The dating-sim directory is intentionally excluded from English/Chinese file-count comparisons because it is official English-only content with no official Chinese counterpart.
- `Dev/Dev-texts/`: current translation workspace.
  - Merged dialogue/story files and the unified `strings.txt`.
  - This is where proposed translation edits belong.
- `release/`: git submodule containing approved, release-ready mod content.
  - Points to the standalone release repository: `https://github.com/solo-race/Better-Chinese-Translation-ReleaseRepo`.
  - Contains `text/`, `content/`, `illustrations/`, `plugins/`, `modinfo.json`, `workshopdata.json`, and `thumbnail.png`.
  - Approved translations are synchronized into it with `scripts/sync_release.py`.
- `scripts/`: automation scripts and operation guide.
  - `scripts/reports/` is ignored by Git and holds generated reports.
- `docs/structure.md`: detailed folder-structure documentation.

## Strings format

- Lines use `TAG|display-value`.
- The English display value is the canonical source for translation.
- The tag is the unique internal key.
- Files are UTF-8; many begin with a BOM.
- Line endings may be CRLF or LF; parsing uses `splitlines()`.
- Duplicate tags inside a file: first occurrence is kept; duplicates are reported for visibility.

## Current scripts

### 1. `scripts/check_missing_strings.py`

- Finds official Chinese tags missing from `Dev/Dev-texts/text_chi/strings.txt`.
- Inputs: five official Chinese string files plus the dev string file.
- Output: `scripts/reports/missing_strings_report.txt`.
- Exit codes:
  - `0`: no missing tags
  - `1`: missing tags found
  - `2`: I/O or usage error

### 2. `scripts/compare_official_file_counts.py`

- Compares official English and Chinese raw-text file inventories.
- Excludes `moreslugcats texts/dating sim` from the comparison.
- Output: `scripts/reports/official_file_count_report.txt`.
- Exit codes:
  - `0`: no unmatched files
  - `1`: unmatched files found
  - `2`: I/O or usage error

### 3. `scripts/compare_official_strings.py`

- Compares official English and Chinese `strings.txt` tables.
- Reports English-only tags, Chinese-only tags, identical values, and value differences.
- Supports `--show-value-differences`.
- Output: `scripts/reports/official_strings_comparison.txt`.
- Exit codes:
  - `0`: no key-level differences
  - `1`: key differences found
  - `2`: I/O or usage error

### 4. `scripts/check_item_translation_consistency.py`

- Detects repeated English item/creature names and character names whose Chinese translations differ across official sources.
- Internally detects canonical `objecttype-` and `creaturetype-` names.
- Character-name candidates are maintained in `CHARACTER_NAME_VALUES`.
- Output: `scripts/reports/item_translation_consistency_report.txt`.
- Exit codes:
  - `0`: no inconsistent translations
  - `1`: inconsistent translations found
  - `2`: I/O or usage error

### 5. `scripts/check_dev_dialogue_character_names.py`

- Scans `Dev/Dev-texts/text_chi/` dialogue text for character-name spelling inconsistency.
- Recognizes named dialogue lines (`Name：text`) and numeric event dialogue lines.
- Reports:
  - `[VARIANT]`: non-canonical character spelling.
  - `[UNMAPPED]`: named speaker not in the known character groups.
- Character groups are maintained in `CHARACTER_GROUPS`.
- Output: `scripts/reports/dev_dialogue_character_names_report.txt`.
- Exit codes:
  - `0`: no variants and no unmapped named speakers
  - `1`: variants or unmapped speakers found
  - `2`: I/O or usage error

## Key current findings

As of the latest verified runs:

- Official English text files: 407.
- Official Chinese text files: 404.
- English-only official files: 3:
  - `Dev/Raw-texts/base-game-text/text/text_eng/8.txt`
  - `Dev/Raw-texts/base-game-text/text/text_eng/9.txt`
  - `Dev/Raw-texts/moreslugcats texts/text_eng/36.txt`
- Dev strings report:
  - Official tags: 2367
  - Dev tags: 2382
  - Missing tags: 117
- Repeated Expedition item/creature translation consistency:
  - Repeated Expedition names: 16
  - Inconsistent translations: 9
  - Consistent translations: 7
- Dev dialogue character-name scanner:
  - Scanned files: 359
  - Dialogue records: 986
  - Character alias variants: 51
  - Unmapped named speakers: 10
  - Broadcast headers are also scanned for participant names.
  - Known variants: `五瓶百石` for Five Pebbles; `月亮大姐` and `月亮大姐姐` for Looks to the Moon.
  - Known unmapped speakers: `主持者`, `手势之铃` in `240.txt`.

## Environment

- Python 3.10 or newer is recommended.
- A local virtual environment exists at `.venv/`.
- Scripts use only the Python standard library.
- The system Python may be externally managed (PEP 668); use `.venv/bin/python`.

## Maintenance conventions

- Keep `Dev/Raw-texts/` read-only.
- Never edit release text or multimedia assets unless explicitly requested.
- When dev translations are approved, run `scripts/sync_release.py` to copy them into the `release/` submodule.
- The sync script does not push; the developer commits and pushes the submodule update manually.
- When the official game updates:
  - Re-run all scripts.
  - Check every generated report.
  - If new official paths are introduced, update the file-path constants in the relevant scripts.
  - If a new character appears in dialogue, add it to `CHARACTER_GROUPS` in `check_dev_dialogue_character_names.py`.
  - If a new character name appears in official strings, consider adding it to `CHARACTER_NAME_VALUES` in `check_item_translation_consistency.py`.
- Generated reports under `scripts/reports/` are intentionally ignored and should not be committed.

## Release packaging

- Standalone release repository: `https://github.com/solo-race/Better-Chinese-Translation-ReleaseRepo`.
- It is mounted in the main repo as the `release/` git submodule.
- Packaging is triggered by a tag push in the release repository; the GitHub Actions workflow creates a zip and uploads it as a GitHub Release.
