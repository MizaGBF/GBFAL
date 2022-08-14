/* sky compass notes (for posterity)

Leader: https://media.skycompass.io/assets/customizes/jobs/1138x1138/ID_GENDER.png
Character: https://media.skycompass.io/assets/customizes/characters/1138x1138/ID_UNCAP.png
Summon: https://media.skycompass.io/assets/archives/summons/ID/detail_l.png
Event: https://media.skycompass.io/assets/archives/events/ID/image/NUM_free.png

*/

protocol = "https://";
endpoints = [
    "prd-game-a-granbluefantasy.akamaized.net/",
    "prd-game-a1-granbluefantasy.akamaized.net/",
    "prd-game-a2-granbluefantasy.akamaized.net/",
    "prd-game-a3-granbluefantasy.akamaized.net/",
    "prd-game-a4-granbluefantasy.akamaized.net/",
    "prd-game-a5-granbluefantasy.akamaized.net/"
];
language = "assets_en/";

counter = 0;
last_id = null;
result_area = null;
null_characters = [
    "3030182000", "3710092000", "3710139000", "3710078000", "3710105000", "3710083000", "3020072000", "3710184000"
];

function getEndpoint()
{
    var e = endpoints[counter];
    counter = (counter + 1) % endpoints.length;
    return e;
}

function filter()
{
    lookup(document.getElementById('filter').value.trim().toLowerCase());
}

function init()
{
    result_area = document.getElementById('resultarea');
    var params = new URLSearchParams(window.location.search);
    var id = params.get("id");
    if(id != null) lookup(id);
}

function updateQuery(id)
{
    var params = new URLSearchParams(window.location.search);
    params.set("id", id);
    var newRelativePathQuery = window.location.pathname + '?' + params.toString();
    history.pushState(null, '', newRelativePathQuery);
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
                load_try = true;
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
    var obj = JSON.parse(this.response);
    console.log(obj);
    if(id.length == 10)
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
                if(id[1] == '9') newArea("NOC", id, true);
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
    
    for(let key of Object.keys(obj))
    {
        var div = addResult(key, key);
        result_area.appendChild(div);
        var urls = obj[key];

        for(let url of urls)
        {
            var img = document.createElement("img");
            var ref = document.createElement('a');
            ref.setAttribute('href', url.replace("img_low", "img").replace("http://", protocol));
            div.appendChild(ref);
            ref.appendChild(img);
            img.id  = "loading";
            if(url.includes("media.skycompass.io")) img.className  = "skycompass";
            img.onerror = function() {
                var result = this.parentNode.parentNode;
                this.parentNode.remove();
                this.remove();
                if(result.childNodes.length <= 2) result.remove();
            }
            img.onload = function() {
                this.id = "done"
            }
            img.src = url.replace("http://", protocol);
        }
    }
}

function failJSON(id)
{
    if(id.length == 10)
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
}

function lookup(id)
{
    counter = 0;
    f = document.getElementById('filter');
    if((id.length == 10 && !isNaN(id) && id != last_id) || (id.length == 8 && id.toLowerCase()[0] === 'e' && !isNaN(id.slice(1)) && id.slice(1) != last_id))
    {
        if(f.value == "") f.value = id;
        if(id.toLowerCase()[0] === 'e') id = id.slice(1);
        getJSON("data/" + id + ".json", successJSON, failJSON, id);
    }
}

function newArea(name, id, include_link)
{    
    while(true)
    {
        var child = result_area.lastElementChild;
        if(!child) break;
        result_area.removeChild(child);
    }
    var div = addResult("Result Header", name + ": " + id);
    if(include_link)
    {
        var l = document.createElement('a');
        l.setAttribute('href', "https://gbf.wiki/index.php?title=Special:Search&search=" + id);
        l.appendChild(document.createTextNode("Wiki"));
        div.appendChild(l);
        
        if(id.slice(0, 3) == "302" || id.slice(0, 3) == "303" || id.slice(0, 3) == "304" || id.slice(0, 3) == "371")
        {
            l = document.createElement('a');
            l.setAttribute('href', "https://mizagbf.github.io/GBFAP/?id=" + id);
            l.appendChild(document.createTextNode("Animation"));
            div.appendChild(l);
        }
    }
}

