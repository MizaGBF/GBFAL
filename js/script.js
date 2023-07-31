/* sky compass notes (for posterity)

Leader: https://media.skycompass.io/assets/customizes/jobs/1138x1138/ID_GENDER.png
Character: https://media.skycompass.io/assets/customizes/characters/1138x1138/ID_UNCAP.png
Summon: https://media.skycompass.io/assets/archives/summons/ID/detail_l.png
Event: https://media.skycompass.io/assets/archives/events/ID/image/NUM_free.png

*/

// endpoints
var endpoints = [
    "https://prd-game-a-granbluefantasy.akamaized.net/",
    "https://prd-game-a1-granbluefantasy.akamaized.net/",
    "https://prd-game-a2-granbluefantasy.akamaized.net/",
    "https://prd-game-a3-granbluefantasy.akamaized.net/",
    "https://prd-game-a4-granbluefantasy.akamaized.net/",
    "https://prd-game-a5-granbluefantasy.akamaized.net/"
];
var main_endp_count = -1;
var language = "assets_en/"; // change to "assets/" for japanese

// tracking last id loaded
var last_id = null;
var last_style = null;

// result div
var result_area = null;

// constant, list of null characters/skins
var null_characters = [
    "3030182000", "3710092000", "3710139000", "3710078000", "3710105000", "3710083000", "3020072000", "3710184000"
];
// add id here to disable some elements
var blacklist = [

];

var index = {}; // data index (loaded from data.json)
var searchHistory = []; // search history
var searchResults = []; // search results
var bookmarks = []; // bookmarks
var timestamp = Date.now(); // timestamp (loaded from changelog.json)
var relations = {}; // relations of loaded elements
var updated = []; // list of recently updated elements (loaded from changelog.json)
var intervals = []; // on screen notifications
var typingTimer; // typing timer timeout
var audio = null; // last played audio

function getMainEndpoint() // return one of the endpoint, one after the other (to benefit from the sharding)
{
    main_endp_count = (main_endp_count + 1) % endpoints.length;
    return endpoints[main_endp_count];
}

function getIndexEndpoint(index) // return one of the endpoint based on the index value passed
{
    return endpoints[index % endpoints.length];
}

function typying() // clear timeout when typying (onkeydown event)
{
    clearTimeout(typingTimer);
}

function filter() // called by the search filter (onkeyup event)
{
    clearTimeout(typingTimer);
    typingTimer = setTimeout(function(){ // set a timeout of 1s before executing lookup
        lookup(document.getElementById('filter').value.trim().toLowerCase());
    }, 1000);
}

function init() // entry point, called by body onload
{
    getJSON("json/changelog.json?" + timestamp, initChangelog, initChangelog, null); // load changelog
}

function initChangelog(unused)
{
    try{ // load content of changelog.json
        let json = JSON.parse(this.response);
        if(json.hasOwnProperty("new")) // set updated
            updated = json["new"].reverse();
        let date = (new Date(json.timestamp)).toISOString();
        document.getElementById('timestamp').innerHTML += " " + date.split('T')[0] + " " + date.split('T')[1].split(':').slice(0, 2).join(':') + " UTC";
        timestamp = json.timestamp; // set timestamp
    } catch(err) {
        document.getElementById('timestamp').innerHTML = "";
    }
    // load other json
    getJSON("json/relation.json?" + timestamp, initRelation, function(unused){}, null);
    getJSON("json/data.json?" + timestamp, initIndex, initIndex, null);
}

function swap(json)  // swap keys and values from an object
{
    var ret = {};
    for(var key in json)
    {
        ret[json[key]] = key;
    }
    return ret;
}

function initIndex(unused) // load data.json
{
    try{
        index = JSON.parse(this.response); // read
        index["lookup_reverse"] = swap(index["lookup"]); // create reversed lookup
        result_area = document.getElementById('resultarea'); // set result_area
        let params = new URLSearchParams(window.location.search); // process url param if any
        let id = params.get("id");
        if(updated.length > 0) // init Updated list
        {
            let newarea = document.getElementById('updated');
            newarea.parentNode.style.display = null;
            updateDynamicList(newarea, updated);
        }
        toggleBookmark(null, null); // init bookmark
        updateHistory(null, 0); // init history
        if(id != null) lookup(id); // lookup if id param is set
    } catch(err) {
        getJSON("json/data.json?" + timestamp, initIndex, initIndex, null); // try again
    }
}

function initRelation(unused) // load relation.json
{
    try{
        relations = JSON.parse(this.response);
    } catch(err) {
        
    }
}

function updateQuery(id) // update url parameters
{
    let params = new URLSearchParams(window.location.search);
    let current_id = params.get("id");
    if(current_id != id)
    {
        params.set("id", id);
        let newRelativePathQuery = window.location.pathname + '?' + params.toString();
        history.pushState(null, '', newRelativePathQuery);
    }
}

function getJSON(url, callback, err_callback, id) { // generic function to request a file. id is a parameter which can be passed to callbacks
    var xhr = new XMLHttpRequest();
    xhr.ontimeout = function () {
        err_callback.apply(xhr);
    };
    xhr.onload = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                callback.apply(xhr, [id]);
            } else {
                err_callback.apply(xhr, [id]);
            }
        }
    };
    xhr.open("GET", url, true);
    xhr.timeout = 1000;
    xhr.send(null);
}

