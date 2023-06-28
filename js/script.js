/* sky compass notes (for posterity)

Leader: https://media.skycompass.io/assets/customizes/jobs/1138x1138/ID_GENDER.png
Character: https://media.skycompass.io/assets/customizes/characters/1138x1138/ID_UNCAP.png
Summon: https://media.skycompass.io/assets/archives/summons/ID/detail_l.png
Event: https://media.skycompass.io/assets/archives/events/ID/image/NUM_free.png

*/

var protocol = "https://";
var endpoints = [
    "prd-game-a-granbluefantasy.akamaized.net/",
    "prd-game-a1-granbluefantasy.akamaized.net/",
    "prd-game-a2-granbluefantasy.akamaized.net/",
    "prd-game-a3-granbluefantasy.akamaized.net/",
    "prd-game-a4-granbluefantasy.akamaized.net/",
    "prd-game-a5-granbluefantasy.akamaized.net/"
];
var main_endp_count = -1;
var language = "assets_en/";
var last_id = null;
var last_style = null;
var result_area = null;
var null_characters = [
    "3030182000", "3710092000", "3710139000", "3710078000", "3710105000", "3710083000", "3020072000", "3710184000"
];
var blacklist = [

]
var index = {};
var mc_index = null;
var lastsearches = [];
var bookmarks = [];
var timestamp = Date.now();
var relations = {};
var updated = [];
var intervals = [];
var typingTimer;

function getMainEndpoint()
{
    main_endp_count = (main_endp_count + 1) % endpoints.length;
    return endpoints[main_endp_count];
}

function getIndexEndpoint(index)
{
    return endpoints[index % endpoints.length];
}

function typying()
{
    clearTimeout(typingTimer);
}

function filter()
{
    clearTimeout(typingTimer);
    typingTimer = setTimeout(function(){
        lookup(document.getElementById('filter').value.trim().toLowerCase());
    }, 1000);
}

function init()
{
    getJSON("json/changelog.json?" + timestamp, initChangelog, initChangelog, null);
    toggleBookmark(null, null);
}

function initChangelog(unusued)
{
    try{
        let json = JSON.parse(this.response);
        if(json.hasOwnProperty("new"))
        {
            updated = json["new"].reverse();
            if(updated.length > 0)
            {
                let newarea = document.getElementById('updated');
                newarea.parentNode.style.display = null;
                updateDynamicList(newarea, updated);
            }
        }
        let date = (new Date(json['timestamp'])).toISOString();
        document.getElementById('timestamp').innerHTML += " " + date.split('T')[0] + " " + date.split('T')[1].split(':').slice(0, 2).join(':') + " UTC";
        timestamp = json['timestamp'];
    }catch{
        document.getElementById('timestamp').innerHTML = "";
    }
    getJSON("json/relation.json?" + timestamp, initRelation, function(unused){}, null);
    getJSON("json/data.json?" + timestamp, initIndex, initIndex, null);
}

function initIndex(unused)
{
    try{
        index = JSON.parse(this.response);
        index["lookup_reverse"] = Object.fromEntries(Object.entries(index["lookup"]).map(([key, value]) => [value, key]));
        result_area = document.getElementById('resultarea');
        let params = new URLSearchParams(window.location.search);
        let id = params.get("id");
        updateHistory(null, 0);
        if(id != null) lookup(id);
    }catch{
        getJSON("json/data.json?" + timestamp, initIndex, initIndex, null); // try again
    }
}

function initRelation(unused)
{
    relations = JSON.parse(this.response);
}

function updateQuery(id)
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

