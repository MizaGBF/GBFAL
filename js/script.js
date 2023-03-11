/* sky compass notes (for posterity)

Leader: https://media.skycompass.io/assets/customizes/jobs/1138x1138/ID_GENDER.png
Character: https://media.skycompass.io/assets/customizes/characters/1138x1138/ID_UNCAP.png
Summon: https://media.skycompass.io/assets/archives/summons/ID/detail_l.png
Event: https://media.skycompass.io/assets/archives/events/ID/image/NUM_free.png

*/

var protocol = "https://";
var endpoints = [
    "prd-game-a1-granbluefantasy.akamaized.net/"
];
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

function getEndpoint()
{
    return endpoints[0];
}

function filter()
{
    lookup(document.getElementById('filter').value.trim().toLowerCase());
}

function init()
{
    getJSON("data.json?" + Date.now(), loadData, function(unused){}, null);
    result_area = document.getElementById('resultarea');
    let params = new URLSearchParams(window.location.search);
    let id = params.get("id");
    if(id != null) lookup(id);
}

function loadData(unused)
{
    index = JSON.parse(this.response);
    for(let key in index)
    {
        if(key != "version")
        {
            index[key].sort();
            index[key].reverse();
        }
    }
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

function successJSON(id)
{
    let obj = JSON.parse(this.response);
    if(id.length == 10 || id.length == 14)
    {
        switch(id[0])
        {
            case '1':
                newArea("Weapon", id, true);
                break;
            case '2':
                newArea("Summon", id, true);
                break;
            case '3':
                if(id[1] == '9') newArea("NPC", id, true);
                else newArea("Character", id, true);
                break;
            default:
                return;
        };
        last_id = id;
        updateQuery(id);
    }
    else if(id.length == 7)
        newArea("Enemy", id, false);
    else if(id.length == 9)
        newArea("Main Character", id, false);
    
    for(let key of Object.keys(obj))
    {
        let paths = obj[key];
        if(paths.length == 0) continue;
        let div = addResult(key, key);
        result_area.appendChild(div);

        for(let path of paths)
        {
            let img = document.createElement("img");
            let ref = document.createElement('a');
            if(path.includes("media.skycompass.io"))
            {
                ref.setAttribute('href', path);
                img.src = path;
                img.className  = "skycompass";
            }
            else
            {
                ref.setAttribute('href', protocol + getEndpoint() + language + path.replace("img_low", "img"));
                img.src = protocol + getEndpoint() + language + path;
            }
            img.id  = "loading";
            img.onerror = function() {
                let result = this.parentNode.parentNode;
                this.parentNode.remove();
                this.remove();
                if(result.childNodes.length <= 2) result.remove();
            }
            img.onload = function() {
                this.id = "done"
            }
            div.appendChild(ref);
            ref.appendChild(img);
        }
    }
}

function failJSON(id)
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
                if(id[1] == '9') lookupNPC(id);
                else lookupCharacter(id);
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
    else if(id.length == 9)
    {
        if(id[5] != '1')
            id = id.slice(0, 5) + "1" + id.slice(6);
        lookupMC(id);
        last_id = id;
        updateQuery(id);
    }
}

function lookup(id)
{
    if(blacklist.includes(id)) return;
    counter = 0;
    f = document.getElementById('filter');
    let el = id.split("_");
    if(
        (el.length == 2 && el[1] == "st2" && el[0].length == 10 && !isNaN(el[0]) && id != last_id) || (el.length == 1 && el[0].length == 10 && !isNaN(el[0]) && id != last_id) || 
        (id.length == 8 && id.toLowerCase()[0] === 'e' && !isNaN(id.slice(1)) && id.slice(1) != last_id) ||
        (id.length == 9 && id.toLowerCase()[6] === '_' && !isNaN(id.slice(0, 6)) && id != last_id)
    )
    {
        if(f.value == "") f.value = id;
        if(id.toLowerCase()[0] === 'e') id = id.slice(1);
        getJSON("data/" + id + ".json?" + Date.now(), successJSON, failJSON, id);
    }
}