// =================================================================================================
// main stuff
function loadIndexed(id, obj, indexed=true) // load an element from data.json
{
    let search_type;
    switch(id.length)
    {
        case 10:
        case 14:
            switch(id[0])
            {
                case '1':
                    newArea("Weapon", id, true, indexed);
                    search_type = 1;
                    break;
                case '2':
                    newArea("Summon", id, true, indexed);
                    search_type = 2;
                    break;
                case '3':
                    switch(id[1])
                    {
                        case '9':
                        case '5':
                            newArea("NPC", id, true, indexed);
                            search_type = 5;
                            break;
                        case '8':
                            newArea("Partner", id, false, indexed);
                            search_type = 6;
                            break;
                        default:
                            newArea("Character", id, true, indexed);
                            search_type = 3;
                            break;
                    }
                    break;
                default:
                    return;
            };
            last_id = id;
            updateQuery(id);
            break;
        case 7:
            newArea("Enemy", id, false, indexed);
            search_type = 4;
            updateQuery("e"+id);
            break;
        case 6:
            newArea("Main Character", id, true, (obj[7].length != 0) && indexed);
            search_type = 0;
            updateQuery(id);
            break;
        default:
            return;
    }
    if(indexed)
    {
        updateHistory(id, search_type);
        favButton(true, id, search_type);
    }
    updateRelated(id);
    let assets = null;
    let skycompass = null;
    let mc_skycompass = false;
    let npcdata = null;
    let files = null;
    let sounds = null;
    let melee = false;
    switch(search_type)
    {
        case 4: // enemies
            assets = [
                ["Big Icon", "sp/assets/enemy/m/", "png", "img/", 0, false, false],
                ["Small Icon", "sp/assets/enemy/s/", "png", "img/", 0, false, false],
                ["Sprite Sheets", "sp/cjs/", "png", "img_low/", 1, false, false],
                ["Raid Appear Sheets", "sp/cjs/", "png", "img_low/", 2, false, false],
                ["Attack Effect Sheets", "sp/cjs/", "png", "img_low/", 3, false, false],
                ["Charge Attack Sheets", "sp/cjs/", "png", "img_low/", 4, false, false],
                ["AOE Charge Attack Sheets", "sp/cjs/", "png", "img_low/", 5, false, false]
            ];
            break;
        case 6: // partners
            assets = [
                ["Party Select Portraits", "sp/assets/npc/quest/", "jpg", "img/", 5, false, false],
                ["Raid Portraits", "sp/assets/npc/raid_normal/", "jpg", "img/", 5, false, true],
                ["Charge Attack Cutins", "sp/assets/npc/cutin_special/", "jpg", "img_low/", 5, false, false],
                ["Chain Cutins", "sp/assets/npc/raid_chain/", "jpg", "img_low/", 5, false, false],
                ["Character Sheets", "sp/cjs/", "png", "img_low/", 0, false, false],
                ["Attack Effect Sheets", "sp/cjs/", "png", "img_low/", 1, false, false],
                ["Charge Attack Sheets", "sp/cjs/", "png", "img_low/", 2, false, false],
                ["AOE Skill Sheets", "sp/cjs/", "png", "img_low/", 3, false, false],
                ["Single Target Skill Sheets", "sp/cjs/", "png", "img_low/", 4, false, false]
            ];
            break;
        case 3: // characters / skins
            assets = [
                ["Main Arts", "sp/assets/npc/zoom/", "png", "img_low/", 5, true, false], // index, skycompass, side form
                ["Journal Arts", "sp/assets/npc/b/", "png", "img_low/", 5, false, false],
                ["Gacha Arts", "sp/assets/npc/gacha/", "png", "img_low/", 6, false, false],
                ["News Art", "sp/banner/notice/update_char_", "png", "img_low/", 6, false, false],
                ["Pose News Arts", "sp/assets/npc/add_pose/", "png", "img_low/", 6, false, false],
                ["Inventory Portraits", "sp/assets/npc/m/", "jpg", "img_low/", 5, false, false],
                ["Square Portraits", "sp/assets/npc/s/", "jpg", "img_low/", 5, false, false],
                ["Party Portraits", "sp/assets/npc/f/", "jpg", "img_low/", 5, false, false],
                ["Popup Portraits", "sp/assets/npc/qm/", "png", "img_mid/", 5, false, false],
                ["Balloon Portraits", "sp/gacha/assets/balloon_s/", "png", "img/", 6, false, false],
                ["Party Select Portraits", "sp/assets/npc/quest/", "jpg", "img/", 5, false, false],
                ["Tower Portraits", "sp/assets/npc/t/", "png", "img_low/", 5, false, false],
                ["Detail Banners", "sp/assets/npc/detail/", "png", "img_low/", 5, false, false],
                ["Sprites", "sp/assets/npc/sd/", "png", "img/", 6, false, false],
                ["Raid Portraits", "sp/assets/npc/raid_normal/", "jpg", "img/", 5, false, true],
                ["Twitter Arts", "sp/assets/npc/sns/", "jpg", "img_low/", 5, false, false],
                ["Charge Attack Cutins", "sp/assets/npc/cutin_special/", "jpg", "img_low/", 5, false, false],
                ["Chain Cutins", "sp/assets/npc/raid_chain/", "jpg", "img_low/", 5, false, false],
                ["Character Sheets", "sp/cjs/", "png", "img_low/", 0, false, false],
                ["Attack Effect Sheets", "sp/cjs/", "png", "img_low/", 1, false, false],
                ["Charge Attack Sheets", "sp/cjs/", "png", "img_low/", 2, false, false],
                ["AOE Skill Sheets", "sp/cjs/", "png", "img_low/", 3, false, false],
                ["Single Target Skill Sheets", "sp/cjs/", "png", "img_low/", 4, false, false]
            ];
            skycompass = ["https://media.skycompass.io/assets/customizes/characters/1138x1138/", ".png", true];
            npcdata = obj[7];
            sounds = obj[8];
            break;
        case 5: // npcs
            assets = [
                ["Main Arts", "sp/assets/npc/zoom/", "png", "img_low/", -1, false, false], // index, skycompass, side form
                ["Journal Arts", "sp/assets/npc/b/", "png", "img_low/", -1, false, false],
                ["Inventory Portraits", "sp/assets/npc/m/", "jpg", "img_low/", -1, false, false]
            ];
            npcdata = obj[1];
            sounds = obj[2];
            files = [id, id + "_01"];
            break;
        case 2: // summons
            assets = [
                ["Main Arts", "sp/assets/summon/b/", "png", "img_low/", 0, true, false], // index, skycompass, side form
                ["Home Arts", "sp/assets/summon/my/", "png", "img_low/", 0, false, false],
                ["Gacha Art", "sp/assets/summon/g/", "png", "img_low/", 0, false, false],
                ["Gacha Header", "sp/gacha/header/", "png", "img_low/", 0, false, false],
                ["Detail Arts", "sp/assets/summon/detail/", "png", "img_low/", 0, false, false],
                ["Inventory Portraits", "sp/assets/summon/m/", "jpg", "img_low/", 0, false, false],
                ["Square Portraits", "sp/assets/summon/s/", "jpg", "img_low/", 0, false, false],
                ["Main Summon Portraits", "sp/assets/summon/party_main/", "jpg", "img_low/", 0, false, false],
                ["Sub Summon Portraits", "sp/assets/summon/party_sub/", "jpg", "img_low/", 0, false, false],
                ["Raid Portraits", "sp/assets/summon/raid_normal/", "jpg", "img/", 0, false, false],
                ["Result Portraits", "sp/assets/summon/btn/", "png", "img/", 0, false, false],
                ["Quest Portraits", "sp/assets/summon/qm/", "png", "img/", 0, false, false],
                ["Summon Call Sheets", "sp/cjs/", "png", "img_low/", 1, false, false],
                ["Summon Damage Sheets", "sp/cjs/", "png", "img_low/", 2, false, false]
            ];
            skycompass = ["https://media.skycompass.io/assets/archives/summons/", "/detail_l.png", false];
            break;
        case 1: // weapons{
            assets = [
                ["Main Arts", "sp/assets/weapon/b/", "png", "img_low/", 0, false, false], // index, skycompass, side form
                ["Gacha Art", "sp/assets/weapon/g/", "png", "img_low/", 0, false, false],
                ["Gacha Cover", "sp/gacha/cjs_cover/", "png", "img_mid/", 0, false, false],
                ["Gacha Header", "sp/gacha/header/", "png", "img_low/", 0, false, false],
                ["Inventory Portraits", "sp/assets/weapon/m/", "jpg", "img_low/", 0, false, false],
                ["Square Portraits", "sp/assets/weapon/s/", "jpg", "img_low/", 0, false, false],
                ["Main Hand Portraits", "sp/assets/weapon/ls/", "jpg", "img_low/", 0, false, false],
                ["Battle Sprites", "sp/cjs/", "png", "img/", 0, false, false],
                ["Attack Effects", "sp/cjs/", "png", "img/", 1, false, false],
                ["Charge Attack Sheets", "sp/cjs/", "png", "img_low/", 2, false, false]
            ];
            melee = (id[4] == "6");
            break;
        case 0: // MC
            assets = [
                ["Job Icons", "sp/ui/icon/job/", "png", "img/", 0, false, false], // index, skycompass, side form
                ["Inventory Portraits", "sp/assets/leader/m/", "jpg", "img/", 1, false, false],
                ["Outfit Portraits", "sp/assets/leader/sd/m/", "jpg", "img/", 1, false, false],
                ["Outfit Description Arts", "sp/assets/leader/skin/", "png", "img_low/", 1, false, false],
                ["Home Arts", "sp/assets/leader/my/", "png", "img_low/", 3, true, false],
                ["Full Arts", "sp/assets/leader/job_change/", "png", "img_low/", 3, false, false],
                ["Outfit Preview Arts", "sp/assets/leader/skin/", "png", "img_low/", 3, false, false],
                ["Class Name Party Texts", "sp/ui/job_name/job_list/", "png", "img/", 0, false, false],
                ["Class Name Master Texts", "sp/assets/leader/job_name_ml/", "png", "img/", 0, false, false],
                ["Class Change Buttons", "sp/assets/leader/jlon/", "png", "img/", 2, false, false],
                ["Party Class Big Portraits", "sp/assets/leader/jobon_z/", "png", "img_low/", 3, false, false],
                ["Party Class Portraits", "sp/assets/leader/p/", "png", "img_low/", 3, false, false],
                ["Profile Portraits", "sp/assets/leader/pm/", "png", "img_low/", 3, false, false],
                ["Profile Board Portraits", "sp/assets/leader/talk/", "png", "img/", 3, false, false],
                ["Party Select Portraits", "sp/assets/leader/quest/", "jpg", "img/", 3, false, false],
                ["Tower Portraits", "sp/assets/leader/t/", "png", "img_low/", 3, false, false],
                ["Raid Portraits", "sp/assets/leader/raid_normal/", "jpg", "img/", 3, false, false],
                ["Result Portraits", "sp/assets/leader/btn/", "png", "img/", 3, false, false],
                ["Raid Log Portraits", "sp/assets/leader/raid_log/", "png", "img/", 3, false, false],
                ["Raid Result Portraits", "sp/assets/leader/result_ml/", "jpg", "img_low/", 3, false, false],
                ["Mastery Portraits", "sp/assets/leader/zenith/", "png", "img_low/", 2, false, false],
                ["Master Level Portraits", "sp/assets/leader/master_level/", "png", "img_low/", 2, false, false],
                ["Sprites", "sp/assets/leader/sd/", "png", "img/", 4, false, false],
                ["Character Sheets", "sp/cjs/", "png", "img_low/", 7, false, false],
                ["Attack Effects", "sp/cjs/", "png", "img/", 8, false, false],
                ["Charge Attack Sheets", "sp/cjs/", "png", "img_low/", 9, false, false]
            ];
            skycompass = ["https://media.skycompass.io/assets/customizes/jobs/1138x1138/", ".png", true];
            mc_skycompass = true;
            break;
    }
    if(assets != null)
    {
        for(let asset of assets)
        {
            files = (asset[4] == -1) ? files : obj[asset[4]]; // for npc
            if(files.length == 0) continue; // empty list
            // exceptions
            switch(asset[0])
            {
                case "Quest Portraits":
                    if(search_type == 2)
                        files = [files[0], files[0]+"_hard", files[0]+"_ex", files[0]+"_high"]; // summon quest icon
                    break;
                case "Gacha Cover": // gacha cover
                    files = [files[0]+"_1", files[0]+"_3"];
                    break;
                case "News Art": // character news art
                    files = [id];
                    break;
                case "Battle Sprites":
                    if(melee) // melee weapon sprites
                        files = [files[0]+"_1", files[0]+"_2"];
                    break;
            };
            
            let div = addResult(asset[0], asset[0], (indexed ? files.length : 0));
            for(let file of files)
            {
                if(!asset[6] && (file.endsWith('_f') || file.endsWith('_f1'))) continue;
                let img = document.createElement("img");
                let ref = document.createElement('a');
                if(file.endsWith(".png") || file.endsWith(".jpg"))
                    img.src = getMainEndpoint() + language + asset[3] + asset[1] + file;
                else
                    img.src = getMainEndpoint() + language + asset[3] + asset[1] + file + "." + asset[2];
                ref.setAttribute('href', img.src.replace("img_low", "img"));
                img.classList.add("loading");
                img.setAttribute('loading', 'lazy');
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                };
                img.onload = function() {
                    this.classList.remove("loading");
                    this.classList.add("asset");
                };
                div.appendChild(ref);
                ref.appendChild(img);
                if(skycompass != null && asset[5]) // skycompass
                {
                    img = document.createElement("img");
                    img.setAttribute('loading', 'lazy');
                    ref = document.createElement('a');
                    if(!skycompass[2])
                    {
                        if(file != obj[asset[4]][0]) continue;
                        ref.setAttribute('href', skycompass[0] + file.split('_')[0] + skycompass[1]);
                        img.src = skycompass[0] + file.split('_')[0] + skycompass[1];
                    }
                    else if(mc_skycompass)
                    {
                        ref.setAttribute('href', skycompass[0] + id + '_' + file.split('_')[2] + skycompass[1]);
                        img.src = skycompass[0] + id + '_' + file.split('_')[2] + skycompass[1];
                    }
                    else
                    {
                        ref.setAttribute('href', skycompass[0] + file + skycompass[1]);
                        img.src = skycompass[0] + file + skycompass[1];
                    }
                    img.classList.add("loading");
                    img.onerror = function() {
                        let result = this.parentNode.parentNode;
                        this.parentNode.remove();
                        this.remove();
                        if(result.childNodes.length <= 2) result.remove();
                    };
                    img.onload = function() {
                        this.classList.remove("loading");
                        this.classList.add("asset");
                        this.classList.add("skycompass");
                    };
                    div.appendChild(ref);
                    ref.appendChild(img);
                }
            }
        }
    }
    if(npcdata != null) // indexed npc data
    {
        assets = [
            ["Raid Bubble Arts", "sp/raid/navi_face/", "png", "img/"],
            ["Scene Arts", "sp/quest/scene/character/body/", "png", "img_low/"]
        ];
        for(let asset of assets)
        {
            if(npcdata.length == 0) continue;
            let div = addResult(asset[0], asset[0], (indexed ? npcdata.length : 0));
            for(let file of npcdata)
            {
                if(asset[0] == "Raid Bubble Arts" && file.endsWith('_up')) continue; // ignore those
                let img = document.createElement("img");
                let ref = document.createElement('a');
                img.src = getMainEndpoint() + language + asset[3] + asset[1] + id + file + "." + asset[2];
                ref.setAttribute('href', img.src.replace("img_low", "img"));
                img.classList.add("loading");
                img.setAttribute('loading', 'lazy');
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                };
                img.onload = function() {
                    this.classList.remove("loading");
                    this.classList.add("asset");
                };
                div.appendChild(ref);
                ref.appendChild(img);
            }
        }
    }
    if(sounds != null && sounds.length > 0) // indexed sounds data for characters
    {
        let sorted_sound = {"Generic":[]}
        let checks = {
            "": "Generic",
            "_v_": "Standard",
            "birthday": "Happy Birthday",
            "year": "Happy New Year",
            "alentine": "Valentine",
            "hite": "White Day",
            "alloween": "Halloween",
            "mas": "Christmas",
            "mypage": "My Page",
            "introduce": "Recruit",
            "formation": "Add to Party",
            "evolution": "Evolution",
            "zenith_up": "Extended Mastery",
            "archive": "Journal",
            "cutin": "Battle",
            "attack": "Attack",
            "kill": "Enemy Defeated",
            "ability_them": "Offensive Skill",
            "ability_us": "Buff Skill",
            "ready": "CA Ready",
            "mortal": "Charge Attack",
            "chain": "Chain Burst Banter",
            "damage": "Damaged",
            "healed": "Healed",
            "power_down": "Debuffed",
            "dying": "Dying",
            "lose": "K.O.",
            "win": "Win",
            "player": "To Player",
            "pair": "Banter"
        }
        for(let sound of sounds) // sorting
        {
            let found = false;
            for(const [k, v] of Object.entries(checks))
            {
                if(k == "") continue;
                if(sound.includes(k))
                {
                    found = true;
                    if(!(v in sorted_sound)) sorted_sound[v] = [];
                    sorted_sound[v].push(sound)
                    break;
                }
            }
            if(!found) sorted_sound["Generic"].push(sound);
        }
        if(sorted_sound["Generic"].length == 0) delete sorted_sound["Generic"];
        for(const [k, v] of Object.entries(checks))
        {
            if(v in sorted_sound)
            {
                let div = sorted_sound[v].length > 15 ? addVoiceResult(v, v + " Voices", sorted_sound[v].length) : addResult(v, v + " Voices");
                for(let sound of sorted_sound[v])
                {
                    let elem = document.createElement("div");
                    elem.classList.add("sound-file");
                    elem.classList.add("clickable");
                    let s = sound.substring(1);
                    switch(s.substring(0, 3))
                    {
                        case "02_": s = "4★_" + s.substring(3); break;
                        case "03_": s = "5★_" + s.substring(3); break;
                        case "04_": s = "6★_" + s.substring(3); break;
                        case "05_": s = "7★_" + s.substring(3); break;
                        default: s = "0★_" + s; break;
                    }
                    s = s.split('_');
                    let isCB = false;
                    for(let i = 0; i < s.length; ++i)
                    {
                        switch(s[i])
                        {
                            case "chain1": elem.appendChild(document.createTextNode("Fire CB")); isCB = true; break;
                            case "chain2": elem.appendChild(document.createTextNode("Water CB")); isCB = true; break;
                            case "chain3": elem.appendChild(document.createTextNode("Earth CB")); isCB = true; break;
                            case "chain4": elem.appendChild(document.createTextNode("Wind CB")); isCB = true; break;
                            case "chain5": elem.appendChild(document.createTextNode("Light CB")); isCB = true; break;
                            case "chain6": elem.appendChild(document.createTextNode("Dark CB")); isCB = true; break;
                            case "s1": elem.appendChild(document.createTextNode("Scene 1")); break;
                            case "s2": elem.appendChild(document.createTextNode("Scene 2")); break;
                            case "s3": elem.appendChild(document.createTextNode("Scene 3")); break;
                            case "s4": elem.appendChild(document.createTextNode("Scene 4")); break;
                            case "s5": elem.appendChild(document.createTextNode("Scene 5")); break;
                            case "s6": elem.appendChild(document.createTextNode("Scene 6")); break;
                            default:
                                if(isCB) elem.appendChild(document.createTextNode(s[i] + " chains"));
                                else elem.appendChild(document.createTextNode(s[i]));
                                break;
                        }
                        elem.appendChild(document.createElement('br'));
                    }
                    elem.onclick = function() {
                        if(audio != null) audio.pause();
                        audio = new Audio("https://prd-game-a5-granbluefantasy.akamaized.net/" + language + "sound/voice/" + id + sound + ".mp3");
                        audio.play();
                    };
                    let a = document.createElement("a");
                    a.href = "https://prd-game-a5-granbluefantasy.akamaized.net/" + language + "sound/voice/" + id + sound + ".mp3";
                    a.classList.add("sound-link");
                    a.onclick = function(event) {
                        event.stopPropagation();
                    };
                    elem.appendChild(a);
                    div.appendChild(elem);
                }
            }
        }
    }
}

