# General Informations  
- GBFAL is a static web page. No API is available.  
- If you want to put a link towards GBFAL for a specific element on your website, use `https://mizagbf.github.io/GBFAL/?id=ID` where `ID` is the element ID on GBFAL.  
- If you want to reuse GBFAL data for your own purpose, you can download the `json/data.json` file from `https://raw.githubusercontent.com/MizaGBF/GBFAL/main/json/data.json`.  
- Sorry if you find typos or mistakes in this file. Reminder I do this as a hobby, on my spare time.
  
# json/data.json Breakdown  
- The file is a big JSON Object. If possible, try to not reload it too often. You can check the timestamp in `json/changelog.json` to check when it has been modified for the last time.  
- The following informations might be inaccurate. I'll try to keep it up to date as much as possible. In doubt, double check with `updater.py` and `js/script.js` codes.  
  
### File Path  
URLs follow the following format:  
`ENDPOINT/LANG/ASSET_TYPE/PATH`  
where:  
- `ENDPOINT`: Can be `https://granbluefantasy.jp` (not recommended because of latency) or one of the CDN mirror: `https://prd-game-a-granbluefantasy.akamaized.net/`, `https://prd-game-a1-granbluefantasy.akamaized.net/` to `https://prd-game-a5-granbluefantasy.akamaized.net/`.  
- `LANG`: Either `assets_en` (for English) or `assets` (for Japanese). Note that `json/data.json` is only updated with English files. In case of differences between both versions, some files might be missing.  
- `ASSET_TYPE`: Either `img` (for Image files), `sound` (for Sound files), `js` (for Javascript files) and more not documented here.  
- `PATH`: The remaining path towards the resource. For example: [img/sp/assets/npc/zoom/3040068000_01.png](https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/zoom/3040068000_01.png).  
  
### json/data.json content  
- `version`: Integer, the file version. Currently **2**.
- `valentines`: Object of ID, integer pairs, for elements with (possibly) white day or valentine scene files. The integer is unused. Elements are always from the `characters`, `skins` or `npcs` indexes.  
- `characters`: Object of ID, data pairs. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of nine lists, each containing file names. (`[[], [], [], [], [], [], [], [], []]`).
    - Index 0: Spritesheets. Path: `sp/cjs/FILE.png`.  
    - Index 1: Attack sheets (effects playing during auto attacks). Path: `sp/cjs/FILE.png`.  
    - Index 2: Charage Attack sheets. Path: `sp/cjs/FILE.png`.  
    - Index 3: AOE Skill sheets (played during AOE/Party Wise skills). Path: `sp/cjs/FILE.png`.  
    - Index 4: Single target skill sheets (played during one foe skills or targeted buff/heal skills). Path: `sp/cjs/FILE.png`.  
    - Index 5: General files. This will be used for most files used in the inventory for example and one will exist for all uncaps and more (for example, if the character has differents arts based on the MC gender).  
    - Index 6: SD files (as seen on the outfit selection screen). Path: `sp/assets/npc/sd/FILE.png`. This is the array to use if you want to generate a list of uncaps without being parazited by bonus poses and such.  
    - Index 7: Scene file suffixes. Possible paths: `sp/quest/scene/character/body/ID_SUFFIX.png` (used in cutscenes) or  `sp/raid/navi_face/ID_SUFFIX.png` (portrait used in battles, when characters talk). A file being in this list means either or both of those paths are valid.  
    - Index 8: Voice file suffixes. Path: `voice/ID_SUFFIX.mp3`.  
- `partners`: Nearly the same as `characters`, up to Index 5 **included**. What I call partners are characters lended to you during script battles.  
- `summons`: Object of ID, data pairs. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of three lists, each containing file names. (`[[], [], []]`).
    - Index 0: General files. This will be used for most files used in the inventory for example and one will exist for all uncaps and more.  
    - Index 1: Summon call sheets. Path: `sp/cjs/FILE.png`.  
    - Index 2: Damage sheets (effects played after the call). Path: `sp/cjs/FILE.png`.  
- `weapons`: Object of ID, data pairs. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of three lists, each containing file names. (`[[], [], []]`).
    - Index 0: General files. This will be used for most files used in the inventory for example and one will exist for all uncaps and more.  
    - Index 1: Attack sheets (effects playing during auto attacks). Path: `sp/cjs/FILE.png`.  
    - Index 2: Charage Attack sheets. Path: `sp/cjs/FILE.png`.  
- `enemies`: Object of ID, data pairs. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of six lists, each containing file names. (`[[], [], [], [], [], []]`).
    - Index 0: General files. This will be used for icons seen near the HP bar or before joining the battle.  
    - Index 1: Spritesheets. Path: `sp/cjs/FILE.png`.  
    - Index 2: Appear sheets (the animation playing with the boss name at the start of the battle). Path: `sp/cjs/FILE.png`.  
    - Index 3: Attack sheets (effects playing during auto attacks). Path: `sp/cjs/FILE.png`.  
    - Index 4: Single target charge attack sheets. Path: `sp/cjs/FILE.png`.  
    - Index 5: AOE charge attack sheets. Path: `sp/cjs/FILE.png`.  