function newArea(name, id, include_link)
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
        
        if(id.slice(0, 3) == "302" || id.slice(0, 3) == "303" || id.slice(0, 3) == "304" || id.slice(0, 3) == "371")
        {
            div.appendChild(document.createElement('br'));
            l = document.createElement('a');
            l.setAttribute('href', "https://mizagbf.github.io/GBFAP/?id=" + id);
            l.appendChild(document.createTextNode("Animation"));
            div.appendChild(l);
        }
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

function lookupCharacter(character_id)
{
    if(blacklist.includes(character_id)) return;
    let el = character_id.split("_");
    character_id = el[0];
    // add manual style later?
    
    let assets = [
        ["Main Arts", "sp/assets/npc/zoom/", "png", "img_low/", false, true, false, true], // skin folder, gendered/multi, spritesheet, bonus
        ["Inventory Portraits", "sp/assets/npc/m/", "jpg", "img_low/", false, true, false, true],
        ["Square Portraits", "sp/assets/npc/s/", "jpg", "img_low/", true, true, false, true],
        ["Party Portraits", "sp/assets/npc/f/", "jpg", "img_low/", true, true, false, true],
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
    let uncaps = ["_01", "_02", "_03", "_04"];
    let styles = ["", "_st2"];
    let bonus = ["_81", "_82", "_83", "_91"];
    let alts = ["", "_f", "_f1", "_f_01"];
    
    
    let is_character_skin = character_id[1] == '7';
    newArea("Character", character_id, true);
    for(let asset of assets)
    {
        let uncap_append = asset[7] ? uncaps.concat(bonus) : uncaps;
        let style_append = asset[0].includes("Sheets") ? ["", "_st2", "_st2_2", "_st2_3"] : styles;
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
            for(let style of style_append)
            {
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
                                            img.id  = "loading";
                                            img.onerror = function() {
                                                let result = this.parentNode.parentNode;
                                                this.parentNode.remove();
                                                this.remove();
                                                if(result.childNodes.length <= 2) result.remove();
                                            }
                                            img.onload = function() {
                                                this.id = "done"
                                            }
                                            img.src = protocol + getEndpoint() + language + asset[3] + path;
                                            // sky compass band aid
                                            if(asset[0] === "Main Arts")
                                            {
                                                let path = character_id + uncap + style + alt + gender + unit + s_a + sh + "." + asset[2];
                                                let img = document.createElement("img");
                                                let ref = document.createElement('a');
                                                ref.setAttribute('href', "https://media.skycompass.io/assets/customizes/characters/1138x1138/" + path);
                                                div.appendChild(ref);
                                                ref.appendChild(img);
                                                img.id  = "loading";
                                                img.className  = "skycompass";
                                                img.onerror = function() {
                                                    let result = this.parentNode.parentNode;
                                                    this.parentNode.remove();
                                                    this.remove();
                                                    if(result.childNodes.length <= 2) result.remove();
                                                }
                                                img.onload = function() {
                                                    this.id = ""
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
    }
}

function lookupNPC(npc_id)
{
    if(blacklist.includes(npc_id)) return;
    let assets = [
        ["Journal Art", "sp/assets/npc/b/", "png", "img_low/"],
        ["Inventory Portrait", "sp/assets/npc/m/", "jpg", "img_low/"],
        ["Scene Arts", "sp/quest/scene/character/body/", "png", "img_low/"],
        ["Battle Text Arts", "sp/raid/navi_face/", "png", "img/"]
    ];
    let scene_alts = ["", "_01", "_laugh", "_laugh2", "_wink", "_sad", "_angry", "_school", "_a", "_shadow", "_close", "_serious", "_shout", "_surprise", "_surprise2", "_think", "_serious", "_ecstasy", "_ecstasy2", "_a", "_a_up", "_body", "_valentine"];
    
    newArea("NPC", npc_id, true);
    for(let asset of assets)
    {
        let scene_append = asset[0] == "Scene Arts" ? scene_alts : ["", "_01"];
        
        let div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let scene of scene_append)
        {
            let path = asset[1] +  npc_id + scene + "." + asset[2];
            let img = document.createElement("img");
            let ref = document.createElement('a');
            ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
            div.appendChild(ref);
            ref.appendChild(img);
            img.id  = "loading";
            img.onerror = function() {
                let result = this.parentNode.parentNode;
                this.parentNode.remove();
                this.remove();
                if(result.childNodes.length <= 2) result.remove();
            }
            img.onload = function() {
                this.id = ""
            }
            img.src = protocol + getEndpoint() + language + asset[3] + path;
        }
    }
}

function lookupSummon(summon_id)
{
    if(blacklist.includes(summon_id)) return;
    assets = [
        ["Main Arts", "sp/assets/summon/b/", "png", "img_low/"],
        ["Inventory Portraits", "sp/assets/summon/m/", "jpg", "img_low/"],
        ["Square Portraits", "sp/assets/summon/s/", "jpg", "img_low/"],
        ["Main Summon Portraits", "sp/assets/summon/party_main/", "jpg", "img_low/"],
        ["Sub Summon Portraits", "sp/assets/summon/party_sub/", "jpg", "img_low/"],
        ["Raid Portraits", "sp/assets/summon/raid_normal/", "jpg", "img/"],
        ["Summon Call Sheets", "sp/cjs/summon_", "png", "img_low/"],
        ["Summon Damage Sheets", "sp/cjs/summon_", "png", "img_low/"]
    ];
    let multi_summons = ['2040414000']
    let uncaps = ["", "_01", "_02", "_03"];
    let sheets = [""];
    let uncap_append = [];
    
    newArea("Summon", summon_id, true);
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
                img.id  = "loading";
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.id = ""
                }
                img.src = protocol + getEndpoint() + language + asset[3] + path;
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
            img.id = "loading";
            img.className  = "skycompass";
            img.onerror = function() {
                let result = this.parentNode.parentNode;
                this.parentNode.remove();
                this.remove();
                if(result.childNodes.length <= 2) result.remove();
            }
            img.onload = function() {
                this.id = ""
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
    
    if(!shortened) newArea("Weapon", weapon_id, true);
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
                img.id  = "loading";
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.id = ""
                }
                img.src = protocol + getEndpoint() + language + asset[3] + path;
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
    
    newArea("Enemy", enemy_id, false);
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
                img.id  = "loading";
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.id = ""
                }
                img.src = protocol + getEndpoint() + language + asset[3] + path;
            }
        }
    }
}