function addVoiceResult(identifier, name, file_count) // add voice elements for characters
{
    let div = document.createElement("div");
    div.classList.add("result");
    if(identifier == "Generic" || identifier == "Standard")
    {
        let tooltip = document.createElement("div");
        tooltip.classList.add("tooltip");
        let img = document.createElement("img");
        img.src = "assets/ui/question.png";
        tooltip.appendChild(img);
        let span = document.createElement("span");
        span.classList.add("tooltiptext");
        span.innerHTML = "For older units, a lot of files might be regrouped under this category";
        tooltip.appendChild(span);
        div.appendChild(tooltip);
    }
    div.setAttribute("data-id", identifier);
    div.appendChild(document.createTextNode(name));
    div.appendChild(document.createElement("br"));
    let details = document.createElement("details");
    let summary = document.createElement("summary");
    summary.innerHTML = file_count + " Files";
    details.appendChild(summary);
    div.appendChild(details);
    result_area.appendChild(div);
    return details;
}

function loadUnindexed(id)// minimal load of an element not indexed or not fully indexed, this is only intended as a cheap placeholder
{
    data = null;
    if(id.length == 10) // general
    {
        switch(id[0])
        {
            case '1': // weapons
                data = [[id],["phit_" + id + ".png","phit_" + id + "_1.png","phit_" + id + "_2.png"],["sp_" + id + "_0_a.png","sp_" + id + "_0_b.png","sp_" + id + "_1_a.png","sp_" + id + "_1_b.png"]];
                break;
            case '2': // summons
                data = [[id,id + "_02"],["summon_" + id + "_01_attack_a.png","summon_" + id + "_01_attack_b.png","summon_" + id + "_01_attack_c.png","summon_" + id + "_01_attack_d.png","summon_" + id + "_02_attack_a.png","summon_" + id + "_02_attack_b.png","summon_" + id + "_02_attack_c.png"],["summon_" + id + "_01_damage.png","summon_" + id + "_02_damage.png"]];
                break;
            case '3': // npcs (styles unsupported)
                switch(id[1])
                {
                    case '0': // playable
                        switch(id[2])
                        {
                            case '5': // special npc
                                data = [true, ["","_up","_laugh","_laugh_up","_laugh2","_laugh2_up","_laugh3","_laugh3_up","_sad","_sad_speed","_sad_up","_angry","_angry_speed","_angry_up","_shadow","_shadow_up","_surprise","_surprise_speed","_surprise_up","_suddenly","_suddenly_up","_suddenly2","_suddenly2_up","_ef","_weak","_weak_up","_a","_b_sad","_valentine","_valentine2","_birthday","_birthday2","_birthday3","_birthday3_a","_birthday3_b"],[]];
                                break;
                            default: // playable r, sr, ssr
                                data = [["npc_" + id + "_01.png","npc_" + id + "_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_02"],["" + id + "_01","" + id + "_02"],["", "_a", "_a_angry", "_a_angry2", "_a_angry2_speed", "_a_angry2_up", "_a_angry_speed", "_a_angry_up", "_a_close", "_a_close_up", "_a_ecstasy", "_a_ecstasy2", "_a_ecstasy2_up", "_a_ecstasy_up", "_a_ef", "_a_ef_speed", "_a_laugh", "_a_laugh2", "_a_laugh2_up", "_a_laugh3", "_a_laugh3_speed", "_a_laugh3_up", "_a_laugh_speed", "_a_laugh_up", "_a_mood", "_a_mood2", "_a_mood2_up", "_a_mood_up", "_a_sad", "_a_sad2", "_a_sad2_up", "_a_sad_speed", "_a_sad_up", "_a_serious", "_a_serious2", "_a_serious2_speed", "_a_serious2_up", "_a_serious_speed", "_a_serious_up", "_a_shadow", "_a_shadow_speed", "_a_shadow_up", "_a_shout", "_a_shout2", "_a_shout2_speed", "_a_shout2_up", "_a_shout_speed", "_a_shout_up", "_a_shy", "_a_shy2", "_a_shy2_up", "_a_shy_up", "_a_speed", "_a_speed2", "_a_suddenly", "_a_suddenly2", "_a_suddenly2_up", "_a_suddenly_up", "_a_surprise", "_a_surprise2", "_a_surprise2_speed", "_a_surprise2_up", "_a_surprise_speed", "_a_surprise_up", "_a_think", "_a_think2", "_a_think2_speed", "_a_think2_up", "_a_think3", "_a_think3_up", "_a_think4", "_a_think4_up", "_a_think5", "_a_think5_up", "_a_think_speed", "_a_think_up", "_a_up", "_a_up_speed", "_a_valentine", "_a_weak", "_a_weak_up", "_a_wink", "_a_wink_up", "_angry", "_angry2", "_angry2_speed", "_angry2_up", "_angry_speed", "_angry_up", "_b", "_b_angry", "_b_angry2", "_b_angry2_speed", "_b_angry2_up", "_b_angry_speed", "_b_angry_up", "_b_close", "_b_close_up", "_b_ef", "_b_ef_speed", "_b_ef_up", "_b_laugh", "_b_laugh2", "_b_laugh2_up", "_b_laugh3", "_b_laugh3_up", "_b_laugh_speed", "_b_laugh_up", "_b_mood", "_b_mood2", "_b_mood2_up", "_b_mood_up", "_b_sad", "_b_sad2", "_b_sad2_up", "_b_sad_up", "_b_serious", "_b_serious2", "_b_serious2_up", "_b_serious_speed", "_b_serious_up", "_b_shadow", "_b_shadow_speed", "_b_shadow_up", "_b_shout", "_b_shout2", "_b_shout2_up", "_b_shout_up", "_b_shy", "_b_shy2", "_b_shy2_up", "_b_shy_up", "_b_speed", "_b_speed2", "_b_suddenly", "_b_suddenly2", "_b_suddenly2_up", "_b_suddenly_up", "_b_surprise", "_b_surprise2", "_b_surprise2_up", "_b_surprise_speed", "_b_surprise_up", "_b_think", "_b_think2", "_b_think2_up", "_b_think3", "_b_think3_up", "_b_think_up", "_b_up", "_b_up_speed", "_b_weak", "_b_weak_up", "_battle", "_battle_angry", "_battle_angry_speed", "_battle_angry_up", "_battle_close", "_battle_close_up", "_battle_ef", "_battle_laugh", "_battle_laugh2", "_battle_laugh2_up", "_battle_laugh3", "_battle_laugh3_up", "_battle_laugh_up", "_battle_serious", "_battle_serious_speed", "_battle_serious_up", "_battle_shadow", "_battle_shout", "_battle_shout_up", "_battle_speed", "_battle_speed2", "_battle_suddenly", "_battle_suddenly_up", "_battle_surprise", "_battle_surprise2", "_battle_surprise2_up", "_battle_surprise_speed", "_battle_surprise_up", "_battle_up", "_birthday", "_birthday2", "_birthday3", "_birthday3_a", "_birthday3_b", "_body", "_body_speed", "_c_up_speed", "_close", "_close_speed", "_close_up", "_ecstasy", "_ecstasy2", "_ecstasy2_up", "_ecstasy_up", "_ef", "_ef_speed", "_ef_up", "_eyeline", "_laugh", "_laugh2", "_laugh2_speed", "_laugh2_up", "_laugh3", "_laugh3_speed", "_laugh3_up", "_laugh_speed", "_laugh_up", "_mood", "_mood2", "_mood2_up", "_mood_speed", "_mood_up", "_sad", "_sad2", "_sad2_speed", "_sad2_up", "_sad_speed", "_sad_up", "_school", "_school_up", "_serious", "_serious2", "_serious2_speed", "_serious2_up", "_serious_speed", "_serious_up", "_shadow", "_shadow_speed", "_shadow_up", "_shout", "_shout2", "_shout2_speed", "_shout2_up", "_shout_speed", "_shout_up", "_shy", "_shy2", "_shy2_up", "_shy_speed", "_shy_up", "_speed", "_speed2", "_suddenly", "_suddenly2", "_suddenly2_up", "_suddenly_speed", "_suddenly_up", "_surprise", "_surprise2", "_surprise2_speed", "_surprise2_up", "_surprise_speed", "_surprise_up", "_think", "_think2", "_think2_speed", "_think2_up", "_think3", "_think3_up", "_think4", "_think4_up", "_think_speed", "_think_up", "_up", "_up_speed", "_valentine", "_valentine2", "_valentine_a", "_weak", "_weak_speed", "_weak_up", "_white", "_whiteday", "_whiteday2", "_whiteday3", "_wink", "_wink_up"],[]];
                                break;
                        };
                        break;
                    case '7': // skins
                        switch(id[2])
                        {
                            case '1': // skins
                                data = [["npc_" + id + "_01.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_01.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_02"],["" + id + "_01","" + id + "_02"],["", "_a", "_a_angry", "_a_angry2", "_a_angry2_speed", "_a_angry2_up", "_a_angry_speed", "_a_angry_up", "_a_close", "_a_close_up", "_a_ecstasy", "_a_ecstasy2", "_a_ecstasy2_up", "_a_ecstasy_up", "_a_ef", "_a_ef_speed", "_a_laugh", "_a_laugh2", "_a_laugh2_up", "_a_laugh3", "_a_laugh3_speed", "_a_laugh3_up", "_a_laugh_speed", "_a_laugh_up", "_a_mood", "_a_mood2", "_a_mood2_up", "_a_mood_up", "_a_sad", "_a_sad2", "_a_sad2_up", "_a_sad_speed", "_a_sad_up", "_a_serious", "_a_serious2", "_a_serious2_speed", "_a_serious2_up", "_a_serious_speed", "_a_serious_up", "_a_shadow", "_a_shadow_speed", "_a_shadow_up", "_a_shout", "_a_shout2", "_a_shout2_speed", "_a_shout2_up", "_a_shout_speed", "_a_shout_up", "_a_shy", "_a_shy2", "_a_shy2_up", "_a_shy_up", "_a_speed", "_a_speed2", "_a_suddenly", "_a_suddenly2", "_a_suddenly2_up", "_a_suddenly_up", "_a_surprise", "_a_surprise2", "_a_surprise2_speed", "_a_surprise2_up", "_a_surprise_speed", "_a_surprise_up", "_a_think", "_a_think2", "_a_think2_speed", "_a_think2_up", "_a_think3", "_a_think3_up", "_a_think4", "_a_think4_up", "_a_think5", "_a_think5_up", "_a_think_speed", "_a_think_up", "_a_up", "_a_up_speed", "_a_valentine", "_a_weak", "_a_weak_up", "_a_wink", "_a_wink_up", "_angry", "_angry2", "_angry2_speed", "_angry2_up", "_angry_speed", "_angry_up", "_b", "_b_angry", "_b_angry2", "_b_angry2_speed", "_b_angry2_up", "_b_angry_speed", "_b_angry_up", "_b_close", "_b_close_up", "_b_ef", "_b_ef_speed", "_b_ef_up", "_b_laugh", "_b_laugh2", "_b_laugh2_up", "_b_laugh3", "_b_laugh3_up", "_b_laugh_speed", "_b_laugh_up", "_b_mood", "_b_mood2", "_b_mood2_up", "_b_mood_up", "_b_sad", "_b_sad2", "_b_sad2_up", "_b_sad_up", "_b_serious", "_b_serious2", "_b_serious2_up", "_b_serious_speed", "_b_serious_up", "_b_shadow", "_b_shadow_speed", "_b_shadow_up", "_b_shout", "_b_shout2", "_b_shout2_up", "_b_shout_up", "_b_shy", "_b_shy2", "_b_shy2_up", "_b_shy_up", "_b_speed", "_b_speed2", "_b_suddenly", "_b_suddenly2", "_b_suddenly2_up", "_b_suddenly_up", "_b_surprise", "_b_surprise2", "_b_surprise2_up", "_b_surprise_speed", "_b_surprise_up", "_b_think", "_b_think2", "_b_think2_up", "_b_think3", "_b_think3_up", "_b_think_up", "_b_up", "_b_up_speed", "_b_weak", "_b_weak_up", "_battle", "_battle_angry", "_battle_angry_speed", "_battle_angry_up", "_battle_close", "_battle_close_up", "_battle_ef", "_battle_laugh", "_battle_laugh2", "_battle_laugh2_up", "_battle_laugh3", "_battle_laugh3_up", "_battle_laugh_up", "_battle_serious", "_battle_serious_speed", "_battle_serious_up", "_battle_shadow", "_battle_shout", "_battle_shout_up", "_battle_speed", "_battle_speed2", "_battle_suddenly", "_battle_suddenly_up", "_battle_surprise", "_battle_surprise2", "_battle_surprise2_up", "_battle_surprise_speed", "_battle_surprise_up", "_battle_up", "_birthday", "_birthday2", "_birthday3", "_birthday3_a", "_birthday3_b", "_body", "_body_speed", "_c_up_speed", "_close", "_close_speed", "_close_up", "_ecstasy", "_ecstasy2", "_ecstasy2_up", "_ecstasy_up", "_ef", "_ef_speed", "_ef_up", "_eyeline", "_laugh", "_laugh2", "_laugh2_speed", "_laugh2_up", "_laugh3", "_laugh3_speed", "_laugh3_up", "_laugh_speed", "_laugh_up", "_mood", "_mood2", "_mood2_up", "_mood_speed", "_mood_up", "_sad", "_sad2", "_sad2_speed", "_sad2_up", "_sad_speed", "_sad_up", "_school", "_school_up", "_serious", "_serious2", "_serious2_speed", "_serious2_up", "_serious_speed", "_serious_up", "_shadow", "_shadow_speed", "_shadow_up", "_shout", "_shout2", "_shout2_speed", "_shout2_up", "_shout_speed", "_shout_up", "_shy", "_shy2", "_shy2_up", "_shy_speed", "_shy_up", "_speed", "_speed2", "_suddenly", "_suddenly2", "_suddenly2_up", "_suddenly_speed", "_suddenly_up", "_surprise", "_surprise2", "_surprise2_speed", "_surprise2_up", "_surprise_speed", "_surprise_up", "_think", "_think2", "_think2_speed", "_think2_up", "_think3", "_think3_up", "_think4", "_think4_up", "_think_speed", "_think_up", "_up", "_up_speed", "_valentine", "_valentine2", "_valentine_a", "_weak", "_weak_speed", "_weak_up", "_white", "_whiteday", "_whiteday2", "_whiteday3", "_wink", "_wink_up"],[]];
                                break;
                            default:
                                return;
                        };
                        break;
                    case '8': // partners
                        data = [["npc_" + id + "_01.png","npc_" + id + "_0_01.png","npc_" + id + "_1_01.png","npc_" + id + "_02.png","npc_" + id + "_0_02.png","npc_" + id + "_1_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_01_0","" + id + "_01_1","" + id + "_02","" + id + "_02_0","" + id + "_02_1"]];
                        break;
                    case '9': // npcs
                        data = [true, ["", "_a", "_a_angry", "_a_angry2", "_a_angry2_speed", "_a_angry2_up", "_a_angry_speed", "_a_angry_up", "_a_close", "_a_close_up", "_a_ecstasy", "_a_ecstasy2", "_a_ecstasy2_up", "_a_ecstasy_up", "_a_ef", "_a_ef_speed", "_a_laugh", "_a_laugh2", "_a_laugh2_up", "_a_laugh3", "_a_laugh3_speed", "_a_laugh3_up", "_a_laugh_speed", "_a_laugh_up", "_a_mood", "_a_mood2", "_a_mood2_up", "_a_mood_up", "_a_sad", "_a_sad2", "_a_sad2_up", "_a_sad_speed", "_a_sad_up", "_a_serious", "_a_serious2", "_a_serious2_speed", "_a_serious2_up", "_a_serious_speed", "_a_serious_up", "_a_shadow", "_a_shadow_speed", "_a_shadow_up", "_a_shout", "_a_shout2", "_a_shout2_speed", "_a_shout2_up", "_a_shout_speed", "_a_shout_up", "_a_shy", "_a_shy2", "_a_shy2_up", "_a_shy_up", "_a_speed", "_a_speed2", "_a_suddenly", "_a_suddenly2", "_a_suddenly2_up", "_a_suddenly_up", "_a_surprise", "_a_surprise2", "_a_surprise2_speed", "_a_surprise2_up", "_a_surprise_speed", "_a_surprise_up", "_a_think", "_a_think2", "_a_think2_speed", "_a_think2_up", "_a_think3", "_a_think3_up", "_a_think4", "_a_think4_up", "_a_think5", "_a_think5_up", "_a_think_speed", "_a_think_up", "_a_up", "_a_up_speed", "_a_valentine", "_a_weak", "_a_weak_up", "_a_wink", "_a_wink_up", "_angry", "_angry2", "_angry2_speed", "_angry2_up", "_angry_speed", "_angry_up", "_b", "_b_angry", "_b_angry2", "_b_angry2_speed", "_b_angry2_up", "_b_angry_speed", "_b_angry_up", "_b_close", "_b_close_up", "_b_ef", "_b_ef_speed", "_b_ef_up", "_b_laugh", "_b_laugh2", "_b_laugh2_up", "_b_laugh3", "_b_laugh3_up", "_b_laugh_speed", "_b_laugh_up", "_b_mood", "_b_mood2", "_b_mood2_up", "_b_mood_up", "_b_sad", "_b_sad2", "_b_sad2_up", "_b_sad_up", "_b_serious", "_b_serious2", "_b_serious2_up", "_b_serious_speed", "_b_serious_up", "_b_shadow", "_b_shadow_speed", "_b_shadow_up", "_b_shout", "_b_shout2", "_b_shout2_up", "_b_shout_up", "_b_shy", "_b_shy2", "_b_shy2_up", "_b_shy_up", "_b_speed", "_b_speed2", "_b_suddenly", "_b_suddenly2", "_b_suddenly2_up", "_b_suddenly_up", "_b_surprise", "_b_surprise2", "_b_surprise2_up", "_b_surprise_speed", "_b_surprise_up", "_b_think", "_b_think2", "_b_think2_up", "_b_think3", "_b_think3_up", "_b_think_up", "_b_up", "_b_up_speed", "_b_weak", "_b_weak_up", "_battle", "_battle_angry", "_battle_angry_speed", "_battle_angry_up", "_battle_close", "_battle_close_up", "_battle_ef", "_battle_laugh", "_battle_laugh2", "_battle_laugh2_up", "_battle_laugh3", "_battle_laugh3_up", "_battle_laugh_up", "_battle_serious", "_battle_serious_speed", "_battle_serious_up", "_battle_shadow", "_battle_shout", "_battle_shout_up", "_battle_speed", "_battle_speed2", "_battle_suddenly", "_battle_suddenly_up", "_battle_surprise", "_battle_surprise2", "_battle_surprise2_up", "_battle_surprise_speed", "_battle_surprise_up", "_battle_up", "_birthday", "_birthday2", "_birthday3", "_birthday3_a", "_birthday3_b", "_body", "_body_speed", "_c_up_speed", "_close", "_close_speed", "_close_up", "_ecstasy", "_ecstasy2", "_ecstasy2_up", "_ecstasy_up", "_ef", "_ef_speed", "_ef_up", "_eyeline", "_laugh", "_laugh2", "_laugh2_speed", "_laugh2_up", "_laugh3", "_laugh3_speed", "_laugh3_up", "_laugh_speed", "_laugh_up", "_mood", "_mood2", "_mood2_up", "_mood_speed", "_mood_up", "_sad", "_sad2", "_sad2_speed", "_sad2_up", "_sad_speed", "_sad_up", "_school", "_school_up", "_serious", "_serious2", "_serious2_speed", "_serious2_up", "_serious_speed", "_serious_up", "_shadow", "_shadow_speed", "_shadow_up", "_shout", "_shout2", "_shout2_speed", "_shout2_up", "_shout_speed", "_shout_up", "_shy", "_shy2", "_shy2_up", "_shy_speed", "_shy_up", "_speed", "_speed2", "_suddenly", "_suddenly2", "_suddenly2_up", "_suddenly_speed", "_suddenly_up", "_surprise", "_surprise2", "_surprise2_speed", "_surprise2_up", "_surprise_speed", "_surprise_up", "_think", "_think2", "_think2_speed", "_think2_up", "_think3", "_think3_up", "_think4", "_think4_up", "_think_speed", "_think_up", "_up", "_up_speed", "_valentine", "_valentine2", "_valentine_a", "_weak", "_weak_speed", "_weak_up", "_white", "_whiteday", "_whiteday2", "_whiteday3", "_wink", "_wink_up"],[]];
                        break;
                };
                break;
            default:
                return;
        };
    }
    else if(id.length == 7) // enemies
    {
        data = [[id],["enemy_" + id + "_a.png","enemy_" + id + "_b.png","enemy_" + id + "_c.png"],["raid_appear_" + id + ".png"],["ehit_" + id + ".png"],["esp_" + id + "_01.png","esp_" + id + "_02.png","esp_" + id + "_03.png"],["esp_" + id + "_01_all.png","esp_" + id + "_02_all.png","esp_" + id + "_03_all.png"]];
    }
    else if(id.length == 9 && id[6] == "_") // mc id + proficiency
    {
        id = id.split('_')[0];
        prof = id.split('_')[1];
        data = [[id],[id + "_01"],[id + "_" + prof + "_0_01",id + "_" + prof + "_1_01"],[id + "_" + prof + "_0_01",id + "_" + prof + "_1_01"],[id + "_" + prof + "_0_01",id + "_" + prof + "_1_01"],[id],["" + prof + ""],[],[],[]];
    }
    else if(id.length == 6) // mc
    {
        data = [[id],[id + "_01"],[],[],[],[id],[],[],[],[]];
    }
    if(data != null)
    {
        last_id = id;
        updateQuery((id.length == 7) ? "e"+id : id);
        loadIndexed(id, data, false);
    }
}