function getJSON(url, callback, err_callback, id) {
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
function loadIndexed(id, obj, shortened=false)
{
    let search_type;
    if(id.length == 10 || id.length == 14)
    {
        switch(id[0])
        {
            case '1':
                if(!shortened)
                {
                    newArea("Weapon", id, true);
                    search_type = 1;
                }
                break;
            case '2':
                newArea("Summon", id, true);
                search_type = 2;
                break;
            case '3':
                if(id[1] == '9')
                {
                    newArea("NPC", id, true);
                    search_type = 5;
                }
                else
                {
                    newArea("Character", id, true);
                    search_type = 3;
                }
                break;
            default:
                return;
        };
        last_id = id;
        updateQuery(id);
    }
    else if(id.length == 7)
    {
        newArea("Enemy", id, true);
        search_type = 4;
        updateQuery("e"+id);
    }
    else if(id.length == 6)
    {
        newArea("Main Character", id, (obj[7].length != 0));
        search_type = 0;
        updateQuery(id);
    }
    updateHistory(id, search_type);
    favButton(true, id, search_type);
    updateRelated(id);
    let assets = null;
    let skycompass = null;
    let mc_skycompass = false;
    let npcdata = null;
    let files = null;
    if(search_type == 4) // enemies
    {
        assets = [
            ["Big Icon", "sp/assets/enemy/m/", "png", "img/", 0, false, false],
            ["Small Icon", "sp/assets/enemy/s/", "png", "img/", 0, false, false],
            ["Sprite Sheets", "sp/cjs/", "png", "img_low/", 1, false, false],
            ["Raid Appear Sheets", "sp/cjs/", "png", "img_low/", 2, false, false],
            ["Attack Effect Sheets", "sp/cjs/", "png", "img_low/", 3, false, false],
            ["Charge Attack Sheets", "sp/cjs/", "png", "img_low/", 4, false, false]
        ];
    }
    else if(search_type == 3) // characters / skins
    {
        assets = [
            ["Main Arts", "sp/assets/npc/zoom/", "png", "img_low/", 5, true, false], // index, skycompass, side form
            ["Journal Arts", "sp/assets/npc/b/", "png", "img_low/", 5, false, false],
            ["Inventory Portraits", "sp/assets/npc/m/", "jpg", "img_low/", 5, false, false],
            ["Square Portraits", "sp/assets/npc/s/", "jpg", "img_low/", 5, false, false],
            ["Party Portraits", "sp/assets/npc/f/", "jpg", "img_low/", 5, false, false],
            ["Popup Portraits", "sp/assets/npc/qm/", "png", "img_low/", 5, false, false],
            ["Party Select Portraits", "sp/assets/npc/quest/", "jpg", "img/", 5, false, false],
            ["Tower Portraits", "sp/assets/npc/t/", "png", "img_low/", 5, false, false],
            ["Detail Banners", "sp/assets/npc/detail/", "png", "img_low/", 5, false, false],
            ["Sprites", "sp/assets/npc/sd/", "png", "img/", 6, false, false],
            ["Raid", "sp/assets/npc/raid_normal/", "jpg", "img/", 5, false, true],
            ["Twitter Arts", "sp/assets/npc/sns/", "jpg", "img_low/", 5, false, false],
            ["Charge Attack Cutins", "sp/assets/npc/cutin_special/", "jpg", "img_low/", 5, false, false],
            ["Chain Cutins", "sp/assets/npc/raid_chain/", "jpg", "img_low/", 5, false, false],
            ["Character Sheets", "sp/cjs/", "png", "img_low/", 0, false, false],
            ["Attack Effect Sheets", "sp/cjs/", "png", "img_low/", 1, false, false],
            ["Charge Attack Sheets", "sp/cjs/", "png", "img_low/", 2, false, false],
            ["AOE Skill Sheets", "sp/cjs/", "png", "img_low/", 5, false, false],
            ["Single Target Skill Sheets", "sp/cjs/", "png", "img_low/", 3, false, false]
        ];
        skycompass = ["https://media.skycompass.io/assets/customizes/characters/1138x1138/", ".png", true];
        npcdata = obj[7];
    }
    else if(search_type == 5) // npcs
    {
        assets = [
            ["Main Arts", "sp/assets/npc/zoom/", "png", "img_low/", -1, false, false], // index, skycompass, side form
            ["Journal Arts", "sp/assets/npc/b/", "png", "img_low/", -1, false, false],
            ["Inventory Portraits", "sp/assets/npc/m/", "jpg", "img_low/", -1, false, false]
        ];
        npcdata = obj[0];
        files = [id, id + "_01"];
    }
    else if(search_type == 2) // summons
    {
        assets = [
            ["Main Arts", "sp/assets/summon/b/", "png", "img_low/", 0, true, false], // index, skycompass, side form
            ["Home Arts", "sp/assets/summon/my/", "png", "img_low/", 0, false, false],
            ["Detail Arts", "sp/assets/summon/detail/", "png", "img_low/", 0, false, false],
            ["Inventory Portraits", "sp/assets/summon/m/", "jpg", "img_low/", 0, false, false],
            ["Square Portraits", "sp/assets/summon/s/", "jpg", "img_low/", 0, false, false],
            ["Main Summon Portraits", "sp/assets/summon/party_main/", "jpg", "img_low/", 0, false, false],
            ["Sub Summon Portraits", "sp/assets/summon/party_sub/", "jpg", "img_low/", 0, false, false],
            ["Raid Portraits", "sp/assets/summon/raid_normal/", "jpg", "img/", 0, false, false],
            ["Quest Portraits", "sp/assets/summon/qm/", "png", "img/", 0, false, false],
            ["Summon Call Sheets", "sp/cjs/", "png", "img_low/", 1, false, false],
            ["Summon Damage Sheets", "sp/cjs/", "png", "img_low/", 2, false, false]
        ];
        skycompass = ["https://media.skycompass.io/assets/archives/summons/", "/detail_l.png", false];
    }
    else if(search_type == 1) // weapons
    {
        assets = [
            ["Main Arts", "sp/assets/weapon/b/", "png", "img_low/", 0, false, false], // index, skycompass, side form
            ["Inventory Portraits", "sp/assets/weapon/m/", "jpg", "img_low/", 0, false, false],
            ["Square Portraits", "sp/assets/weapon/s/", "jpg", "img_low/", 0, false, false],
            ["Main Hand Portraits", "sp/assets/weapon/ls/", "jpg", "img_low/", 0, false, false],
            ["Battle Sprites", "sp/cjs/", "png", "img/", 0, false, false],
            ["Attack Effects", "sp/cjs/", "png", "img/", 1, false, false],
            ["Charge Attack Sheets", "sp/cjs/", "png", "img_low/", 2, false, false]
        ];
    }
    else if(search_type == 0) // MC
    {
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
    }
    if(assets != null)
    {
        for(let asset of assets)
        {
            files = (asset[4] == -1) ? files : obj[asset[4]]; // for npc
            if(files.length == 0) continue; // empty list
            if(shortened && asset[0] != "Attack Effects" && asset[0] != "Charge Attack Sheets") continue; // weapon sheet for mc
            if(search_type == 2 && asset[0] == "Quest Portraits") files = [files[0], files[0]+"_hard", files[0]+"_ex", files[0]+"_high"]; // summon quest icon
            let div = addResult(asset[0], asset[0]);
            result_area.appendChild(div);
            
            for(let file of files)
            {
                if(!asset[6] && (file.endsWith('_f') || file.endsWith('_f1'))) continue;
                let img = document.createElement("img");
                let ref = document.createElement('a');
                if(file.endsWith(".png") || file.endsWith(".jpg"))
                    img.src = protocol + getMainEndpoint() + language + asset[3] + asset[1] + file;
                else
                    img.src = protocol + getMainEndpoint() + language + asset[3] + asset[1] + file + "." + asset[2];
                ref.setAttribute('href', img.src.replace("img_low", "img"));
                img.classList.add("loading");
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.classList.remove("loading");
                    this.classList.add("asset");
                }
                div.appendChild(ref);
                ref.appendChild(img);
                if(skycompass != null && asset[5]) // skycompass
                {
                    img = document.createElement("img");
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
                    }
                    img.onload = function() {
                        this.classList.remove("loading");
                        this.classList.add("asset");
                        this.classList.add("skycompass");
                    }
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
            let div = addResult(asset[0], asset[0]);
            result_area.appendChild(div);
            for(let file of npcdata)
            {
                if(asset[0] == "Raid Bubble Arts" && file.endsWith('_up')) continue; // ignore those
                let img = document.createElement("img");
                let ref = document.createElement('a');
                img.src = protocol + getMainEndpoint() + language + asset[3] + asset[1] + id + file + "." + asset[2];
                ref.setAttribute('href', img.src.replace("img_low", "img"));
                img.classList.add("loading");
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.classList.remove("loading");
                    this.classList.add("asset");
                }
                div.appendChild(ref);
                ref.appendChild(img);
            }
        }
    }
    // non indexed
    else if(id.length >= 10 && id[0] == '3') // character npc files, at the end
    {
        lookupNPCChara(id, obj);
    }
}