function lookupMC(mc_id)
{
    if(blacklist.includes(mc_id)) return;
    let job_ids = mc_id.split('_');
    let assets = [
        ["Job Icon", "sp/ui/icon/job/", "png", "img/", 0],
        ["Inventory Portrait", "sp/assets/leader/m/", "jpg", "img/", 1],
        ["Outfit Portrait", "sp/assets/leader/sd/m/", "jpg", "img/", 1],
        ["Outfit Description", "sp/assets/leader/skin/", "png", "img_low/", 1],
        ["Home Art", "sp/assets/leader/my/", "png", "img_low/", 2],
        ["Full Art", "sp/assets/leader/job_change/", "png", "img_low/", 2],
        ["Outfit Preview Art", "sp/assets/leader/skin/", "png", "img_low/", 2],
        ["Class Name Party Text", "sp/ui/job_name/job_list/", "png", "img/", 0],
        ["Class Name Master Text", "sp/assets/leader/job_name_ml/", "png", "img/", 0],
        ["Class Change Button", "sp/assets/leader/jlon/", "png", "img/", 2],
        ["Party Class Big Portrait", "sp/assets/leader/jobon_z/", "png", "img_low/", 2],
        ["Party Class Portrait", "sp/assets/leader/p/", "png", "img_low/", 2],
        ["Profile Portrait", "sp/assets/leader/pm/", "png", "img_low/", 2],
        ["Profile Board Portrait", "sp/assets/leader/talk/", "png", "img/", 2],
        ["Raid Portrait", "sp/assets/leader/raid_normal/", "jpg", "img/", 2],
        ["Raid Log", "sp/assets/leader/raid_log/", "png", "img/", 2],
        ["Raid Result", "sp/assets/leader/result_ml/", "jpg", "img_low/", 2],
        ["Mastery Portrait", "sp/assets/leader/zenith/", "png", "img_low/", 2],
        ["Master Level Portrait", "sp/assets/leader/master_level/", "png", "img_low/", 2],
        ["Sprite", "sp/assets/leader/sd/", "png", "img/", 3]
    ];
    // 0 = job_ids[0]
    // 1 = job_ids[0] + "_01"
    // 2 = mc_id + "_1_01"
    // 3 = mc_id + "_1_01" (color variations)
    newArea("Main Character", mc_id, false);
    getJSON("data/job.json", lookupMCPlus, function(v){}, mc_id);
    for(let asset of assets)
    {
        let div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        let variations = ['01', '02', '03', '04', '05', '80'];
        if(asset[4] >= 2)
        {
            for(let i = 0; i < 2; ++i)
            {
                for(let vr of variations)
                {
                    let job_final_id = job_ids[0].slice(0, 4) + vr;
                    let path = asset[1] + job_final_id + "_" + job_ids[1] + "_" + i + "_01" + "." + asset[2];
                    let img = document.createElement("img");
                    let ref = document.createElement('a');
                    ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                    div.appendChild(ref);
                    ref.appendChild(img);
                    img.id  = "loading";
                    img.onerror = function() {
                        let result = this.parentNode.parentNode;
                        this.parentNode.remove();
                        this.remove();
                        if(result.childNodes.length <= 2) result.remove();
                    }
                    img.onload = function() {
                        this.id = ""
                    }
                    img.src = protocol + getEndpoint() + language + asset[3] + path;
                }
                // sky compass band aid
                if(asset[0] === "Full Art")
                {
                    let path = job_ids[0] + "_" + i + "." + asset[2];
                    let img = document.createElement("img");
                    let ref = document.createElement('a');
                    ref.setAttribute('href', "https://media.skycompass.io/assets/customizes/jobs/1138x1138/" + path);
                    div.appendChild(ref);
                    ref.appendChild(img);
                    img.id  = "loading";
                    img.className  = "skycompass";
                    img.onerror = function() {
                        let result = this.parentNode.parentNode;
                        this.parentNode.remove();
                        this.remove();
                        if(result.childNodes.length <= 2) result.remove();
                    }
                    img.onload = function() {
                        this.id = ""
                    }
                    img.src = "https://media.skycompass.io/assets/customizes/jobs/1138x1138/" + path;
                }
            }
        }
        else
        {
            for(let vr of variations)
            {
                let job_final_id = job_ids[0].slice(0, 4) + vr;
                let path = asset[1] + (asset[4] == 0 ? job_final_id : job_final_id + "_01") + "." + asset[2];
                let img = document.createElement("img");
                let ref = document.createElement('a');
                ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                div.appendChild(ref);
                ref.appendChild(img);
                img.id  = "loading";
                img.onerror = function() {
                    let result = this.parentNode.parentNode;
                    this.parentNode.remove();
                    this.remove();
                    if(result.childNodes.length <= 2) result.remove();
                }
                img.onload = function() {
                    this.id = ""
                }
                img.src = protocol + getEndpoint() + language + asset[3] + path;
            }
        }
    }
}