function lookup(id)
{
    main_endp_count = -1;
    f = document.getElementById('filter');
    if(
        (id.length == 10 && !isNaN(id)) || 
        (id.length == 8 && id.toLowerCase()[0] === 'e' && !isNaN(id.slice(1))) ||
        (id.length == 9 && id.toLowerCase()[6] === '_' && !isNaN(id.slice(0, 6))) || // retrocompatibility
        (id.length == 6 && !isNaN(id))
    )
    {
        if(blacklist.includes(id)) return;
        // process id // NOTE TO SELF: replace this trash by a switch later
        let start = id.slice(0, 2);
        let check = null;
        if(f.value == "" || f.value != id)
        {
            f.value = id;
        }
        if(id.toLowerCase()[0] === 'e')
        {
            id = id.slice(1);
            check = "enemies";
        }
        else if(id.slice(0, 3) == "305") check = "npcs"; // for lyria and stuff
        else if(start == "30") check = "characters";
        else if(start == "38") check = "partners";
        else if(start == "39") check = "npcs";
        else if(start == "37") check = "skins";
        else if(start == "20") check = "summons";
        else if(start == "10") check = "weapons";
        else if(id.length == 9 && id[6] == "_") // retrocompatibility
        {
            id = id.split('_')[0];
            check = "job";
        }
        else if(id.length == 6) check = "job";
        if(id == last_id) return; // quit if already loaded
        // disable search results if not relevant to current id
        let found = false;
        for(const el of searchResults)
        {
            if(el[0] == id)
            {
                found = true;
                break;
            }
        }
        if(!found)
        {
            document.getElementById('results').style.display = "none";
            searchResults = [];
        }
        // remove fav button before loading
        favButton(false, null, null);
        if(check != null && id in index[check] && index[check][id] !== 0)
        {
            loadIndexed(id, index[check][id]);
        }
        else
        {
            if(check != null && id in index[check] && index[check][id] == 0)
            {
                switch(check) // enable favorite if partially indexed
                {
                    case "npcs":
                        favButton(true, id, 5);
                        break;
                    case "enemies":
                        favButton(true, id, 4);
                        break;
                    case "characters":
                    case "skins":
                        favButton(true, id, 3);
                        break;
                    case "summons":
                        favButton(true, id, 2);
                        break;
                    case "weapons":
                        favButton(true, id, 1);
                        break;
                    case "job":
                        favButton(true, id, 0);
                        break;
                    case "partners":
                        favButton(true, id, 6);
                        break;
                }
            }
            loadUnindexed(id);
        }
    }
    else
    {
        let results = document.getElementById('results');
        results.style.display = "none";
        results.innerHTML = "";
        if(id == "") return;
        let words = id.toLowerCase().split(' ');
        let positives = [];
        for(const [key, value] of Object.entries(index['lookup_reverse']))
        {
            let matching = true;
            for(const w of words)
            {
                if(!key.includes(w))
                {
                    matching = false;
                    break;
                }
            }
            if(matching)
            {
                positives.push([value, parseInt(value[0])]);
                if(positives.length == 50) break;
            }
        }
        updateDynamicList(results, positives);
        results.style.display = null;
        if(positives.length == 50)
        {
            results.appendChild(document.createElement("br"));
            results.appendChild(document.createTextNode("(First 50 results)"));
        }
        else if(positives.length == 0)
        {
            results.appendChild(document.createTextNode("No Results"));
        }
        if(positives.length > 0)
        {
            results.insertBefore(document.createElement("br"), results.firstChild);
            results.insertBefore(document.createTextNode("Results for \"" + id + "\""), results.firstChild);
        }
        searchResults = positives;
    }
}

