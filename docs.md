# General Informations  
- GBFAL is a static web page. No API is available.  
- If you want to put a link towards GBFAL for a specific element on your website, use `https://mizagbf.github.io/GBFAL/?id=ID` where `ID` is the element ID on GBFAL.  
- Some elements have a prefix before the id, like events: [https://mizagbf.github.io/GBFAL/?id=q131201](https://mizagbf.github.io/GBFAL/?id=q131201)  
- If you want to reuse GBFAL data for your own purpose, you can download the `json/data.json` file from `https://raw.githubusercontent.com/MizaGBF/GBFAL/main/json/data.json`.  
  
# json/data.json Breakdown  
- The file is a big JSON Object. If possible, do not reload it. You can instead check the timestamp in `json/changelog.json` to check when it has been modified for the last time.  
- The following informations might be inaccurate. I'll try to keep it up to date as much as possible. In doubt, double check with `updater.py` content.  
  
### File Path  
URLs follow the following format:  
`ENDPOINT/LANG/ASSET_TYPE/PATH`  
where:  
- `ENDPOINT`: Can be `https://granbluefantasy.jp` (not recommended because of latency) or the CDN mirror `https://prd-game-a-granbluefantasy.akamaized.net/`.  
- `LANG`: Either `assets_en` (for English) or `assets` (for Japanese). Note that `json/data.json` is only updated with English files. In case of differences between both versions, some files might be missing.  
- `ASSET_TYPE`: Either `img` (for Image files), `sound` (for Sound files), `js` (for Javascript files) and more not documented here.  
- `PATH`: The remaining path towards the resource. For example: [img/sp/assets/npc/zoom/3040068000_01.png](https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/zoom/3040068000_01.png).  
  
### json/data.json content  
The JSON is made to be compact while retaining readability as much as possible.  
The file is also `utf-8` encoded (`\u` isn't used).  
```jsonc
{
"version":5, // The data.json format version. A change in this number means a major change happened.
"uncap_queue":[ // The list of pending elements with upcoming uncaps (here, 3040161000)
"3040161000"
],
"valentines":{ // Object of elements with valentine/white day scene arts. The 0 is unused.
"3040001000":0
},
"characters":{ // Object of playable character elements
"3020000000":[["npc_3020000000_01.png","npc_3020000000_02.png"],[],["nsp_3020000000_01.png","nsp_3020000000_02.png"],[],[],["3020000000_01","3020000000_02"],["3020000000_01","3020000000_02"],["","_shadow"],["_v_001","_v_002","_v_003","_v_004","_v_005a","_v_005b"],[]]
// In this example, character 3020000000. Content is:
// 0. Spritesheets. Path: `sp/cjs/FILE.png`.
// 1. Attack sheets (effects playing during auto attacks). Path: `sp/cjs/FILE.png`.
// 2. Charge Attack sheets. Path: `sp/cjs/FILE.png`.
// 3. AOE Skill sheets. Path: `sp/cjs/FILE.png`.
// 4. Targeted Skill sheets. Path: `sp/cjs/FILE.png`.
// 5. General files. Used for a lot of them (like portraits) and will contain uncap, gender variations and the like.
// 6. SD files  (as seen on the outfit selection screen). Path: `sp/assets/npc/sd/FILE.png`. Usable instead of General files if you don't want variations.
// 7. Scene file suffixes. Possible paths. `sp/quest/scene/character/body/ID_SUFFIX.png` (used in cutscenes) or`sp/raid/navi_face/ID_SUFFIX.png` (portrait used in battles, when characters talk). A file being in this list means either or both of those paths are valid.
// 8. Voice file suffixes. Path: `voice/ID_SUFFIX.mp3`.
// 9. MyPage animation sheets. Path: `sp/cjs/FILE.png`.
},
"partners":{ // Object of temporary event battle characters
"3820005000":[[],[],[],[],[],["3820005000_01","3820005000_02"]]
// The format is indentical to characters, except it stops at index 5 included.
},
"summons": // Object of summons
{
"2030000000":[["2030000000"],["summon_2030000000_01_attack_e.png","summon_2030000000_01_attack_a.png","summon_2030000000_01_attack_b.png","summon_2030000000_01_attack_c.png","summon_2030000000_01_attack_d.png"],["summon_2030000000_01_damage.png"],[]]
// In this example, summon 2030000000. Content is:
// 0. General files. General files. Used for a lot of them (like portraits) and will contain uncap variations and the like.
// 1. Summon call sheets. Path: `sp/cjs/FILE.png`.
// 2. Damage sheets (effects played after the call). Path: `sp/cjs/FILE.png`.
// 3. MyPage animation sheets. Path: `sp/cjs/FILE.png`.
},
"weapons": // Object of weapons
{
"1040000000":[["1040000000"],[],["sp_1040000000_0_a.png","sp_1040000000_0_b.png","sp_1040000000_1_a.png","sp_1040000000_1_b.png"]]
// In this example, summon 1040000000. Content is:
// 0. General files. General files. Used for a lot of them (like portraits).
// 1. Attack sheets (effects playing during auto attacks). Path: `sp/cjs/FILE.png`.
// 2. Charage Attack sheets. Path: `sp/cjs/FILE.png`.
},
"shields": // Object of shields
{
"4002":[["4002"]]
// In this example, shield 4002. Content is:
// Currently, only one list of one file, which should match the ID.
},
"manaturas": // Object of shields
{
"0001":[["1"]]
// In this example, manatura 1 (zero-padded to length 4). Content is:
// Currently, only one list of one file, which should match the ID without the padding.
},
"enemies": // Object of enemies
"1200011":[["1200011"],["enemy_1200011_a.png","enemy_1200011_b.png"],[],[],["esp_1200011_02.png"],[]]
// In this example, enemy 1200011. Content is:
// 0. General files. Used for icons seen near the HP bar or before joining the battle.
// 1. Spritesheets. Path: `sp/cjs/FILE.png`.
// 2. Appear sheets (the animation playing with the boss name at the start of the battle). An enemy can have multiples. Path: `sp/cjs/FILE.png`.
// 3. Attack sheets (effects playing during auto attacks). Path: `sp/cjs/FILE.png`.
// 4. Single target charge attack sheets. Path: `sp/cjs/FILE.png`.
// 5. AOE charge attack sheets. Path: `sp/cjs/FILE.png`.
},
"skins": // Object of character outfits
{
// EXACT SAME format as for "characters"
},
"jobs": // Object of main character classes and outfits
{
"370201":[["370201"],["370201_01"],["370201_me_0_01","370201_me_1_01"],["370201_me_0_01","370201_me_1_01"],["370201_me_0_01","370201_me_1_01"],["370201"],["me"],["kjb_me_0_01.png","kjb_me_1_01.png"],["phit_1040610200.png"],["sp_1040610200_0_s2.png","sp_1040610200_1_s2.png"],[],[],[],[]]
// In this example, element 370201. Content is:
// 0: Base file. Used for icons (`sp/ui/icon/job/FILE.png`) and texts (`sp/ui/job_name/job_list/FILE.png`, ...).
// 1. Other Base file. Used for inventory portraits and such.
// 2. Detail portrait files.
// 3. Other detail portrait files. Similar to Index 2.
// 4. More files. Those will include some color swap/helmetless files.
// 5. Color swap/helmetless SD sprite files.
// 6. Main hand ID strings. For internal use only.
// 7. Spritesheets. Path. `sp/cjs/FILE.png`.
// 8. Attack sheets (effects playing during auto attacks). Path. `sp/cjs/FILE.png`.
// 9. Charage attack sheets. Path. `sp/cjs/FILE.png`.
// 10. AOE skill sheets. Path. `sp/cjs/FILE.png`.
// 11. Single Target skill sheets. Path. `sp/cjs/FILE.png`.
// 12. Unlock animation sheets. Path. `sp/cjs/FILE.png`.
// 13. MyPage animation sheets. Path. `sp/cjs/FILE.png`. 
},
"job_wpn":{ // For internal use. Object of matching weapons and classes.
// Outfits use dedicated weapons for their animations.
"1040610200":"370201"
// In this example, class/outfit 370201 uses weapon 1040610200
},
"job_key":{ // For internal use. Object of matching classes ID and secondary ID.
"ogr":"160201"
// In this example, class/outfit 370201 is matched with the second ID ogr. It's always 3 letter and evoking the class name/character (Without checking, this is probably Ogre)
},
"npcs": // Object of scene NPCS
{
"3990000000":[true,["","_battle","_nalhe","_nalhe_hood","_nalhe_hood_shadow","_nalhe_hood_up","_nalhe_light","_nalhe_shout","_valentine"],["_v_033","_v_034","_v_036","_v_037","_v_042","_v_043","_v_073","_v_078","_v_101","_v_111","_v_114","_v_118"]]
// In this example, NPC 3990000000. Content is:
// 0. The boolean indicates if the NPC has a journal thumbnail.
// 1. Scene file suffixes. Possible paths. `sp/quest/scene/character/body/ID_SUFFIX.png` (used in cutscenes) or`sp/raid/navi_face/ID_SUFFIX.png` (portrait used in battles, when characters talk). A file being in this list means either or both of those paths are valid.
// 2. Voice file suffixes. Path. `voice/ID_SUFFIX.mp3`.
},
"profile_npcs": // Object of profile card npcs. Value is unused.
{
"2":0
// In this example, NPC 2 exists
},
"profile_stickers": // Object of profile card stickers. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"profile_arts": // Object of profile card arts. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"profile_bgs": // Object of profile card backgrounds. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"arca3_maps": // Object of Evoking Solomonis maps. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"arca3_specials": // Object of Evoking Solomonis map events. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"background": // Object of in-game backgrounds (battle, crew, ...).
{
"e015r":[["e015r_1","e015r_1_a","e015r_2","e015r_2_a","e015r_3","e015r_3_a"]]
// In this example, background e015r. Content is:
// 0: The list of background files. Possible paths are `sp/guild/custom/bg/FILE.png` for MAIN backgrounds and `sp/raid/bg/FILE.jpg` for everything else.
},
"mypage_bg": // Object of Home page backgrounds. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"story_memory": // Object of Main Story Compilation Arts. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"title": // Object of Title Screen Arts. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"stamp": // Object of Chat Stamps. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"sky_title": // Object of Arts from the Sky Compass Gallery. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"suptix": // Object of Surprise Draw Ticket banners. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"lookup": // Object of string lookup for search purpose. See the next category.
{
"3050000000":"/w Lyria_(NPC) /n lyria /b human /s female /y ルリア nao tōyama 東山奈央 2014-03-10 /! /1 /2"
},
"evt_lookup": // Object of event string lookup for search purpose.
{
"arcarum the world beyond":["160916","arca00","arca01","arca02","arca03"]
// In this example, these events match to the name "arcarum the world beyond"
},
"events": // Object of events
{
"141130":[6,"Defender's Oath","70190","11001",[],[],["scene_evt141130_01.png","scene_evt141130_02.png","scene_evt141130_03.png"],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[1,2,3,4,5,6,7,8,9,10,11,12]]
// In this example, event 141130. The ID usually matches the start date. Content is:
// 0. For internal use, the estimated number of chapters. -1 means no chapters, 0 means unknown.
// 1. A string, the event name. Empty string if not set.
// 2. A string, the event thumbnail ID. Set to **null** if not set.
// 3. A string, the side story ID. Set to **null** if not set.
// 4. Opening chapter files with the file extension.
// 5. Ending chapter files with the file extension.
// 6. Other files with the file extension.
// 7 to 26. Numbered chapter files with the file extension (**1** to **20**).
// 27. Skycompass files.
},
"skills": // Object of character skills
{
"0105":[["105_1"]]
// In this example, skill 105 (zero-padded to length 4). Content is:
// 0. One known file variation of this skill. Not all of them are stored. This index is mostly to track which skills exist. Possible files follow the following format: `sp/ui/icon/ability/m/ID.png` or `sp/ui/icon/ability/m/ID_N.png` where `N` can be 1 to 5.
},
"subskills": // Object of subskills (like Grand Wamdus's first skill)
{
// EXACT SAME format as for "profile_npcs"
},
"buffs": // Object of buff/debuff icons
{
"7000":[["7000"],["","1","2","3","4","5"]]
// In this example, buff/debuff 7000. Content is:
// 0. The first part of the filename. It should matches the ID without leading zeros.
// 1. Valid suffixes for this buff/debuff. Resulting path: `sp/ui/icon/status/x64/status_ZID_suffix.png` where `ZID` is the string at Index 0.
},
"eventthumb": // For internal use. Object of event thumbnails. Value is unused.
{
// EXACT SAME format as for "profile_npcs"
},
"free": // Object of Free quest scene arts
{
// EXACT SAME format as for "story0" and "story1" (See below)
},
"story0": // Object of First MSQ scene arts. 
{
"006":[["scene_cp6_1.png","scene_cp6_2.png"]]
// In this example, chapter 6. ID is zero-padded to length 3. Recap IDs use `rNN` and compilation IDS use `cNN`, where `N` is a digit. Content is:
// 0. The list of known files. 
},
"story1": // Object of Second MSQ scene arts
{
// EXACT SAME format as for "free" and "story0" (See above)
},
"fate": // Object of Fate episodes
{
"0900":[["scene_chr900_01.png","scene_chr900_02.png","scene_chr900_03.png","scene_chr900_04.png","scene_chr900_05.png","scene_chr900_05_a.png","scene_chr900_06.png","scene_chr900_06_a.png"],[],[],[],"3040557000"]
// In this example, Fate episode 900. Content is:
// 0. The list of known files for base fates.
// 1. The list of known files for uncap fates.
// 2. The list of known files for transcendence fates.
// 3. The list of known files for other fates (cross, etc...).
// 4. The related character or summon ID.
},
"premium": // For internal use. Object of character/weapon pairs obtainable in the Gacha.
{
"3040284000":"1040312800"
},
"npc_replace": // For internal use. Object of ID replacement for some NPC scene files
{
"3991093000":"fpae5yilyd"
// In this example, the scene file of 3991093000 will use fpae5yilyd instead
// It's used for some old collaborations, possibly to protect them from datamining.
}
}
```  
  
# Lookup  
  
The format is:  
```console
/f [Boss Type] /w [Relation] /w [Wiki_path] /e [Element] /a [Rarity] /n [Name] /k [Outfit_name] /m Class /c [Series] /b [Races] /s [Gender] /t [Type] /p [Proficiency] /y [Name JP] [Voice Actor] [Voice Actor JP] [Release Date] ... [Additional_tags]
```  
They are delimited by special markers using a `/`.
  
- `[Boss Type]` is the element's boss type tag. Only for enemies. Names are arbitrary and not official, and automatically added by the GBFAL updater.
- `[Relation]` is the relation to another element. Example: `/x gran /n djeeta`. It should always be at the start.  
- `/w [Wiki_path]` indicates this element has a wiki page and its path. Example: /w [Bahamut](https://gbf.wiki/Bahamut). It should always be at the start.  
- `[Element]` can be either `fire`, `water`, `earth`, `wind`, `light`, `dark`, `any`. It should always be before the name.  
- `[Rarity]` can be either `n`, `r`, `sr`, `ssr`. It should always be before the name  
- `[Name]` is the element's name in english.  
- `[Outfit_name]` is the element's outfit name in english.  
- `[Series]` is the element's series, such as `summer`, `yukata`, `collab`, etc...  
- `[Races]` are the element's races, such as `human`, `erune`, etc... Other is set to `unknown`, to not confuse with the other gender.  
- `[Type]` is the element's type (`balanced`, etc... for characters, `sword`, etc... for weapons).
- `[Proficiency]` are a character's proficiency (`sword`, etc...).
- `[Gender]` is the element's gender, either `male`, `female` or `other`.  
- `[Name JP]` is the element's name in japanese.  
- `[Voice Actor]` is the element's Voice Actor's name in english.  
- `[Voice Actor JP]` is the element's Voice Actor's name in japanese.  
- `[Release Date]` is the element's Release date sourced from the wiki.  
- `[Additional Tags]` are special tags used for search purpose. There are currently: `/$` (for elements with invalid or without lookup entries), `/!` (for elements with voice files), `/!!` (for elements with only voice files), `/!` (for younger appearances of elements), `/1` (for elements appearing in Versus / Rising) and `/2` (for elements appearing Relink / Ragnarok). Additional tags should always be at the end.
- `/%` can be used to set multiple names.  

# Skycompass  
Skycompass files can be accessed with the following URLs:  
- Main characters Classes and Outfits: `https://media.skycompass.io/assets/customizes/jobs/1138x1138/ID_GENDER.png` where `ID` is a class ID and `GENDER` can be **0** (Gran) or **1** (Djeeta).  
- Characters and Outfits: `https://media.skycompass.io/assets/customizes/characters/1138x1138/ID_UNCAP.png` where `ID` is a character ID and `UNCAP` can be an uncap ID (`01`) or bonus pose ID (`81`).  
- Summons: `https://media.skycompass.io/assets/archives/summons/ID/detail_l.png` where `ID` is a summon ID. No arts exist for summon uncaps.  
- Event: `https://media.skycompass.io/assets/archives/events/THUMBNAIL/image/NUM_free.png` where `THUMBNAIL` is an event **Thumbnail** ID and **NUM** is a number, as found in the `events` object at index **20**. The numbers are sequential.  
  
No skycompass arts exist for Collaboration/Tie-In related elements.  