var class_lookup = { // need to be manually updated..... :(
    "150201_sw": ["dkf_sw", "dkf_kn"], // dark fencer
    "200201_kn": ["acm_kn", "acm_gu"], // alchemist
    "310401_sw": ["mcd_sw"], // mac do
    "130201_wa": ["hrm_wa", "hrm_kn"], // hermit
    "120401_wa": ["hlr_wa", "hlr_sp"], // iatromantis
    "150301_sw": ["csr_sw", "csr_kn"], // chaos ruler
    "170201_bw": ["sdw_bw", "sdw_gu"], // sidewinder
    "240201_gu": ["gns_gu"], // gunslinger
    "360001_me": ["vee_me"], // vyrn suit
    "310701_sw": ["fal_sw"], // fallen
    "400001_kt": ["szk_kt"], // zhuque
    "450301_sw": ["rlc_sw", "rlc_gu"], // relic buster
    "140301_kn": ["gzk_kn", "gzk_gu"], // bandit tycoon
    "110001_sw": ["kni_sw", "kni_sp"], // knight
    "270301_mc": ["ris_mc"], // rising force
    "290201_gu": ["kks_gu"], // mechanic
    "190101_sp": ["drg_sp", "drg_ax"], // dragoon
    "140201_kn": ["hky_kn", "hky_gu"], // hawkeye
    "240301_gu": ["sol_gu"], // soldier
    "120301_wa": ["sag_wa", "sag_sp"], // sage
    "120101_wa": ["cle_wa", "cle_sp"], // cleric
    "150101_sw": ["ars_sw", "ars_kn"], // arcana dueler
    "130301_wa": ["wrk_wa", "wrk_kn"], // warlock
    "130401_wa": ["mnd_wa", "mnd_kn"], // warlock
    "310601_sw": ["edg_sw"], // eternal 2
    "120001_wa": ["pri_wa", "pri_sp"], // priest
    "180101_mc": ["mst_kn", "mst_mc"], // bard
    "200301_kn": ["dct_kn", "dct_gu"], // doctor
    "220201_kt": ["smr_bw", "smr_kt"], // samurai
    "140001_kn": ["thi_kn", "thi_gu"], // thief
    "370601_me": ["bel_me"], // belial 1
    "370701_me": ["ngr_me"], // cook
    "330001_sp": ["sry_sp"], // qinglong
    "370501_me": ["phm_me"], // anime s2 skin
    "440301_bw": ["rbn_bw"], // robin hood
    "160201_me": ["ogr_me"], // ogre
    "210301_me": ["mhs_me", "mhs_kt"], // runeslayer
    "310001_sw": ["lov_sw"], // lord of vermillion
    "370801_me": ["frb_me"], // belial 2
    "180201_mc": ["sps_kn", "sps_mc"], // superstar
    "310301_sw": ["chd_sw"], // attack on titan
    "125001_wa": ["snt_wa"], // santa
    "110301_sw": ["spt_sw", "spt_sp"], // spartan
    "310801_sw": ["ykt_sw"], // yukata
    "110201_sw": ["hsb_sw", "hsb_sp"], // holy saber
    "230301_sw": ["glr_sw", "glr_kt"], // glorybringer
    "130101_wa": ["srr_wa", "srr_kn"], // sorcerer
    "430301_wa": ["mnk_wa", "mnk_me"], // monk
    "280301_kn": ["msq_kn"], // masquerade
    "250201_wa": ["wmn_wa"], // mystic
    "160001_me": ["grp_me"], // grappler
    "110101_sw": ["frt_sw", "frt_sp"], // sentinel
    "270201_mc": ["drm_mc"], // taiko
    "300301_sw": ["crs_sw", "crs_kt"], // chrysaor
    "360101_gu": ["rac_gu"], // platinum sky 2
    "300201_sw": ["gda_sw", "gda_kt"], // gladiator
    "100101_sw": ["wrr_sw", "wrr_ax"], // warrior
    "170001_bw": ["rng_bw", "rng_gu"], // ranger
    "280201_kn": ["dnc_kn"], // dancer
    "410301_mc": ["lmb_ax", "lmb_mc"],
    "100001_sw": ["fig_sw", "fig_ax"], // fighter
    "180301_kn": ["els_kn", "els_mc"], // elysian
    "250301_wa": ["knd_wa"], // nekomancer
    "260201_kn": ["asa_kn"], // assassin
    "370301_me": ["kjm_me"], // monster 3
    "140101_kn": ["rdr_kn", "rdr_gu"], // raider
    "180001_mc": ["hpt_kn", "hpt_mc"], // superstar
    "370001_me": ["kjt_me"], // monster 1
    "165001_me": ["stf_me"], // street fighter
    "160301_me": ["rsr_me"], // luchador
    "100201_sw": ["wms_sw", "wms_ax"], // weapon master
    "170301_bw": ["hdg_bw", "hdg_gu"], // nighthound
    "230201_sw": ["sdm_sw", "sdm_kt"], // swordmaster
    "310201_sw": ["swm_sw"], // summer
    "190301_sp": ["aps_sp", "aps_ax"], // apsaras
    "100401_sw": ["vkn_sw", "vkn_ax"], // viking
    "150001_sw": ["enh_sw", "enh_kn"], // enhancer
    "220301_bw": ["kng_bw", "kng_kt"], // kengo
    "120201_wa": ["bis_wa", "bis_sp"], // bishop
    "310101_sw": ["ani_sw"], // anime season 1
    "130001_wa": ["wiz_wa", "wiz_kn"], // wizard
    "185001_kn": ["idl_kn", "idl_mc"], // idol
    "100301_sw": ["bsk_sw", "bsk_ax"], // berserker
    "160101_me": ["kun_me"], // kung fu artist
    "370201_me": ["kjb_me"], // monster 2
    "110401_sw": ["pld_sw", "pld_sp"], // paladin
    "310501_sw": ["cnq_sw"], // eternal 1
    "310901_sw": ["vss_sw"], // versus skin
    "190001_sp": ["lnc_sp", "lnc_ax"], // lancer
    "420301_sp": ["cav_sp", "cav_gu"], // cavalier
    "190201_sp": ["vkr_sp", "vkr_ax"], // valkyrie
    "260301_kn": ["tmt_kn"], // tormentor
    "210201_kt": ["nnj_me", "nnj_kt"], // ninja
    "370401_me": ["ybk_me"], // bird
    "320001_kn": ["sut_kn"], // story dancer
    "170101_bw": ["mrk_bw", "mrk_gu"], // archer
    "311001_sw": ["gkn_sw"], // school
    "340001_ax": ["gnb_ax"], // xuanwu
    "360201_gu": ["ebi_gu"], // premium friday
    "370901_me": ["byk_me"], // baihu
    "460301_sw": ["ymt_sw", "ymt_kt"] // yamato
}
var class_ougi = {
    "320001_kn": "1040115000", // school dancer
    "340001_ax": "1040315700", // xuanwu
    "400001_kt": "1040913700", // zhuque
    "330001_sp": "1040216600", // qinglong
    "370901_me": "1040617400", // baihu
    "310501_sw": "1040016700", // eternal 1
    "310601_sw": "1040016800", // eternal 2
    "360101_gu": "1040508600", // platinum sky 2
    "370801_me": "1040616000", // belial 2
    "310701_sw": "1040016900", // fallen
    "370001_me": "1040610300", // monster 1
    "310901_sw": "1040019100", // versus
    "370201_me": "1040610200", // monster 2
    "370301_me": "1040610400", // monster 3
    "370601_me": "1040614400", // belial 1
    "370701_me": "1040615300", // cook
    "310001_sw": "1040009100", // lord of vermillion
    "310801_sw": "1040018800", // yukata
    "311001_sw": "1040020200", // school
    "310301_sw": "1040014200", // attack on titan
    "360201_gu": "1040515800" // premium friday
}