function newArea(name, id, include_link, indexed=true)
{
    while(true)
    {
        let child = result_area.lastElementChild;
        if(!child) break;
        result_area.removeChild(child);
    }
    let div = addResult("Result Header", name + ": " + id);
    if(include_link)
    {
        let l = document.createElement('a');
        l.setAttribute('href', "https://gbf.wiki/index.php?title=Special:Search&search=" + id);
        l.appendChild(document.createTextNode("Wiki"));
        div.appendChild(l);
        div.appendChild(document.createElement('br'));
    }
    if(id.slice(0, 3) == "302" || id.slice(0, 3) == "303" || id.slice(0, 3) == "304" || id.slice(0, 3) == "371" || id.slice(0, 2) == "10" || id.length == 6)
    {
        l = document.createElement('a');
        l.setAttribute('href', "https://mizagbf.github.io/GBFAP/?id=" + id);
        l.appendChild(document.createTextNode("Animation"));
        div.appendChild(l);
    }
    if(id in index["lookup"] && index["lookup"][id].split(' ').length > 1)
    {
        div.appendChild(document.createElement('br'));
        let i = document.createElement('i');
        i.appendChild(document.createTextNode("Search Tags: "));
        div.appendChild(i);
        for(let t of index["lookup"][id].split(' '))
        {
            i = document.createElement('i');
            i.classList.add("tag");
            switch(t)
            {
                case "ssr": i.appendChild(document.createTextNode("SSR ")); break;
                case "sr": i.appendChild(document.createTextNode("SR ")); break;
                default:
                    if(t.length == 1) i.appendChild(document.createTextNode(t.toUpperCase() + " "));
                    else i.appendChild(document.createTextNode(t.charAt(0).toUpperCase() + t.slice(1) + " "));
                    break;
            }
            i.onclick = function() {
                lookup(t);
            };
            div.appendChild(i);
        }
    }
    if(!indexed)
    {
        div.appendChild(document.createElement('br'));
        div.appendChild(document.createTextNode("This element isn't indexed, assets will be missing"));
    }
    else if(name == "Partner") // partner chara matching
    {
        let cid = "30" + id.slice(2);
        if("characters" in index && cid in index["characters"])
        {
            div.appendChild(document.createTextNode("Character: "));
            let i = document.createElement('i');
            i.classList.add("tag");
            i.onclick = function() {
                lookup(cid);
            };
            i.appendChild(document.createTextNode(cid)); 
            div.appendChild(i);
        }
    }
}