- `skins`: Same format as `characters`.  
- `job`: Object of ID, data pairs for MC classes or skins. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of eleven lists, each containing file names. (`[[], [], [], [], [], [], [], [], [], [], []]`).
    - Index 0: Base file. Used for icons (`sp/ui/icon/job/FILE.png`) and texts (`sp/ui/job_name/job_list/FILE.png`, ...).  
    - Index 1: Other Base file. Used for inventory portraits and such.  
    - Index 2: Detail portrait files.  
    - Index 3: Other detail portrait files. Similar to Index 2.  
    - Index 4: More files. Those will include some color swap/helmetless files.  
    - Index 5: Color swap/helmetless SD sprite files.
    - Index 6: Main hand ID strings. For internal use only.  
    - Index 7: Spritesheets. Path: `sp/cjs/FILE.png`.  
    - Index 8: Attack sheets (effects playing during auto attacks). Path: `sp/cjs/FILE.png`.  
    - Index 9: Charage attack sheets. Path: `sp/cjs/FILE.png`.  
    - Index 10: Unlock animation sheets. Path: `sp/cjs/FILE.png`.  
- `job_wpn`: Object of weapon ID, class ID pairs. Some special weapons are used in the game internally to have specific animations for some class outfits. This object is for internal use and is used to associate those weapons with the corresponding class ID.  
- `job_key`: Similar to `job_wpn`, it's also for internal use. Classes all have what I call a secondary ID, a three characters string. Those strings are used for spritesheets. This object lists them.  
- `background`: Object of ID, data pairs for guild/battle backgrounds. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of one single list, containing file names. (`[[]]`).  
    - Index 0: The list of background files.  
    - Possible paths are `sp/guild/custom/bg/FILE.png` for MAIN backgrounds and `sp/raid/bg/FILE.jpg` for everything else.  
- `title`: Object of ID, integer pairs, for title screens. The integer is unused. Simply use `sp/top/bg/bg_ID.jpg`.  
- `suptix`: Object of ID, integer pairs, for surprise ticket banners. The integer is unused. Simply use `sp/gacha/campaign/surprise/top_ID.jpg`.  
- `lookup`: Object of ID, string pairs. It's used to create the tag lists on GBFAL. The ID can be found in any other index and the string is the list of tags. The element starting with `@@` corresponds to the wiki link.  
- `events`: Object of ID, data pairs for events. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of twenty six elements. (`[CHAPTER_COUNT, THUMBNAIL_ID, [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]`).  
    - Index 0: An integer, the estimated number of chapters in the event. Set to **-1** if no chapters is found, **0** if the number of chapters is unknown.  
    - Index 1. A string, the event thumbnail ID. Set to **null** if not set.  
    - Index 2: Opening chapter files.  
    - Index 3: Ending chapter files.  
    - Index 4: Other files.  
    - Index 5 to 24: Numbered chapter files (**1** to **20**).  
    - Index 25: Skycompass files.  
- `skills`: Object of ID (zfilled to string of length 4) and data pairs. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of one single list, containing file names. (`[[]]`).  
    - Index 0: One known file variation of this skill. Not all of them are stored. This index is mostly to track which skills exist.  
    - Possible files follow the following format: `sp/ui/icon/ability/m/ID.png` or `sp/ui/icon/ability/m/ID_N.png` where `N` can be **1** to **5**.  
- `subskills`: Object of ID and integer pairs for subskills (such as Wamdus' s1). The integer is unused. Paths: `sp/assets/item/ability/s/ID_N.jpg` where `N` can be **1** to **3**.  
- `buffs`: Object of ID (zfilled to string of length 4), data pairs for buff icons. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of two lists, each containing file names. (`[[], [], [], [], [], [], [], [], [], []]`).
    - Index 0: One file (the main one to be displayed on GBFAL). Path: `sp/ui/icon/status/x64/status_FILE.png`.  
    - Index 1: Some valid suffixes for this buff. Because of the sheer number of possible variations, only a few of them are checked and stored. Path: `sp/ui/icon/status/x64/status_ID_suffix.png`.  
- `eventthumb`: Object of ID and integer pairs for event thumbnail. For internal use only. The integer is set to **1** if it's used for an event.  
- `story`: Object of chapter ID (zfilled to string of length 3) and data pairs. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of one single list, containing file names. (`[[]]`).  
    - Index 0: The list of known files.  
- `fate`: Object of chapter ID (zfilled to string of length 3) and data pairs. If the element hasn't been updated, the data will be set to **0**. Otherwise, the data will be an array with the following format:  
    - General format: A list of five elements, four lists containing file names, and an optional string. (`[[], [], [], [], null]`).  
    - Index 0: The list of known files for base fates.  
    - Index 1: The list of known files for uncap fates.  
    - Index 2: The list of known files for transcendence fates.  
    - Index 3: The list of known files for other fates (cross, etc...).  
    - Index 4: The related character id.  
- `premium`: Object listing element IDs obtained via the gachas, along with character/weapon associations.  

# Skycompass  
Skycompass files can be accessed with the following URLs:  
- Main characters Classes and Outfits: `https://media.skycompass.io/assets/customizes/jobs/1138x1138/ID_GENDER.png` where `ID` is a class ID and `GENDER` can be **0** (Gran) or **1** (Djeeta).  
- Characters and Outfits: `https://media.skycompass.io/assets/customizes/characters/1138x1138/ID_UNCAP.png` where `ID` is a character ID and `UNCAP` can be an uncap ID (`01`) or bonus pose ID (`81`).  
- Summons: `https://media.skycompass.io/assets/archives/summons/ID/detail_l.png` where `ID` is a summon ID. No arts exist for summon uncaps.  
- Event: `https://media.skycompass.io/assets/archives/events/THUMBNAIL/image/NUM_free.png` where `THUMBNAIL` is an event **Thumbnail** ID and **NUM** is a number, as found in the `events` object at index **20**. The numbers are sequential.  
  
No skycompass arts exist for Collaboration/Tie-In related elements.  