======================================================================================
### Rain World Chinese Localization Improvememt #####
======================================================================================

### Purpose
1. To improve the official Chinese localization of Rain World.
2. Add translations missing from the official translation
3. Add support for the game to load custom assets
4. Hotfix for a bug where the game crashes upon switching languages, caused by glyph chart switching behavior. 

### Current status
A release has been out in late 2025, with however, for newer updates of the game, viability of the translation change has not been checked, while the viability of the `.dll` plugin has not been yet verified. The original work of the codebase is located here https://github.com/HarvieSorroway/BetterChineseTransUtils. You can only read the repo, do not attempt cloning without user permission. 

### Project structure reference
The folders are currently split into Dev and Releases, where the Releases folder stores the approved translation ready for release. 
The Dev folder is split into Dev-texts and Raw-texts, where the prior hosts modified but not ye approved files, the latter hosts decrypted text files from the original game. 
For more explanation of the project file structure, read docs/structure.md

### To-dos
Development scripts designed for comparing diffs across different sources of strings.txt
It should catch:
1. Catches `strings.txt` content present in official files, but not in the modified files. The string should be clearly flagged. 
2. Translation differences between all txts across the Dev-texts and Release.