function addResult(identifier, name, file_count = 0)
{
    let div = document.createElement("div");
    div.classList.add("result");
    if(identifier == "Result Header") div.classList.add("result-header");
    div.setAttribute("data-id", identifier);
    div.appendChild(document.createTextNode(name));
    div.appendChild(document.createElement("br"));
    if(file_count > 20)
    {
        let details = document.createElement("details");
        let summary = document.createElement("summary");
        summary.innerHTML = file_count + " Files";
        details.appendChild(summary);
        div.appendChild(details);
        result_area.appendChild(div);
        return details;
    }
    else
    {
        result_area.appendChild(div);
        return div;
    }
}

// =================================================================================================
// bookmark, history, relation
function updateDynamicList(dynarea, idlist)
{
    dynarea.classList.add("mobile-big");
    for(let e of idlist)
    {
        switch(e[1])
        {
            case 3: // character, skin, ...
            {
                let uncap = "_01";
                if(e[0][1] != 7 && "characters" in index && e[0] in index["characters"])
                {
                    let data = index["characters"][e[0]];
                    if(data != 0)
                    {
                        for(const f of data[6])
                            if(!f.includes("st") && f[11] != 8 && f.slice(11, 13) != "02" && (f[11] != 9 || (f[11] == 9 && !(["_03", "_04", "_05"].includes(uncap))))) uncap = f.slice(10);
                    }
                }
                addIndexImage(dynarea, "sp/assets/npc/m/" + e[0] + uncap + ".jpg", e[0]);
                break;
            }
            case 2: // summon
            {
                let onerr = null;
                let uncap = "";
                if("summons" in index && e[0] in index["summons"])
                {
                    let data = index["summons"][e[0]];
                    if(data != 0)
                    {
                        for(const f of data[0])
                            if(f.includes("_")) uncap = f.slice(10);
                        onerr = function() {
                            this.src = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/m/2999999999.jpg";
                        };
                    }
                }
                addIndexImage(dynarea, "sp/assets/summon/m/" + e[0] + uncap + ".jpg", e[0], onerr);
                break;
            }
            case 1: // weapon
            {
                addIndexImage(dynarea, "sp/assets/weapon/m/" + e[0] + ".jpg", e[0]);
                break;
            }
            case 0: // mc
            {
                if(e[0].length == 9) e[0] = e[0].split('_')[0]; // retrocompatibility
                addIndexImage(dynarea, "sp/assets/leader/m/" + e[0] + "_01.jpg", e[0]);
                break;
            }
            case 4: // enemy
            {
                addIndexImage(dynarea, "sp/assets/enemy/s/" + e[0] + ".png", "e" + e[0], null, "img/");
                break;
            }
            case 5: // npc
            {
                if("npcs" in index && e[0] in index["npcs"] && index["npcs"][e[0]] != 0)
                {
                    if(index["npcs"][e[0]][0])
                        addIndexImage(dynarea, "sp/assets/npc/m/" + e[0] + "_01.jpg", e[0], null);
                    else if(index["npcs"][e[0]][1].length > 0)
                        addIndexImage(dynarea, "sp/quest/scene/character/body/" + e[0] + index["npcs"][e[0]][1][0] + ".png", e[0], null).className = "preview";
                    else
                        addIndexImage(dynarea, "assets/ui/sound_only.png", e[0], null, "local").className = "sound-only";
                }
                else // old, might not be needed anymore
                {
                    let onerr = function() {
                        this.onerror = function() {
                            this.onerror = function() {
                                this.remove();
                            };
                            this.src = "assets/ui/sound_only.png";
                            this.className = "sound-only";
                        };
                        this.src = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/quest/scene/character/body/"+this.src.split('/').slice(-1)[0].split('_')[0]+".png";
                        this.className = "preview";
                    };
                    addIndexImage(dynarea, "sp/assets/npc/m/" + e[0] + "_01.jpg", e[0], onerr);
                }
                break;
            }
            case 6: // partners
            {
                if('partners' in index && index['partners'][e[0]] != 0 && index['partners'][e[0]][5].length > 0)
                {
                    let onerr;
                    if(index['partners'][e[0]][5].length > 1)
                    {
                        onerr = function() {
                            this.onerror = function() {
                                this.src = "https://prd-game-a3-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/raid_normal/3999999999.jpg";
                            };
                            this.src = "https://prd-game-a3-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/raid_normal/" + index['partners'][e[0]][5][1] + ".jpg";
                        };
                    }
                    else
                    {
                        onerr = function() {
                            this.src = "https://prd-game-a3-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/raid_normal/3999999999.jpg";
                        };
                    }
                    addIndexImage(dynarea, "sp/assets/npc/raid_normal/" + index['partners'][e[0]][5][0] + ".jpg", e[0], onerr, "img_low/").classList.add("preview");
                }
                else
                {
                    let onerr = function() {
                        this.src = "https://prd-game-a3-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/raid_normal/3999999999.jpg";
                    };
                    addIndexImage(dynarea, "sp/assets/npc/raid_normal/" + e[0] + "_01.jpg", e[0], onerr, "img_low/").classList.add("preview");
                }
                break;
            }
        }
    }
}