function addResult(identifier, name)
{
    var div = document.createElement("div");
    div.id = "result";
    div.setAttribute("data-id", identifier);
    div.appendChild(document.createTextNode(name));
    div.appendChild(document.createElement("br"));
    result_area.appendChild(div);
    return div;
}

function lookupCharacter(character_id)
{
    assets = [
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
    uncaps = ["_01", "_02", "_03", "_04"];
    bonus = ["_81", "_82", "_83"];
    alts = ["", "_f", "_f1", "_f_01"];
    
    
    var is_character_skin = character_id[1] == '7';
    newArea("Character", character_id, true);
    for(let asset of assets)
    {
        var uncap_append = asset[7] ? uncaps.concat(bonus) : uncaps;
        var alt_append = asset[0].includes("Sheets") ? alts : [""];
        var skin_folders = (is_character_skin && asset[4]) ? ["", "skin/"] : [""];
        var skin_appends = (is_character_skin && asset[4]) ? ["", "_s1", "_s2", "_s3", "_s4", "_s5", "_s6"] : [""];
        var gendered = asset[5] ? ["", "_0", "_1"] : [""];
        var multi = asset[5] ? ["", "_101", "_102", "_103"] : [""];
        var sheet = asset[6] ? ((asset[1].includes("nsp_") || asset[1].includes("npc_")) ? ["", "_s2", "_s3", "_a", "_s2_a", "_s3_a", "_b", "_s2_b", "_s3_b", "_c", "_s2_c", "_s3_c"] : ["", "_a", "_b", "_c"]) : [""];
        var extra = [""];
        
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
        if(asset[0].includes("Skill")) uncap_append = ["_01", "_02", "_03", "_04"];
        
        var div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let uncap of uncap_append)
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
                                        var path = asset[1] + s_f + character_id + uncap + alt + gender + unit + ex + s_a + sh + "." + asset[2];
                                        var img = document.createElement("img");
                                        var ref = document.createElement('a');
                                        ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                                        div.appendChild(ref);
                                        ref.appendChild(img);
                                        img.id  = "loading";
                                        img.onerror = function() {
                                            var result = this.parentNode.parentNode;
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
                                            var path = character_id + uncap + alt + gender + unit + s_a + sh + "." + asset[2];
                                            img = document.createElement("img");
                                            ref = document.createElement('a');
                                            ref.setAttribute('href', "https://media.skycompass.io/assets/customizes/characters/1138x1138/" + path);
                                            div.appendChild(ref);
                                            ref.appendChild(img);
                                            img.id  = "loading";
                                            img.className  = "skycompass";
                                            img.onerror = function() {
                                                var result = this.parentNode.parentNode;
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

function lookupNPC(npc_id)
{
    assets = [
        ["Journal Art", "sp/assets/npc/b/", "png", "img_low/"],
        ["Inventory Portrait", "sp/assets/npc/m/", "jpg", "img_low/"],
        ["Scene Arts", "sp/quest/scene/character/body/", "png", "img_low/"]
    ];
    scene_alts = ["", "_01", "_laugh", "_laugh2", "_sad", "_angry", "_school", "_a", "_shadow", "_close", "_serious", "_shout", "_surprise", "_surprise2", "_think", "_serious", "_a", "_a_up", "_body", "_valentine"];
    
    newArea("NPC", npc_id, true);
    for(let asset of assets)
    {
        var scene_append = asset[0] == "Scene Arts" ? scene_alts : ["", "_01"];
        
        var div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let scene of scene_append)
        {
            var path = asset[1] +  npc_id + scene + "." + asset[2];
            var img = document.createElement("img");
            var ref = document.createElement('a');
            ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
            div.appendChild(ref);
            ref.appendChild(img);
            img.id  = "loading";
            img.onerror = function() {
                var result = this.parentNode.parentNode;
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
    uncaps = ["", "_01", "_02"];
    sheets = [""];
    
    newArea("Summon", summon_id, true);
    for(let asset of assets)
    {
        var uncap_append = JSON.parse(JSON.stringify(uncaps));
        switch(asset[0])
        {
            case "Summon Call Sheets":
                for(let i = 0; i < uncap_append.length; ++i)
                    uncap_append[i] += "_attack";
                sheets = ["", "_a", "_b", "_c", "_d", "_e", "_f", "_bg", "_bg1", "_bg2", "_bg3"];
                break;
            case "Summon Damage Sheets":
                for(let i = 0; i < uncap_append.length; ++i)
                    uncap_append[i] += "_damage";
                sheets = ["", "_a", "_b", "_c", "_d", "_e", "_f", "_bg", "_bg1", "_bg2", "_bg3"];
                break;
            default:
                sheets = [""];
        };
        
        var div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let uncap of uncap_append)
        {
            for(let sheet of sheets)
            {
                var path = asset[1] + summon_id + uncap + sheet + "." + asset[2];
                var img = document.createElement("img");
                var ref = document.createElement('a');
                ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                div.appendChild(ref);
                ref.appendChild(img);
                img.id  = "loading";
                img.onerror = function() {
                    var result = this.parentNode.parentNode;
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
            img = document.createElement("img");
            ref = document.createElement('a');
            ref.setAttribute('href', "https://media.skycompass.io/assets/archives/summons/" + summon_id + "/detail_l.png");
            div.appendChild(ref);
            ref.appendChild(img);
            img.id  = "loading";
            img.className  = "skycompass";
            img.onerror = function() {
                var result = this.parentNode.parentNode;
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

function lookupWeapon(weapon_id)
{
   assets = [
        ["Main Arts", "sp/assets/weapon/b/", "png", "img_low/"],
        ["Inventory Portraits", "sp/assets/weapon/m/", "jpg", "img_low/"],
        ["Square Portraits", "sp/assets/weapon/s/", "jpg", "img_low/"],
        ["Main Hand Portraits", "sp/assets/weapon/ls/", "jpg", "img_low/"],
        ["Battle Sprites", "sp/cjs/", "png", "img/"],
        ["Attack Effects", "sp/cjs/phit_", "png", "img/"],
        ["Charge Attack Sheets", "sp/cjs/sp_", "png", "img_low/"]
    ];
    appends = [""];
    sheets = [""];
    
    newArea("Weapon", weapon_id, true);
    for(let asset of assets)
    {
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
        
        var div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let append of appends)
        {
            for(let sheet of sheets)
            {
                var path = asset[1] + weapon_id + append + sheet + "." + asset[2];
                var img = document.createElement("img");
                var ref = document.createElement('a');
                ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                div.appendChild(ref);
                ref.appendChild(img);
                img.id  = "loading";
                img.onerror = function() {
                    var result = this.parentNode.parentNode;
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
   assets = [
        ["Big Icon", "sp/assets/enemy/m/", "png", "img/"],
        ["Small Icon", "sp/assets/enemy/s/", "png", "img/"],
        ["Sprite Sheets", "sp/cjs/enemy_", "png", "img_low/"],
        ["Raid Appear Sheets", "sp/cjs/raid_appear_", "png", "img_low/"],
        ["Attack Effect Sheets", "sp/cjs/ehit_", "png", "img_low/"],
        ["Charge Attack Sheets", "sp/cjs/esp_", "png", "img_low/"]
    ];
    appends = [""];
    sheets = [""];
    
    newArea("Enemy", enemy_id, false);
    for(let asset of assets)
    {
        sheets = asset[0].includes("Sheets") ? ["", "_a", "_b", "_c", "_d", "_e"] : [""];
        appends = asset[0].includes("Charge Attack") ? ["_01", "_02", "_03", "_04", "_05", "_06", "_07", "_08", "_09", "_10", "_11", "_12", "_13", "_14", "_15", "_16", "_17", "_18", "_19", "_20"] : [""];
        
        var div = addResult(asset[0], asset[0]);
        result_area.appendChild(div);
        for(let append of appends)
        {
            for(let sheet of sheets)
            {
                var path = asset[1] + enemy_id + append+sheet + "." + asset[2];
                var img = document.createElement("img");
                var ref = document.createElement('a');
                ref.setAttribute('href', protocol + endpoints[0] + language + "img/" + path);
                div.appendChild(ref);
                ref.appendChild(img);
                img.id  = "loading";
                img.onerror = function() {
                    var result = this.parentNode.parentNode;
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