function lookupMCPlus(mc_id)
{
    if(blacklist.includes(mc_id)) return;
    let dupe_check = [];
    let obj = JSON.parse(this.response);
    let genders = ['_0_', '_1_'];
    if(mc_id in class_lookup)
    {
        if(class_lookup[mc_id].length > 0)
        {
            let div = addResult("Sprite Sheets", "Sprite Sheets");
            result_area.appendChild(div);
            for(let cid of class_lookup[mc_id])
            {
                if(cid in obj)
                {
                    for(let elem of obj[cid])
                    {
                        for(let gender of genders)
                        {
                            let file_name = elem.replace('_0_', gender).split('/');
                            file_name = file_name[file_name.length - 1];
                            if(dupe_check.includes(file_name)) continue;
                            else dupe_check.push(file_name);
                            let img = document.createElement("img");
                            let ref = document.createElement('a');
                            ref.setAttribute('href', elem.replace('img_low/', 'img/').replace('_0_', gender));
                            div.appendChild(ref);
                            ref.appendChild(img);
                            img.id  = "loading";
                            img.onerror = function() {
                                let result = this.parentNode.parentNode;
                                this.parentNode.remove();
                                this.remove();
                                if(result.childNodes.length <= 2) result.remove();
                            }
                            img.onload = function() {
                                this.id = ""
                            }
                            img.src = elem.replace('_0_', gender);
                        }
                    }
                }
                else
                {
                    div.appendChild(document.createTextNode("Sprite Sheets are missing, check this page again later"));
                    return
                }
            }
        }
        if(mc_id in class_ougi)
        {
            lookupWeapon(class_ougi[mc_id], true);
        }
    }
}