function favButton(state, id, search_type)
{
    let fav = document.getElementById('favorite');
    if(state)
    {
        fav.style.display = null;
        fav.onclick = function() { toggleBookmark(id, search_type); };
        for(let e of bookmarks)
        {
            if(e[0] == id)
            {
                if(fav.src != "assets/ui/fav_1.png")
                    fav.src = "assets/ui/fav_1.png";
                return;
            }
        }
        if(fav.src != "assets/ui/fav_0.png")
            fav.src = "assets/ui/fav_0.png";
    }
    else
    {
        document.getElementById('favorite').style.display = "none";
        fav.onclick = null;
    }
}

function updateBookmark()
{
    if(bookmarks.length == 0)
    {
        document.getElementById('bookmark').parentNode.style.display = "none";
        return;
    }
    let bookarea = document.getElementById('bookmark');
    bookarea.parentNode.style.display = null;
    bookarea.innerHTML = "";
    updateDynamicList(bookarea, bookmarks);
    bookarea.appendChild(document.createElement("br"));
    let btn = document.createElement("button");
    btn.innerHTML = "Clear";
    btn.onclick = clearBookmark;
    bookarea.appendChild(btn);
    btn = document.createElement("button");
    btn.innerHTML = "Export";
    btn.onclick = exportBookmark;
    bookarea.appendChild(btn);
    btn = document.createElement("button");
    btn.innerHTML = "Import";
    btn.onclick = importBookmark;
    bookarea.appendChild(btn);
}

function clearBookmark()
{
    localStorage.removeItem('bookmark');
    document.getElementById('bookmark').parentNode.style.display = "none";
    document.getElementById('favorite').src = "assets/ui/fav_0.png";
}

function exportBookmark()
{
    try
    {
        bookmarks = localStorage.getItem("bookmark");
        if(bookmarks == null)
        {
            bookmarks = [];
        }
        else
        {
            bookmarks = JSON.parse(bookmarks);
        }
    }
    catch(err)
    {
        bookmarks = [];
    }
    navigator.clipboard.writeText(JSON.stringify(bookmarks));
    let div = document.createElement('div');
    div.className = 'popup';
    div.textContent ='Bookmarks have been copied';
    document.body.appendChild(div);
    intervals.push(setInterval(rmPopup, 2500, div));
}

function importBookmark()
{
    navigator.clipboard.readText().then((clipText) => {
        try
        {
            let tmp = JSON.parse(clipText);
            if(typeof tmp != 'object') return;
            let fav = false;
            let i = 0;
            while(i < tmp.length)
            {
                let e = tmp[i];
                if(typeof e != 'object' || e.length != 2 || typeof e[0] != 'string' || typeof e[1] != 'number') return;
                if(last_id == e[0]) fav = true;
                ++i;
            }
            bookmarks = tmp;
            localStorage.setItem("bookmark", JSON.stringify(bookmarks));
            if(fav) document.getElementById('favorite').src = "assets/ui/fav_1.png";
            else document.getElementById('favorite').src = "assets/ui/fav_0.png";
            let div = document.createElement('div');
            div.className = 'popup';
            div.textContent ='Bookmarks have been imported with success';
            document.body.appendChild(div);
            intervals.push(setInterval(rmPopup, 2500, div));
            updateBookmark();
        }
        catch(err) {}
    });
}

function rmPopup(popup) {
    popup.parentNode.removeChild(popup);
    clearInterval(intervals[0]);
    intervals.shift();
}

function toggleBookmark(id, search_type)
{
    try
    {
        bookmarks = localStorage.getItem("bookmark");
        if(bookmarks == null)
        {
            bookmarks = [];
        }
        else
        {
            bookmarks = JSON.parse(bookmarks);
        }
    }
    catch(err)
    {
        bookmarks = [];
    }
    if(id != null)
    {
        let fav = document.getElementById('favorite');
        if(fav.src.endsWith('fav_0.png'))
        {
            bookmarks.push([id, search_type]);
            fav.src = "assets/ui/fav_1.png";
        }
        else
        {
            for(let i = 0; i < bookmarks.length; ++i)
            {
                if(bookmarks[i][0] == id)
                {
                    bookmarks.splice(i, 1);
                    break;
                }
            }
            fav.src = "assets/ui/fav_0.png";
        }
        localStorage.setItem("bookmark", JSON.stringify(bookmarks));
    }
    updateBookmark();
}

function clearHistory()
{
    localStorage.removeItem('history');
    document.getElementById('history').parentNode.style.display = "none";
}

function updateHistory(id, search_type)
{
    // update local storage
    try
    {
        searchHistory = localStorage.getItem("history");
        if(searchHistory == null)
        {
            searchHistory = [];
        }
        else
        {
            searchHistory = JSON.parse(searchHistory);
            if(searchHistory.length > 20) searchHistory = searchHistory.slice(searchHistory.length - 20); // resize if too big to not cause problems
        }
    }
    catch(err)
    {
        searchHistory = [];
    }
    if(id != null)
    {
        for(let e of searchHistory)
        {
            if(e[0] == id) return; // don't update if already in
        }
        searchHistory.push([id, search_type]);
        if(searchHistory.length > 20) searchHistory = searchHistory.slice(searchHistory.length - 20);
        localStorage.setItem("history", JSON.stringify(searchHistory));
    }
    if(searchHistory.length == 0)
    {
        document.getElementById('history').parentNode.style.display = "none";
        return;
    }
    let histarea = document.getElementById('history');
    histarea.parentNode.style.display = null;
    histarea.innerHTML = "";
    updateDynamicList(histarea, searchHistory.slice().reverse());
    histarea.appendChild(document.createElement("br"));
    let btn = document.createElement("button");
    btn.innerHTML = "Clear";
    btn.onclick = clearHistory;
    histarea.appendChild(btn);
}

function updateRelated(id)
{
    let relarea = document.getElementById('related');
    let idlist = [];
    if(id in relations)
    {
        for(let e of relations[id])
        {
            let indice = -1;
            if(e[0] == 'e') indice = 4;
            else if(e.startsWith('39')) indice = 5;
            else if(e.includes('_') && !e.includes('_st')) indice = 0;
            else indice = parseInt(e[0]);
            if(indice != -1) idlist.push([e, indice]);
        }
        if(idlist.length > 0)
        {
            relarea.parentNode.style.display = null;
            updateDynamicList(relarea, idlist);
        }
        else
        {
            relarea.parentNode.style.display = "none";
        }
    }
    else relarea.parentNode.style.display = "none";
}

// =================================================================================================
// index stuff
function addIndexImage(node, path, id, onerr = null, quality="img_low/")
{
    let img = document.createElement("img");
    node.appendChild(img);
    img.title = id;
    img.classList.add("loading");
    img.setAttribute('loading', 'lazy');
    if(onerr == null)
    {
        img.onerror = function() {
            this.remove();
        };
    }
    else img.onerror = onerr;
    img.onload = function() {
        this.classList.remove("loading");
        this.classList.add("clickable");
        this.onclick = function()
        {
            window.scrollTo(0, 0);
            lookup(id);
        };
    };
    if(quality == "local") img.src = path;
    else img.src = getIndexEndpoint(parseInt(id.replace(/\D/g,''))) + language + quality + path;
    return img;
}