function loadUnindexed(id)
{
    if(blacklist.includes(id)) return;
    if(id.length == 10 || id.length == 14)
    {
        switch(id[0])
        {
            case '1':
                lookupWeapon(id);
                break;
            case '2':
                lookupSummon(id);
                break;
            case '3':
                if(id[1] == '9')
                {
                    lookupNPC(id);
                }
                else
                {
                    lookupCharacter(id);
                }
                break;
            default:
                return;
        };
        last_id = id;
        updateQuery(id);
    }
    else if(id.length == 7)
    {
        lookupEnemy(id);
        last_id = id;
        updateQuery("e" + id);
    }
    else if(id.length == 9 && id[6] == "_") // retrocompatibility
    {
        id = id.split('_')[0]
        lookupMC(id);
        last_id = id;
        updateQuery(id);
    }
    else if(id.length == 6)
    {
        lookupMC(id);
        last_id = id;
        updateQuery(id);
    }
    updateRelated(id);
}

function lookup(id)
{
    if(blacklist.includes(id)) return;
    main_endp_count = -1;
    document.getElementById('results').style.display = "none";
    f = document.getElementById('filter');
    let el = id.split("_");
    if(
        (el.length == 2 && el[1] == "st2" && el[0].length == 10 && !isNaN(el[0]) && id != last_id) || (el.length == 1 && el[0].length == 10 && !isNaN(el[0]) && id != last_id) || 
        (id.length == 8 && id.toLowerCase()[0] === 'e' && !isNaN(id.slice(1)) && id.slice(1) != last_id) ||
        (id.length == 9 && id.toLowerCase()[6] === '_' && !isNaN(id.slice(0, 6)) && id != last_id) || // retrocompatibility
        (id.length == 6 && !isNaN(id))
    )
    {
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
        else if(start == "30") check = "characters";
        else if(start == "39") check = "npcs";
        else if(start == "37") check = "skins";
        else if(start == "20") check = "summons";
        else if(start == "10") check = "weapons";
        else if(id.length == 9 && id[6] == "_")
        {
            id = id.split('_')[0];
            check = "job";
        }
        else if(id.length == 6) check = "job";
        favButton(false, null, null);
        if(check != null && id in index[check] && index[check][id] !== 0)
            loadIndexed(id, index[check][id]);
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
                }
            }
            loadUnindexed(id);
        }
    }
    else
    {
        let results = document.getElementById('results');
        results.innerHTML = "";
        if(id == "") return;
        let words = id.toLowerCase().split(' ');
        console.log(words);
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
            console.log(t);
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
            }
            div.appendChild(i);
        }
    }
    if(!indexed)
    {
        div.appendChild(document.createElement('br'));
        div.appendChild(document.createTextNode("This element isn't indexed, assets might be missing"));
    }
}

function addResult(identifier, name)
{
    let div = document.createElement("div");
    div.classList.add("result");
    if(identifier == "Result Header") div.classList.add("result-header");
    div.setAttribute("data-id", identifier);
    div.appendChild(document.createTextNode(name));
    div.appendChild(document.createElement("br"));
    result_area.appendChild(div);
    return div;
}