// =================================================================================================
// index stuff
function addImage(node, path, id)
{
    let img = document.createElement("img");
    let ref = document.createElement('a');
    ref.setAttribute('href', "?id=" + id);
    node.appendChild(ref);
    ref.appendChild(img);
    img.id  = "loading";
    img.loading = "lazy";
    img.onerror = function() {
        this.remove();
    }
    img.onload = function() {
        this.id = "done"
    }
    img.src = protocol + getEndpoint() + language + "img_low/" + path; 
}

function displayCharacters(elem)
{
    elem.removeAttribute("onclick");
    if("characters" in index)
    {
        let node = document.getElementById('areacharacters');  
        for(let id of index["characters"])
        {
            let el = id.split("_");
            if(el.length == 2)
                addImage(node, "sp/assets/npc/m/" + el[0] + "_01_" + el[1] + ".jpg", id);
            else
                addImage(node, "sp/assets/npc/m/" + id + "_01.jpg", id);
        }
    }
}

function displaySummons(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areasummons');
    if("summons" in index)
    {
        for(let id of index["summons"])
        {
            addImage(node, "sp/assets/summon/m/" + id + ".jpg", id);
        }
    }
}

function displayWeapons(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areaweapons');
    if("weapons" in index)
    {
        for(let id of index["weapons"])
        {
            addImage(node, "sp/assets/weapon/m/" + id + ".jpg", id);
        }
    }
}

function displaySkins(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areaskins');
    if("skins" in index)
    {
        for(let id of index["skins"])
        {
            addImage(node, "sp/assets/npc/m/" + id + "_01.jpg", id);
        }
    }
}

function displayEnemies(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areaenemies');
    if("enemies" in index)
    {
        for(let id of index["enemies"])
        {
            addImage(node, "sp/assets/enemy/m/" + id + ".png", "e" + id);
        }
    }
}

function displayMC(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areamc');
    if("job" in index)
    {
        for(let id of index["job"])
        {
            addImage(node, "sp/assets/leader/m/" + id.split('_')[0] + "_01.jpg", id);
        }
    }
}