======================================================================================
### Rain World Chinese Localization Improvement #####
======================================================================================

### Purpose
1. Improve the official Chinese localization of Rain World.
2. Add translations missing from the official translation.
3. Add support for the game to load custom assets.
4. Hotfix for a bug where the game crashes upon switching languages, caused by glyph chart switching behavior.

### Current status
- A release has been out in late 2025.
- For newer updates of the game, the viability of the translation changes has not been checked.
- The viability of the `.dll` plugin has not yet been verified.
- The original utility codebase is located here: <https://github.com/HarvieSorroway/BetterChineseTransUtils>
- The upstream repository should only be read; do not attempt cloning without user permission.

### Development script status
The project now includes a set of development scripts under `scripts/`:

| Script | Purpose | Default report |
|---|---|---|
| `scripts/check_missing_strings.py` | Find official Chinese string tags that are missing from the dev string file. | `scripts/reports/missing_strings_report.txt` |
| `scripts/compare_official_file_counts.py` | Compare official English and Chinese raw-text file inventories. | `scripts/reports/official_file_count_report.txt` |
| `scripts/compare_official_strings.py` | Compare official English and Chinese `strings.txt` key/value tables. | `scripts/reports/official_strings_comparison.txt` |
| `scripts/check_item_translation_consistency.py` | Check repeated English item/creature/character names for consistent Chinese translations. | `scripts/reports/item_translation_consistency_report.txt` |
| `scripts/check_dev_dialogue_character_names.py` | Scan dev-space dialogue texts and broadcast headers for inconsistent character-name spellings. | `scripts/reports/dev_dialogue_character_names_report.txt` |
| `scripts/sync_release.py` | Sync approved dev text into the release submodule. | terminal output |

All scripts:
- Are Python 3 stdlib-only.
- Are designed to be run with the local virtual environment `.venv`.
- Support `--out PATH` and `--no-file` where applicable.
- Never modify official raw text, dev text, release text, or multimedia files.
- Generate reports into `scripts/reports/`, which is ignored by Git.

A Chinese operation guide is available at `scripts/操作指南.md`.

### Project structure reference
- `release/`: git submodule containing approved, release-ready mod content. This is the standalone release repository used for GitHub Releases.
- `Dev/`: development space, split into:
  - `Dev-texts/`: modified/not-yet-approved translation files.
  - `Raw-texts/`: decrypted official game text, used as an authoritative read-only baseline.
- `scripts/`: automation and comparison scripts plus generated reports.
- `docs/structure.md`: detailed folder structure explanation.

### Release workflow
1. Work on translations in `Dev/Dev-texts/`.
2. After approval, run:
   ```bash
   .venv/bin/python scripts/sync_release.py
   ```
3. The script syncs approved dev text into `release/` (`release/text/` and `release/content/`).
4. Commit and push the submodule update, then update the submodule pointer in the main repo.
5. The `release/` repository GitHub Actions workflow automatically packages the mod and creates a GitHub Release when a version tag is pushed or a release is triggered.

For more explanation of the project file structure, read `docs/structure.md`.