function lookupCharacter(character_id) // old and slow, avoid using this
{
    if(blacklist.includes(character_id)) return;
    let el = character_id.split("_");
    character_id = el[0];
    style = "";
    if(el.length > 1) style = "_"+el[1];
    // add manual style later?
    
    let assets = [
        ["Main Arts", "sp/assets/npc/zoom/", "png", "img_low/", false, true, false, true], // skin folder, gendered/multi, spritesheet, bonus
        ["Journal Arts", "sp/assets/npc/b/", "png", "img_low/", false, true, false, true],
        ["Inventory Portraits", "sp/assets/npc/m/", "jpg", "img_low/", false, true, false, true],
        ["Square Portraits", "sp/assets/npc/s/", "jpg", "img_low/", true, true, false, true],
        ["Party Portraits", "sp/assets/npc/f/", "jpg", "img_low/", true, true, false, true],
        ["Popup Portraits", "sp/assets/npc/qm/", "png", "img_low/", true, true, false, true],
        ["Party Select Portraits", "sp/assets/npc/quest/", "jpg", "img/", true, true, false, true],
        ["Tower Portraits", "sp/assets/npc/t/", "png", "img_low/", true, true, false, true],
        ["Detail Banners", "sp/assets/npc/detail/", "png", "img_low/", true, true, false, true],
        ["Sprites", "sp/assets/npc/sd/", "png", "img/", false, false, false, false],
        ["Raid", "sp/assets/npc/raid_normal/", "jpg", "img/", false, true, false, true],
        ["Twitter Arts", "sp/assets/npc/sns/", "jpg", "img_low/", false, true, false, true],
        ["Charge Attack Cutins", "sp/assets/npc/cutin_special/", "jpg", "img_low/", false, true, false, true],
        ["Chain Cutins", "sp/assets/npc/raid_chain/", "jpg", "img_low/", false, true, false, true],
        ["Character Sheets", "sp/cjs/npc_", "png", "img_low/", false, false, true, false],
        ["Attack Effect Sheets", "sp/cjs/phit_", "png", "img_low/", false, false, true, false],
        ["Charge Attack Sheets", "sp/cjs/nsp_", "png", "img_low/", false, false, true, false],
        ["AOE Skill Sheets", "sp/cjs/ab_all_", "png", "img_low/", false, false, true, false],
        ["Single Target Skill Sheets", "sp/cjs/ab_", "png", "img_low/", false, false, true, false]
    ];
    let uncaps = ["_01", "_02"];
    if(character_id[1] != '0') uncaps = ["_01"];
    let styles = ["", "_st2"];
    let bonus = ["_81", "_82", "_83", "_91"];
    let alts = ["", "_f", "_f1", "_f_01"];
    
    
    let is_character_skin = character_id[1] == '7';
    newArea("Character", character_id, true, false);
    for(let asset of assets)
    {
        let uncap_append = asset[7] ? uncaps.concat(bonus) : uncaps;
        let alt_append = asset[0].includes("Sheets") ? alts : [""];
        let skin_folders = (is_character_skin && asset[4]) ? ["", "skin/"] : [""];
        let skin_appends = (is_character_skin && asset[4]) ? ["", "_s1", "_s2", "_s3", "_s4", "_s5", "_s6"] : [""];
        let gendered = asset[5] ? ["", "_0", "_1"] : [""];
        let multi = asset[5] ? ["", "_101", "_102", "_103", "_104", "_105"] : [""];
        let sheet = asset[6] ? ((asset[1].includes("nsp_") || asset[1].includes("npc_")) ? ["", "_s2", "_s3", "_a", "_s2_a", "_s3_a", "_b", "_s2_b", "_s3_b", "_c", "_s2_c", "_s3_c"] : ["", "_a", "_b", "_c"]) : [""];
        let extra = [""];
        
        // lyria / young cat fix
        if(null_characters.includes(character_id))
        {
            multi = [""];
            if(asset[0].includes("Portraits") || asset[0].includes("Chain")) extra = ["", "_01", "_02", "_03", "_04", "_05", "_06"];
            else if(asset[0].includes("Twitter") || asset[0].includes("Sheets")) extra = [""];
            else if(!is_character_skin) extra = ["_01"];
            else extra = [""];
        }
        
        // phit fix
        if(asset[0] === "Attack Effect Sheets") uncap_append = [""];
        
        // skill fix
        if(asset[0].includes("Skill"))
        {
            uncap_append = [""];
            alt_append = ["_01", "_02", "_03", "_04", "_05", "_06", "_07", "_08"];
        }
        
        let div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let uncap of uncap_append)
        {
            if(uncap != "_01") style_append = [""]; // style limited to _01 for now
            for(let alt of alt_append)
            {
                for(let gender of gendered)
                {
                    for(let unit of multi)
                    {
                        for(let ex of extra)
                        {
                            for(let s_f of skin_folders)
                            {
                                for(let s_a of skin_appends)
                                {
                                    for(let sh of sheet)
                                    {
                                        if(s_a != "" && s_f == "") continue;
                                        let path = asset[1] + s_f + character_id + uncap + style + alt + gender + unit + ex + s_a + sh + "." + asset[2];
                                        let img = document.createElement("img");
                                        let ref = document.createElement('a');
                                        ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                                        div.appendChild(ref);
                                        ref.appendChild(img);
                                        img.classList.add("loading");
                                        img.onerror = function() {
                                            let result = this.parentNode.parentNode;
                                            this.parentNode.remove();
                                            this.remove();
                                            if(result.childNodes.length <= 2) result.remove();
                                        }
                                        img.onload = function() {
                                            this.classList.remove("loading");
                                            this.classList.add("asset");
                                        }
                                        img.src = protocol + getMainEndpoint() + language + asset[3] + path;
                                        // sky compass band aid
                                        if(asset[0] === "Main Arts")
                                        {
                                            let path = character_id + uncap + style + alt + gender + unit + s_a + sh + "." + asset[2];
                                            let img = document.createElement("img");
                                            let ref = document.createElement('a');
                                            ref.setAttribute('href', "https://media.skycompass.io/assets/customizes/characters/1138x1138/" + path);
                                            div.appendChild(ref);
                                            ref.appendChild(img);
                                            img.classList.add("loading");
                                            img.onerror = function() {
                                                let result = this.parentNode.parentNode;
                                                this.parentNode.remove();
                                                this.remove();
                                                if(result.childNodes.length <= 2) result.remove();
                                            }
                                            img.onload = function() {
                                                this.classList.remove("loading");
                                                this.classList.add("asset");
                                                this.classList.add("skycompass");
                                            }
                                            img.src = "https://media.skycompass.io/assets/customizes/characters/1138x1138/" + path;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    // character npc files, at the end
    lookupNPCChara(character_id);
}

function lookupNPCChara(character_id, chara_data = null)
{
    let uncaps = [""];
    if(chara_data != null)
    {
        for(let el of chara_data[5])
        {
            let u = '_'+el.split('.')[0].split(character_id.split('_')[0])[1].split('_')[1];
            if(u != '_01' && !u.startsWith('_8') && !u.includes('f')) uncaps.push(u);
        }
    }
    else
    {
        uncaps = ["", "_02"];
    }
    let assets = [
        ["Raid Bubble Arts", "sp/raid/navi_face/", "png", "img/"],
        ["Scene Arts", "sp/quest/scene/character/body/", "png", "img_low/"]
    ];
    
    let expressions = ["", "_laugh", "_laugh2", "_laugh3", "_wink", "_shout", "_shout2", "_sad", "_sad2", "_angry", "_angry2", "_school", "_shadow", "_close", "_serious", "_serious2", "_surprise", "_surprise2", "_think", "_think2", "_serious", "_serious2", "_ecstasy", "_ecstasy2", "_ef", "_body", "_speed2", "_suddenly", "_shy", "_shy2", "_weak"];
    let variationsA = ["", "_battle"];
    let variationsB = ["", "_speed", "_up"]
    let others = ["_up_speed"];
    let specials = ["_valentine", "_valentine_a", "_a_valentine", "_valentine2", "_valentine3", "_white", "_whiteday", "_whiteday2", "_whiteday3"]
    let scene_alts = [];
    for(let uncap of uncaps)
        for(let A of variationsA)
            for(let ex of expressions)
                for(let B of variationsB)
                    scene_alts.push(uncap+A+ex+B);
    scene_alts = scene_alts.concat(others, specials);
    
    for(let asset of assets)
    {
        let div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        
        let iterations =  (asset[0] != "Scene Arts") ? [].concat(expressions, others) : scene_alts;
        for(let scene of iterations)
        {
            let path = asset[1] +  character_id + scene + "." + asset[2];
            let img = document.createElement("img");
            let ref = document.createElement('a');
            ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
            div.appendChild(ref);
            ref.appendChild(img);
            img.classList.add("loading");
            img.onerror = function() {
                let result = this.parentNode.parentNode;
                this.parentNode.remove();
                this.remove();
                if(result.childNodes.length <= 2) result.remove();
            }
            img.onload = function() {
                this.classList.remove("loading");
                this.classList.add("asset");
            }
            img.src = protocol + getMainEndpoint() + language + asset[3] + path;
        }
    }
}

function lookupNPC(npc_id)
{
    if(blacklist.includes(npc_id)) return;
    let assets = [
        ["Main Arts", "sp/assets/npc/zoom/", "png", "img_low/"],
        ["Journal Arts", "sp/assets/npc/b/", "png", "img_low/"],
        ["Inventory Portraits", "sp/assets/npc/m/", "jpg", "img_low/"],
        ["Raid Bubble Arts", "sp/raid/navi_face/", "png", "img/"],
        ["Scene Arts", "sp/quest/scene/character/body/", "png", "img_low/"]
    ];
    let expressions = ["", "_laugh", "_laugh2", "_laugh3", "_wink", "_shout", "_shout2", "_sad", "_sad2", "_angry", "_angry2", "_school", "_shadow", "_close", "_serious", "_serious2", "_surprise", "_surprise2", "_think", "_think2", "_serious", "_serious2", "_suddenly", "_suddenly2", "_ecstasy", "_ecstasy2", "_ef", "_body", "_speed2"];
    let variationsA = ["", "_battle"];
    let variationsB = ["", "_speed", "_up"]
    let others = ["_up_speed"];
    let specials = ["_valentine", "_valentine_a", "_a_valentine", "_valentine2", "_valentine3", "_white", "_whiteday", "_whiteday2", "_whiteday3"]
    let scene_alts = [];
    for(let uncap of [""])
        for(let A of variationsA)
            for(let ex of expressions)
                for(let B of variationsB)
                    scene_alts.push(uncap+A+ex+B);
    scene_alts = scene_alts.concat(others, specials);
    
    newArea("NPC", npc_id, true, false);
    for(let asset of assets)
    {
        let div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);

        let iterations = ["", "_01"];
        if(asset[0] == "Raid Bubble Arts") iterations = [].concat(expressions, others);
        else if(asset[0] == "Scene Arts") iterations = scene_alts.slice();
        for(let scene of iterations)
        {
            let path = asset[1] + npc_id + scene + "." + asset[2];
            let img = document.createElement("img");
            let ref = document.createElement('a');
            ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
            div.appendChild(ref);
            ref.appendChild(img);
            img.classList.add("loading");
            img.onerror = function() {
                let result = this.parentNode.parentNode;
                this.parentNode.remove();
                this.remove();
                if(result.childNodes.length <= 2) result.remove();
            }
            img.onload = function() {
                this.classList.remove("loading");
                this.classList.add("asset");
            }
            img.src = protocol + getMainEndpoint() + language + asset[3] + path;
        }
    }
}

function lookupSummon(summon_id)
{
    if(blacklist.includes(summon_id)) return;
    assets = [
        ["Main Arts", "sp/assets/summon/b/", "png", "img_low/"],
        ["Home Arts", "sp/assets/summon/my/", "png", "img_low/"],
        ["Detail Arts", "sp/assets/summon/detail/", "png", "img_low/"],
        ["Inventory Portraits", "sp/assets/summon/m/", "jpg", "img_low/"],
        ["Square Portraits", "sp/assets/summon/s/", "jpg", "img_low/"],
        ["Main Summon Portraits", "sp/assets/summon/party_main/", "jpg", "img_low/"],
        ["Sub Summon Portraits", "sp/assets/summon/party_sub/", "jpg", "img_low/"],
        ["Raid Portraits", "sp/assets/summon/raid_normal/", "jpg", "img/"],
        ["Quest Portraits", "sp/assets/summon/qm/", "png", "img/"],
        ["Summon Call Sheets", "sp/cjs/summon_", "png", "img_low/"],
        ["Summon Damage Sheets", "sp/cjs/summon_", "png", "img_low/"]
    ];
    let multi_summons = ['2040414000']
    let uncaps = ["", "_01", "_02", "_03"];
    let sheets = [""];
    let uncap_append = [];
    
    newArea("Summon", summon_id, true, false);
    for(let asset of assets)
    {
        if(asset[0].includes('Sheets'))
        {
            let typestring = asset[0].includes('Call') ? "_attack" : "_damage";
            if(multi_summons.includes(summon_id))
            {
                let capp = JSON.parse(JSON.stringify(uncaps));
                let multistrings = ["", "_a", "_b", "_c", "_d", "_e", "_f"];
                uncap_append = []
                for(let m of multistrings)
                {
                    for(let ca of capp)
                    {
                        uncap_append.push(ca + m + typestring);
                    }
                }
            }
            else
            {
                uncap_append = JSON.parse(JSON.stringify(uncaps));
                for(let i = 0; i < uncap_append.length; ++i)
                    uncap_append[i] += typestring;
            }
            sheets = ["", "_a", "_b", "_c", "_d", "_e", "_f", "_bg", "_bg1", "_bg2", "_bg3"];
        }
        else if(asset[0] == "Quest Portraits")
        {
            sheets = ["", "_hard", "_ex", "_high"];
            uncap_append = uncaps;
        }
        else
        {
            sheets = [""];
            uncap_append = uncaps;
        }
        
        let div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let uncap of uncap_append)
        {
            for(let sheet of sheets)
            {
                let path = asset[1] + summon_id + uncap + sheet + "." + asset[2];
                let img = document.createElement("img");
                let ref = document.createElement('a');
                ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                div.appendChild(ref);
                ref.appendChild(img);
                img.classList.add("loading");
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.classList.remove("loading");
                    this.classList.add("asset");
                }
                img.src = protocol + getMainEndpoint() + language + asset[3] + path;
            }
        }
        // sky compass band aid
        if(asset[0] === "Main Arts")
        {
            let img = document.createElement("img");
            let ref = document.createElement('a');
            ref.setAttribute('href', "https://media.skycompass.io/assets/archives/summons/" + summon_id + "/detail_l.png");
            div.appendChild(ref);
            ref.appendChild(img);
            img.classList.add("loading");
            img.onerror = function() {
                let result = this.parentNode.parentNode;
                this.parentNode.remove();
                this.remove();
                if(result.childNodes.length <= 2) result.remove();
            }
            img.onload = function() {
                this.classList.remove("loading");
                this.classList.add("asset");
                this.classList.add("skycompass");
            }
            img.src = "https://media.skycompass.io/assets/archives/summons/" + summon_id + "/detail_l.png";
        }
    }
}

function lookupWeapon(weapon_id, shortened=false)
{
    if(blacklist.includes(weapon_id)) return;
    let assets = [
        ["Main Arts", "sp/assets/weapon/b/", "png", "img_low/"],
        ["Inventory Portraits", "sp/assets/weapon/m/", "jpg", "img_low/"],
        ["Square Portraits", "sp/assets/weapon/s/", "jpg", "img_low/"],
        ["Main Hand Portraits", "sp/assets/weapon/ls/", "jpg", "img_low/"],
        ["Battle Sprites", "sp/cjs/", "png", "img/"],
        ["Attack Effects", "sp/cjs/phit_", "png", "img/"],
        ["Charge Attack Sheets", "sp/cjs/sp_", "png", "img_low/"]
    ];
    let appends = [""];
    let sheets = [""];
    
    if(!shortened) newArea("Weapon", weapon_id, true, false);
    for(let asset of assets)
    {
        if(shortened && asset[0] != "Attack Effects" && asset[0] != "Charge Attack Sheets") continue;
        switch(asset[0])
        {
            case "Battle Sprites":
                appends = ["", "_1", "_2"];
                sheets = [""];
                break;
            case "Attack Effects":
                appends = ["", "_f1", "_1", "_1_f1", "_2", "_2_f1"];
                sheets = ["", "_a", "_b", "_c", "_d", "_e"];
                break;
            case "Charge Attack Sheets":
                appends = ["", "_f1", "_1", "_1_f1", "_2", "_2_f1", "_0_s2", "_s2", "_f1_s2", "_1_s2", "_1_f1_s2", "_2_s2", "_2_f1_s2"];
                sheets = ["", "_a", "_b", "_c", "_d", "_e"];
                break;
            default:
                appends = [""];
                sheets = [""];
        };
        
        let div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let append of appends)
        {
            for(let sheet of sheets)
            {
                let path = asset[1] + weapon_id + append + sheet + "." + asset[2];
                let img = document.createElement("img");
                let ref = document.createElement('a');
                ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                div.appendChild(ref);
                ref.appendChild(img);
                img.classList.add("loading");
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.classList.remove("loading");
                    this.classList.add("asset");
                }
                img.src = protocol + getMainEndpoint() + language + asset[3] + path;
            }
        }
    }
}

function lookupEnemy(enemy_id)
{
    if(blacklist.includes(enemy_id)) return;
    let assets = [
        ["Big Icon", "sp/assets/enemy/m/", "png", "img/"],
        ["Small Icon", "sp/assets/enemy/s/", "png", "img/"],
        ["Sprite Sheets", "sp/cjs/enemy_", "png", "img_low/"],
        ["Raid Appear Sheets", "sp/cjs/raid_appear_", "png", "img_low/"],
        ["Attack Effect Sheets", "sp/cjs/ehit_", "png", "img_low/"],
        ["Charge Attack Sheets", "sp/cjs/esp_", "png", "img_low/"]
    ];
    let appends = [""];
    let sheets = [""];
    
    newArea("Enemy", enemy_id, false, false);
    for(let asset of assets)
    {
        sheets = asset[0].includes("Sheets") ? ["", "_a", "_b", "_c", "_d", "_e"] : [""];
        appends = asset[0].includes("Charge Attack") ? ["_01", "_02", "_03", "_04", "_05", "_06", "_07", "_08", "_09", "_10", "_11", "_12", "_13", "_14", "_15", "_16", "_17", "_18", "_19", "_20"] : [""];
        if(asset[0].includes("Icon")) appends = ["", "_a"];
        
        let div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let append of appends)
        {
            for(let sheet of sheets)
            {
                let path = asset[1] + enemy_id + append+sheet + "." + asset[2];
                let img = document.createElement("img");
                let ref = document.createElement('a');
                ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                div.appendChild(ref);
                ref.appendChild(img);
                img.classList.add("loading");
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.classList.remove("loading");
                    this.classList.add("asset");
                }
                img.src = protocol + getMainEndpoint() + language + asset[3] + path;
            }
        }
    }
}

function lookupMC(mc_id)
{
    if(blacklist.includes(mc_id)) return;
    let assets = [
        ["Job Icons", "sp/ui/icon/job/", "png", "img/", 0],
        ["Inventory Portraits", "sp/assets/leader/m/", "jpg", "img/", 1],
        ["Outfit Portraits", "sp/assets/leader/sd/m/", "jpg", "img/", 1],
        ["Outfit Description Arts", "sp/assets/leader/skin/", "png", "img_low/", 1],
        ["Home Arts", "sp/assets/leader/my/", "png", "img_low/", 2],
        ["Full Arts", "sp/assets/leader/job_change/", "png", "img_low/", 2],
        ["Outfit Preview Arts", "sp/assets/leader/skin/", "png", "img_low/", 2],
        ["Class Name Party Texts", "sp/ui/job_name/job_list/", "png", "img/", 0],
        ["Class Name Master Texts", "sp/assets/leader/job_name_ml/", "png", "img/", 0],
        ["Class Change Buttons", "sp/assets/leader/jlon/", "png", "img/", 2],
        ["Party Class Big Portraits", "sp/assets/leader/jobon_z/", "png", "img_low/", 2],
        ["Party Class Portraits", "sp/assets/leader/p/", "png", "img_low/", 2],
        ["Profile Portraits", "sp/assets/leader/pm/", "png", "img_low/", 2],
        ["Profile Board Portraits", "sp/assets/leader/talk/", "png", "img/", 2],
        ["Party Select Portraits", "sp/assets/leader/quest/", "jpg", "img/", 2],
        ["Tower Portraits", "sp/assets/leader/t/", "png", "img_low/", 2],
        ["Raid Portraits", "sp/assets/leader/raid_normal/", "jpg", "img/", 2],
        ["Raid Log Portraits", "sp/assets/leader/raid_log/", "png", "img/", 2],
        ["Raid Result Portraits", "sp/assets/leader/result_ml/", "jpg", "img_low/", 2],
        ["Mastery Portraits", "sp/assets/leader/zenith/", "png", "img_low/", 2],
        ["Master Level Portraits", "sp/assets/leader/master_level/", "png", "img_low/", 2],
        ["Sprites", "sp/assets/leader/sd/", "png", "img/", 2]
    ];
    newArea("Main Character", mc_id, false, false);
    for(let asset of assets)
    {
        let div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        let variations = null;
        switch(asset[4])
        {
            case 1: variations = ['_01']; break
            case 2:
                variations = [];
                for(let mh of ['sw', 'wa', 'kn', 'me', 'bw', 'mc', 'sp', 'ax', 'gu', 'kt'])
                {
                    variations.push("_"+mh+'_0_01');
                    variations.push("_"+mh+'_1_01');
                }
                break;
            default: variations = ['']; break
        }
        for(let vr of variations)
        {
            let path = asset[1] + mc_id + vr + "." + asset[2];
            let img = document.createElement("img");
            let ref = document.createElement('a');
            ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
            div.appendChild(ref);
            ref.appendChild(img);
            img.classList.add("loading");
            img.onerror = function() {
                let result = this.parentNode.parentNode;
                this.parentNode.remove();
                this.remove();
                if(result.childNodes.length <= 2) result.remove();
            }
            img.onload = function() {
                this.classList.remove("loading");
                this.classList.add("asset");
            }
            img.src = protocol + getMainEndpoint() + language + asset[3] + path;
        }
        for(let i = 0; i < 2; ++i)
        {
            // sky compass band aid
            if(asset[0] === "Home Art")
            {
                let path = mc_id + "_" + i + "." + asset[2];
                let img = document.createElement("img");
                let ref = document.createElement('a');
                ref.setAttribute('href', "https://media.skycompass.io/assets/customizes/jobs/1138x1138/" + path);
                div.appendChild(ref);
                ref.appendChild(img);
                img.classList.add("loading");
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.classList.remove("loading");
                    this.classList.add("asset");
                    this.classList.add("skycompass");
                }
                img.src = "https://media.skycompass.io/assets/customizes/jobs/1138x1138/" + path;
            }
        }
    }
}

// =================================================================================================
// bookmark, history, relation
function updateDynamicList(dynarea, idlist)
{
    for(let e of idlist)
    {
        switch(e[1])
        {
            case 3: // character, skin, ...
            {
                if(e[0].includes('_st'))
                    addIndexImage(dynarea, "sp/assets/npc/m/" + e[0].split('_')[0] + "_01_" + e[0].split('_')[1] + ".jpg", e[0]);
                else
                    addIndexImage(dynarea, "sp/assets/npc/m/" + e[0] + "_01.jpg", e[0]);
                break;
            }
            case 2: // summon
            {
                addIndexImage(dynarea, "sp/assets/summon/m/" + e[0] + ".jpg", e[0]);
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
                let onerr = function() {
                    this.onerror = function() {
                        this.remove();
                    }
                    this.src = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/quest/scene/character/body/"+this.src.split('/').slice(-1)[0].split('_')[0]+".png";
                    this.className = "preview";
                }
                addIndexImage(dynarea, "sp/assets/npc/m/" + e[0] + "_01.jpg", e[0], onerr);
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
    catch
    {
        bookmarks = [];
    }
    navigator.clipboard.writeText(JSON.stringify(bookmarks));
    let div = document.createElement('div');
    div.className = 'popup';
    div.textContent ='Bookmarks have been copied'
    document.body.appendChild(div)
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
                if(typeof e != 'object' || e.length != 2 || typeof e[0] != 'string' || typeof e[1] != 'number') return
                if(last_id == e[0]) fav = true;
                ++i;
            }
            bookmarks = tmp;
            localStorage.setItem("bookmark", JSON.stringify(bookmarks));
            if(fav) document.getElementById('favorite').src = "assets/ui/fav_1.png";
            else document.getElementById('favorite').src = "assets/ui/fav_0.png";
            let div = document.createElement('div');
            div.className = 'popup';
            div.textContent ='Bookmarks have been imported with success'
            document.body.appendChild(div)
            intervals.push(setInterval(rmPopup, 2500, div));
            updateBookmark();
        }
        catch {}
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
    catch
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
        lastsearches = localStorage.getItem("history");
        if(lastsearches == null)
        {
            lastsearches = [];
        }
        else
        {
            lastsearches = JSON.parse(lastsearches);
        }
    }
    catch
    {
        lastsearches = [];
    }
    if(id != null)
    {
        for(let e of lastsearches)
        {
            if(e[0] == id) return; // don't update if already in
        }
        lastsearches.push([id, search_type]);
        localStorage.setItem("history", JSON.stringify(lastsearches));
    }
    if(lastsearches.length == 0)
    {
        document.getElementById('history').parentNode.style.display = "none";
        return;
    }
    else if(lastsearches.length > 10)
    {
        lastsearches = lastsearches.slice(lastsearches.length - 10);
    }
    let histarea = document.getElementById('history');
    histarea.parentNode.style.display = null;
    histarea.innerHTML = "";
    updateDynamicList(histarea, lastsearches);
    histarea.appendChild(document.createElement("br"));
    let btn = document.createElement("button");
    btn.innerHTML = "Clear";
    btn.onclick = clearHistory;
    histarea.appendChild(btn);
}

function updateRelated(id)
{
    let relarea = document.getElementById('related');
    if(id in relations)
    {
        relarea.parentNode.style.display = relations[id].length > 0 ? null : "none";
        relarea.innerHTML = "";
        for(let e of relations[id])
        {
            let indice = -1;
            if(e[0] == 'e') indice = 4;
            else if(e.startsWith('39')) indice = 5;
            else if(e.includes('_') && !e.includes('_st')) indice = 0;
            else indice = parseInt(e[0]);
            switch(indice)
            {
                case 3: // character, skin, ...
                {
                    if(e.includes('_st'))
                        addIndexImage(relarea, "sp/assets/npc/m/" + e.split('_')[0] + "_01_" + e.split('_')[1] + ".jpg", e);
                    else
                        addIndexImage(relarea, "sp/assets/npc/m/" + e + "_01.jpg", e);
                    break;
                }
                case 2: // summon
                {
                    addIndexImage(relarea, "sp/assets/summon/m/" + e + ".jpg", e);
                    break;
                }
                case 1: // summon
                {
                    addIndexImage(relarea, "sp/assets/weapon/m/" + e + ".jpg", e);
                    break;
                }
                case 0: // mc
                {
                    addIndexImage(relarea, "sp/assets/leader/m/" + e.split('_')[0] + "_01.jpg", e);
                    break;
                }
                case 4: // enemy
                {
                    addIndexImage(relarea, "sp/assets/enemy/m/" + e + ".png", "e" + e);
                    break;
                }
                case 5: // npc
                {
                    let onerr = function() {
                        this.onerror = null;
                        this.src = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/quest/scene/character/body/"+this.src.split('/').slice(-1)[0].split('_')[0]+".png";
                        this.className = "preview";
                    }
                    addIndexImage(relarea, "sp/assets/npc/m/" + e + "_01.jpg", e, onerr);
                    break;
                }
            }
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
        }
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
    }
    img.src = protocol + getIndexEndpoint(parseInt(id.replace(/\D/g,''))) + language + quality + path;
}

function displayCharacters(elem, i)
{
    i = JSON.stringify(i);
    elem.removeAttribute("onclick");
    let node = document.getElementById('areacharacters'+i);
    if("characters" in index)
    {
        let slist = {};
        for(const id in index["characters"])
        {
            if(id[2] != i) continue;
            let el = id.split("_");
            if(el.length == 2)
                slist[id.padEnd(15, "0")] = ["sp/assets/npc/m/" + el[0] + "_01_" + el[1] + ".jpg", id];
            else
                slist[id.padEnd(15, "0")] = ["sp/assets/npc/m/" + id + "_01.jpg", id];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1]);
    }
    this.onclick = null;
}