function displayCharacters(elem, i, r_start, r_end, sr_start, sr_end, ssr_start, ssr_end)
{
    i = JSON.stringify(i);
    elem.removeAttribute("onclick");
    let node = document.getElementById('areacharacters'+i);
    if("characters" in index)
    {
        let slist = {};
        for(const [id, data] of Object.entries(index["characters"]))
        {
            let val = parseInt(id.slice(4, 7));
            switch(id[2])
            {
                case "2":
                    if(val < r_start || val >= r_end) continue;
                    break;
                case "3":
                    if(val < r_start || val >= r_end) continue;
                    break;
                case "4":
                    if(val < r_start || val >= r_end) continue;
                    break;
            }
            let uncap = "_01";
            if(data != 0)
            {
                for(const f of data[6])
                    if(!f.includes("st") && f[11] != 8 && f.slice(11, 13) != "02" && (f[11] != 9 || (f[11] == 9 && !(["_03", "_04", "_05"].includes(uncap))))) uncap = f.slice(10);
            }
            slist[id.padEnd(15, "0")] = ["sp/assets/npc/m/" + id + uncap + ".jpg", id];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1]);
    }
    this.onclick = null;
}

function displayPartners(elem, i)
{
    i = JSON.stringify(i);
    elem.removeAttribute("onclick");
    let node = document.getElementById('areapartners'+i);
    let onerr_basic = function() {
        this.src = "https://prd-game-a3-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/raid_normal/3999999999.jpg";
    };
    if("partners" in index)
    {
        let slist = {};
        for(const [id, data] of Object.entries(index["partners"]))
        {
            if(id[2] != i) continue;
            if(data != 0 && data[5].length > 0)
            {
                let onerr;
                if(data[5].length > 1)
                {
                    onerr = function() { // failsafe
                        this.onerror = function() {
                            this.src = "https://prd-game-a3-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/raid_normal/3999999999.jpg";
                        };
                        this.src = "https://prd-game-a3-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/raid_normal/" + data[5][1] + ".jpg";
                    };
                }
                else
                {
                    onerr = onerr_basic;
                }
                slist[id.padEnd(15, "0")] = ["sp/assets/npc/raid_normal/" + data[5][0] + ".jpg", id, onerr];
            }
            else
            {
                slist[id.padEnd(15, "0")] = ["sp/assets/npc/raid_normal/" + id + "_01.jpg", id, onerr_basic];
            }
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1], slist[k][2], "img_low/").classList.add("preview");
    }
    this.onclick = null;
}

function displaySummonsSSR(elem, i, n)
{
    i = JSON.stringify(i);
    elem.removeAttribute("onclick");
    let node = document.getElementById('areasummons'+i);
    let start = 2040000000 + n * 1000;
    let end = start + 200 * 1000;
    let onerr = function() {
        this.src = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/m/2999999999.jpg";
    };
    if("summons" in index)
    {
        let slist = {};
        for(const [id, data] of Object.entries(index["summons"]))
        {
            if(id[2] != "4") continue;
            let t = parseInt(id);
            if(t < start || t >= end) continue;
            let uncap = "";
            if(data != 0)
            {
                for(const f of data[0])
                    if(f.includes("_")) uncap = f.slice(10);
            }
            slist[id] = ["sp/assets/summon/m/" + id + uncap + ".jpg", id, data != 0];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1], (slist[k][2] ? onerr : null));
    }
    this.onclick = null;
}

function displaySummons(elem, i)
{
    i = JSON.stringify(i);
    elem.removeAttribute("onclick");
    let node = document.getElementById('areasummonsrare'+i);
    let onerr = function() {
        this.src = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/m/2999999999.jpg";
    };
    if("summons" in index)
    {
        let slist = {};
        for(const [id, data] of Object.entries(index["summons"]))
        {
            if(id[2] != i) continue;
            let uncap = "";
            if(data != 0)
            {
                for(const f of data[0])
                    if(f.includes("_")) uncap = f.slice(10);
            }
            slist[id] = ["sp/assets/summon/m/" + id + uncap + ".jpg", id, data != 0];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1], (slist[k][2] ? onerr : null));
    }
    this.onclick = null;
}

function displayWeapons(elem, r, i)
{
    r = JSON.stringify(r);
    i = JSON.stringify(i);
    elem.removeAttribute("onclick");
    let node = document.getElementById('areaweapons'+r+i);
    if("weapons" in index)
    {
        let slist = {};
        for(const id in index["weapons"])
        {
            if(id[4] != i || id[2] != r) continue;
            slist[id] = ["sp/assets/weapon/m/" + id + ".jpg", id];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1]);
    }
    this.onclick = null;
}

function displaySkins(elem, i)
{
    elem.removeAttribute("onclick");
    let start = 3710000000 + i * 1000;
    let end = start + 100 * 1000;
    let node = document.getElementById('areaskins' + i);
    if("skins" in index)
    {
        let slist = {};
        for(const id in index["skins"])
        {
            let t = parseInt(id);
            if(t < start || t >= end) continue;
            slist[id] = ["sp/assets/npc/m/" + id + "_01.jpg", id];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1]);
    }
}

function displayEnemies(elem, i)
{
    i = JSON.stringify(i);
    elem.removeAttribute("onclick");
    let node = document.getElementById('areaenemies'+i);
    if("enemies" in index)
    {
        let slist = {};
        for(const id in index["enemies"])
        {
            if(id[0] != i) continue;
            slist[id] = ["sp/assets/enemy/s/" + id + ".png", "e"+id];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1], null, "img/");
    }
    this.onclick = null;
}

function displayMainNPC(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areamainnpc');
    let onerr = function() {
        this.onerror = function() {
            this.remove();
        }
        this.src = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/quest/scene/character/body/"+this.src.split('/').slice(-1)[0].split('_')[0]+".png";
        this.className = "preview";
    };
    if("npcs" in index)
    {
        let slist = {};
        for(const id in index["npcs"])
        {
            if(id.startsWith("39")) continue;
            slist[id] = ["sp/assets/npc/m/" + id + "_01.jpg", id];
        }
        const keys = Object.keys(slist).sort();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1], onerr);
    }
    this.onclick = null;
}

function displayNPC(elem, i, n)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areanpc'+i);
    let start = 3990000000 + i * 1000;
    let end = start + n * 1000;
    if("npcs" in index)
    {
        let slist = {};
        for(const [id, data]  of Object.entries(index["npcs"]))
        {
            let t = parseInt(id);
            if(t < start || t >= end) continue;
            if(data != 0)
            {
                if(data[0]) slist[id] = ["sp/assets/npc/m/" + id + "_01.jpg", id, null];
                else if(data[1].length > 0) slist[id] = ["sp/quest/scene/character/body/" + id + data[1][0] + ".png", id, "preview"];
                else slist[id] = ["assets/ui/sound_only.png", id, "sound-only"];
            }
        }
        const keys = Object.keys(slist).sort();
        for(const k of keys)
        {
            switch(slist[k][2])
            {
                case "preview":
                    addIndexImage(node, slist[k][0], slist[k][1], null).className = slist[k][2];
                    break;
                case "sound-only":
                    addIndexImage(node, slist[k][0], slist[k][1], null, "local").className = slist[k][2];
                    break;
                default:
                    addIndexImage(node, slist[k][0], slist[k][1], null);
                    break;
            }
            
        }
    }
    this.onclick = null;
}

function displayMC(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areamc');
    if("job" in index)
    {
        let slist = {};
        for(const id in index["job"])
        {
            slist[id] = ["sp/assets/leader/m/" + id + "_01.jpg", id];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1]);
    }
    this.onclick = null;
}

function addIndexImageGeneric(node, path, id, onerr, className = "preview")
{
    let a = document.createElement("a");
    let img = document.createElement("img");
    a.appendChild(img);
    node.appendChild(a);
    img.title = id;
    img.classList.add("loading");
    img.setAttribute('loading', 'lazy');
    img.onload = function() {
        this.classList.remove("loading");
        this.classList.add(className);
    };
    if(onerr == null)
    {
        img.onerror = function() {
            this.parentNode.remove();
            this.remove();
        };
    }
    else img.onerror = onerr;
    img.src = getIndexEndpoint(parseInt(id.replace(/\D/g,''))) + language + "img_low/" + path;
    a.href = img.src.replace("img_low/", "img/");
}

function displayBG(elem, i=null)
{
    elem.removeAttribute("onclick");
    let node = (i==null ? document.getElementById('areabg') : document.getElementById('areabg'+i));
    if("background" in index)
    {
        let slist = {};
        for(const id in index["background"])
        {
            slist[id.padStart(9, "0")] = id;
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
        {
            const id = slist[k];
            if(i == null && !id.startsWith("common") && !id.startsWith("event") && !id.startsWith("main"))
            {
                addIndexImageGeneric(node, "sp/raid/bg/" + id + "_3.jpg", id+"_3", null);
                addIndexImageGeneric(node, "sp/raid/bg/" + id + "_2.jpg", id+"_2", null);
                addIndexImageGeneric(node, "sp/raid/bg/" + id + "_1.jpg", id+"_1", null);
            }
            else if(id.startsWith(i))
            {
                if(i == "main") addIndexImageGeneric(node, "sp/guild/custom/bg/" + id + ".png", id, null);
                else addIndexImageGeneric(node, "sp/raid/bg/" + id + ".jpg", id, null);
            }
        }
    }
    this.onclick = null;
}

function displayTitle(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areatitle');
    if("title" in index)
    {
        let slist = {};
        for(const id in index["title"])
        {
            slist[id.padStart(9, "0")] = id;
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImageGeneric(node, "sp/top/bg/bg_" + slist[k] + ".jpg", slist[k], null);
    }
    this.onclick = null;
}

function displaySuptix(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areasuptix');
    if("suptix" in index)
    {
        let slist = {};
        for(const id in index["suptix"])
        {
            slist[id.padStart(9, "0")] = id;
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImageGeneric(node, "sp/gacha/campaign/surprise/top_" + slist[k] + ".jpg", slist[k], null, "preview-wide");
    }
    this.onclick = null;
}