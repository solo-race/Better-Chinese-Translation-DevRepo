=======================================================================================
### Folder Strcuture ###
=======================================================================================


# Overview of original game file structures
For better understanding of the development workspace, the folder structure of the base game is first explained for context. 

The txt files comes from two layers in the base game. 

1. Base game files, located in `text/text_[language-code]`.
2. DLC files `mods/[DLC_id]/text/text_[language-code]`. The exception is `moreslugcats`, where a part of the text files is located in `moreslugcats/content`. 
3. Dialogue texts are mainly stored in independent `*.txt` files within each text_[language-code] folders, while UI strings are mainly stored in `strings.txt` in respective language specific text folders.


While the official files are positioned in this way, when the games loads, it will combine the independent files into one folder and unify all the `strings.txt` into one file, hence the structure present in the `Release` folder.

### Strings.txt structure ###
1. The text is structured in this way: [internal-code-name]|[display-name];
2. The English [display-name] should be considered the canon name to be translated, while the [code-name] is the unique internal tag for each string piece. 
3. Each language has a different [display-name], which was all translated from the English [display-name].

### Raw-texts folder structure
To clearly separate base game texts and DLC texts, the folders are divided cleary into catgories. 
- `base-game-text` contains all the texts that appear in the base game, with `base-game-text/text/text_chi` containing the Chinese texts, `base-game-text/text/text_eng` containing the English texts. The base game texts should be considered the authoritative text. Should any DLC texts specifically change a base game text, the discrepency should be flagged. 
- `expedition` and `jolly-coop` contains all the texts from the Expedition and Jolly-Coop DLC, which only has `strings.txt` for UI display. While the `strings.txt` are each named as `strings.txt` in the official release and placed in respective language folders, to reduce folder layering the English version kept the `strings.txt` file name, while the Chinese version was renamed to `strings_CN.txt`. When merging with `strings.txt` in the `Dev-texts` folder, only the contents of the text file should be merged, not the file name. Merge only the Chinese version. 
- `moreslugcats texts` contains all texts in the More Slugcats DLC, with the `text_eng` and `text_chi` folder containing the official English text and Chinese translation. Note DLC specific `strings.txt` are also inside each language folder. It should be noted that the the `dating sim` folder contains the texts in `mods/moreslugcats/contents` in the real game environment. The official game 
- `watcher` contains all texts in the Watcher DLC, with the `text_eng` and `text_chi` folder containing the official English text and Chinese translation. Note DLC specific `strings.txt` are also inside each language folder.

Contents of `Raw-texts` should not be changed at any time. It serves as the authoritative official game release reference baseline. 


### Dev-texts structure
Dev-texts merged all `*.txt` files into one folder and all contents of `strings.txt` into one unified `strings.txt`. 
This is the actual dev space for translation work. It contains the unapproved/proposed translation modifications. However, it does not contain the texts of `moreslugcats texts/dating sim` as the translation and proofreading the texts have long been solidied and the work is present in `Release/contents`. 


### Release structure
Release-ready content is now maintained in a separate Git repository, referenced from the main repository as the `release/` submodule.

```
release/
├── content/
├── text/
├── illustrations/
├── plugins/
├── modinfo.json
├── workshopdata.json
└── thumbnail.png
```

The `release/` submodule contains the complete mod artifact set (text, content, illustrations, plugin binaries, assets, metadata). Approved dev translations are synchronized into it with `scripts/sync_release.py`. The submodule should not be actively edited directly; use the sync script.

### MediaAssets
Contains PSD/AI files for display. DO NOT MODIFY unless asked. 