function displaySummons(elem, i)
{
    i = JSON.stringify(i);
    elem.removeAttribute("onclick");
    let node = document.getElementById('areasummons'+i);
    if("summons" in index)
    {
        let slist = {};
        for(const id in index["summons"])
        {
            if(id[2] != i) continue;
            slist[id] = ["sp/assets/summon/m/" + id + ".jpg", id];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1]);
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

function displaySkins(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areaskins');
    if("skins" in index)
    {
        let slist = {};
        for(const id in index["skins"])
        {
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

function displayNPC(elem, i)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areanpc'+i);
    let start = 3990000000 + i * 1000;
    let end = start + 499000;
    let onerr = function() {
        this.onerror = function() {
            this.remove();
        }
        this.src = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/quest/scene/character/body/"+this.src.split('/').slice(-1)[0].split('_')[0]+".png";
        this.className = "preview";
    }
    if("npcs" in index)
    {
        let slist = {};
        for(const id in index["npcs"])
        {
            let t = parseInt(id);
            if(t < start || t > end) continue;
            slist[id] = ["sp/assets/npc/m/" + id + "_01.jpg", id];
        }
        const keys = Object.keys(slist).sort();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1], onerr);
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

function addIndexImageGeneric(node, path, id, onerr = null)
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
        this.classList.add("preview");
    }
    if(onerr == null)
    {
        img.onerror = function() {
            this.parentNode.remove();
            this.remove();
        }
    }
    else img.onerror = onerr;
    img.src = protocol + getIndexEndpoint(parseInt(id.replace(/\D/g,''))) + language + "img_low/" + path;
    a.href = img.src.replace("img_low/", "img/")
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