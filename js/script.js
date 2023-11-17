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
var init_err = 0;
var main_endp_count = -1;
var language = "assets_en/"; // change to "assets/" for japanese

// tracking last id loaded
var last_id = null;
var last_type = null;

// result div
var result_area = null;

// constant
const DISPLAY_MINI = 4; // number of file to display at the minimum if a lot of files are present
// list of null characters/skins
const null_characters = [
    "3030182000", "3710092000", "3710139000", "3710078000", "3710105000", "3710083000", "3020072000", "3710184000"
];
// list of known scene strings for unindexed characters
const no_bubble_scene_suffix = ["speed", "up", "shadow", "shadow2", "shadow3", "light", "blood"];
const dummy_scene_strings = ["", "_2022", "_2022_laugh", "_a", "_a_amaze", "_a_amaze_up", "_a_angry", "_a_angry2", "_a_angry2_speed", "_a_angry2_up", "_a_angry3", "_a_angry3_up", "_a_angry_light", "_a_angry_shadow", "_a_angry_speed", "_a_angry_up", "_a_bad", "_a_bad_up", "_a_blood", "_a_close", "_a_close_light", "_a_close_up", "_a_ecstasy", "_a_ecstasy2", "_a_ecstasy2_up", "_a_ecstasy_up", "_a_ef", "_a_ef_speed", "_a_eyeline", "_a_eyeline_light", "_a_eyeline_up", "_a_joy", "_a_joy_up", "_a_laugh", "_a_laugh2", "_a_laugh2_light", "_a_laugh2_up", "_a_laugh3", "_a_laugh3_speed", "_a_laugh3_up", "_a_laugh4", "_a_laugh4_speed", "_a_laugh4_up", "_a_laugh5", "_a_laugh5_up", "_a_laugh6", "_a_laugh6_up", "_a_laugh_light", "_a_laugh_speed", "_a_laugh_up", "_a_light", "_a_light_shadow", "_a_light_speed", "_a_light_up", "_a_mood", "_a_mood2", "_a_mood2_up", "_a_mood3", "_a_mood3_up", "_a_mood_up", "_a_painful", "_a_painful2", "_a_painful2_blood", "_a_painful2_light", "_a_painful2_speed", "_a_painful2_up", "_a_painful2_up_blood", "_a_painful_blood", "_a_painful_light", "_a_painful_speed", "_a_painful_up", "_a_painful_up_blood", "_a_sad", "_a_sad2", "_a_sad2_blood", "_a_sad2_light", "_a_sad2_up", "_a_sad_blood", "_a_sad_light", "_a_sad_speed", "_a_sad_up", "_a_serious", "_a_serious2", "_a_serious2_light", "_a_serious2_shadow", "_a_serious2_speed", "_a_serious2_up", "_a_serious3", "_a_serious3_light", "_a_serious3_up", "_a_serious4", "_a_serious4_light", "_a_serious4_up", "_a_serious_blood", "_a_serious_light", "_a_serious_shadow", "_a_serious_speed", "_a_serious_up", "_a_shadow", "_a_shadow2", "_a_shadow3", "_a_shadow_blood", "_a_shadow_light", "_a_shadow_speed", "_a_shadow_up", "_a_shout", "_a_shout2", "_a_shout2_light", "_a_shout2_speed", "_a_shout2_up", "_a_shout3", "_a_shout3_up", "_a_shout_blood", "_a_shout_light", "_a_shout_speed", "_a_shout_up", "_a_shy", "_a_shy2", "_a_shy2_up", "_a_shy_up", "_a_speed", "_a_speed2", "_a_suddenly", "_a_suddenly2", "_a_suddenly2_light", "_a_suddenly2_up", "_a_suddenly_light", "_a_suddenly_up", "_a_surprise", "_a_surprise2", "_a_surprise2_light", "_a_surprise2_speed", "_a_surprise2_up", "_a_surprise_light", "_a_surprise_shadow", "_a_surprise_speed", "_a_surprise_up", "_a_think", "_a_think2", "_a_think2_speed", "_a_think2_up", "_a_think3", "_a_think3_up", "_a_think4", "_a_think4_up", "_a_think5", "_a_think5_up", "_a_think_speed", "_a_think_up", "_a_up", "_a_up_blood", "_a_up_light", "_a_up_shadow", "_a_up_shadow2", "_a_up_shadow3", "_a_up_speed", "_a_valentine", "_a_weak", "_a_weak_up", "_a_wink", "_a_wink_up", "_amaze", "_amaze_light", "_amaze_up", "_amaze_up_blood", "_angry", "_angry2", "_angry2_a", "_angry2_blood", "_angry2_light", "_angry2_shadow", "_angry2_speed", "_angry2_up", "_angry2_up_blood", "_angry3", "_angry3_blood", "_angry3_light", "_angry3_speed", "_angry3_up", "_angry3_up_blood", "_angry_a", "_angry_blood", "_angry_light", "_angry_shadow", "_angry_shadow2", "_angry_speed", "_angry_up", "_angry_up2", "_angry_up_blood", "_b", "_b_amaze", "_b_angry", "_b_angry2", "_b_angry2_light", "_b_angry2_speed", "_b_angry2_up", "_b_angry3", "_b_angry_light", "_b_angry_speed", "_b_angry_up", "_b_bad", "_b_blood", "_b_close", "_b_close_up", "_b_ef", "_b_ef_speed", "_b_ef_up", "_b_eyeline", "_b_eyeline_light", "_b_eyeline_up", "_b_laugh", "_b_laugh2", "_b_laugh2_up", "_b_laugh3", "_b_laugh3_up", "_b_laugh4", "_b_laugh4_up", "_b_laugh5", "_b_laugh6", "_b_laugh_light", "_b_laugh_speed", "_b_laugh_up", "_b_light", "_b_light_speed", "_b_mood", "_b_mood2", "_b_mood2_up", "_b_mood3", "_b_mood3_up", "_b_mood_light", "_b_mood_up", "_b_painful", "_b_painful2", "_b_painful2_speed", "_b_painful2_up", "_b_painful_shadow", "_b_painful_speed", "_b_painful_up", "_b_painful_up_blood", "_b_sad", "_b_sad2", "_b_sad2_up", "_b_sad_light", "_b_sad_up", "_b_serious", "_b_serious2", "_b_serious2_up", "_b_serious3", "_b_serious3_up", "_b_serious4", "_b_serious4_up", "_b_serious_light", "_b_serious_speed", "_b_serious_up", "_b_shadow", "_b_shadow2", "_b_shadow_light", "_b_shadow_speed", "_b_shadow_up", "_b_shout", "_b_shout2", "_b_shout2_up", "_b_shout_up", "_b_shy", "_b_shy2", "_b_shy2_up", "_b_shy_up", "_b_speed", "_b_speed2", "_b_suddenly", "_b_suddenly2", "_b_suddenly2_shadow", "_b_suddenly2_up", "_b_suddenly_up", "_b_surprise", "_b_surprise2", "_b_surprise2_up", "_b_surprise_speed", "_b_surprise_up", "_b_think", "_b_think2", "_b_think2_up", "_b_think3", "_b_think3_up", "_b_think_up", "_b_up", "_b_up_light", "_b_up_shadow", "_b_up_speed", "_b_weak", "_b_weak_up", "_bad", "_bad_speed", "_bad_up", "_battle", "_battle_angry", "_battle_angry_speed", "_battle_angry_up", "_battle_close", "_battle_close_up", "_battle_ef", "_battle_laugh", "_battle_laugh2", "_battle_laugh2_up", "_battle_laugh3", "_battle_laugh3_up", "_battle_laugh4", "_battle_laugh4_up", "_battle_laugh_up", "_battle_light", "_battle_painful", "_battle_painful2", "_battle_painful2_up", "_battle_painful_up", "_battle_serious", "_battle_serious_speed", "_battle_serious_up", "_battle_shadow", "_battle_shadow2", "_battle_shout", "_battle_shout_up", "_battle_speed", "_battle_speed2", "_battle_suddenly", "_battle_suddenly_up", "_battle_surprise", "_battle_surprise2", "_battle_surprise2_up", "_battle_surprise_speed", "_battle_surprise_up", "_battle_up", "_battle_up_shadow", "_battle_up_speed", "_birthday", "_birthday2", "_birthday3", "_birthday3_a", "_birthday3_b", "_blood", "_body", "_body_speed", "_c", "_c_angry", "_c_angry2", "_c_angry2_up", "_c_angry3", "_c_angry_light", "_c_angry_shadow2", "_c_angry_up", "_c_close", "_c_close_up", "_c_ef", "_c_ef_shadow", "_c_laugh", "_c_laugh2", "_c_laugh2_speed", "_c_laugh2_up", "_c_laugh3", "_c_laugh3_up", "_c_laugh4", "_c_laugh4_speed", "_c_laugh4_up", "_c_laugh_up", "_c_light", "_c_mood", "_c_mood2", "_c_mood2_up", "_c_mood_up", "_c_painful", "_c_painful2", "_c_painful2_shadow", "_c_painful2_up", "_c_painful_speed", "_c_painful_up", "_c_sad", "_c_sad2", "_c_sad2_up", "_c_sad_up", "_c_serious", "_c_serious2", "_c_serious2_up", "_c_serious3", "_c_serious3_up", "_c_serious_light", "_c_serious_speed", "_c_serious_up", "_c_shadow", "_c_shadow2", "_c_shadow_up", "_c_shout", "_c_shout2", "_c_shout2_up", "_c_shout_shadow", "_c_shout_up", "_c_shy", "_c_shy2", "_c_shy2_up", "_c_shy_up", "_c_speed", "_c_speed2", "_c_suddenly", "_c_surprise", "_c_surprise2", "_c_surprise2_up", "_c_surprise_speed", "_c_surprise_up", "_c_think", "_c_think2", "_c_think2_up", "_c_think_up", "_c_up", "_c_up_speed", "_c_weak", "_c_weak_speed", "_c_weak_up", "_close", "_close_a", "_close_blood", "_close_light", "_close_shadow2", "_close_shadow3", "_close_speed", "_close_up", "_close_up_blood", "_doya", "_ecstasy", "_ecstasy2", "_ecstasy2_up", "_ecstasy_light", "_ecstasy_up", "_ef", "_ef_a", "_ef_light", "_ef_shadow", "_ef_speed", "_ef_up", "_eyeline", "_eyeline_a", "_eyeline_light", "_eyeline_up", "_eyeline_up2", "_gesu", "_gesu2", "_girl_angry", "_girl_laugh", "_girl_sad", "_girl_serious", "_girl_surprise", "_joy", "_joy_a", "_joy_shadow", "_joy_speed", "_joy_up", "_laugh", "_laugh2", "_laugh2_a", "_laugh2_blood", "_laugh2_light", "_laugh2_shadow", "_laugh2_speed", "_laugh2_up", "_laugh2_up2", "_laugh2_up_blood", "_laugh3", "_laugh3_a", "_laugh3_blood", "_laugh3_light", "_laugh3_shadow", "_laugh3_speed", "_laugh3_up", "_laugh3_up2", "_laugh3_up_blood", "_laugh4", "_laugh4_blood", "_laugh4_shadow", "_laugh4_up", "_laugh4_up_blood", "_laugh5", "_laugh5_blood", "_laugh5_up", "_laugh5_up_blood", "_laugh6", "_laugh6_blood", "_laugh6_light", "_laugh6_up", "_laugh6_up_blood", "_laugh7", "_laugh7_blood", "_laugh7_up", "_laugh7_up_blood", "_laugh8", "_laugh8_blood", "_laugh8_up", "_laugh8_up_blood", "_laugh_a", "_laugh_blood", "_laugh_light", "_laugh_shadow", "_laugh_shadow2", "_laugh_speed", "_laugh_up", "_laugh_up2", "_laugh_up_blood", "_light", "_light_shadow", "_light_shadow2", "_light_speed", "_light_up", "_mood", "_mood2", "_mood2_a", "_mood2_light", "_mood2_shadow3", "_mood2_up", "_mood2_up2", "_mood3", "_mood3_a", "_mood3_up", "_mood_a", "_mood_light", "_mood_shadow", "_mood_shadow3", "_mood_speed", "_mood_up", "_mood_up2", "_mood_up_blood", "_nalhe", "_nalhe_speed", "_nalhe_up", "_narrator", "_painful", "_painful2", "_painful2_a", "_painful2_blood", "_painful2_light", "_painful2_shadow", "_painful2_shadow2", "_painful2_speed", "_painful2_up", "_painful2_up_blood", "_painful_a", "_painful_blood", "_painful_light", "_painful_shadow", "_painful_shadow2", "_painful_speed", "_painful_up", "_painful_up_blood", "_pride", "_pride_a", "_pride_up", "_sad", "_sad2", "_sad2_light", "_sad2_speed", "_sad2_up", "_sad_a", "_sad_light", "_sad_shadow", "_sad_speed", "_sad_up", "_sad_up2", "_school", "_school_a", "_school_up", "_serious", "_serious10", "_serious10_blood", "_serious10_up", "_serious10_up_blood", "_serious11", "_serious11_blood", "_serious11_up", "_serious11_up_blood", "_serious2", "_serious2_blood", "_serious2_light", "_serious2_speed", "_serious2_up", "_serious2_up_blood", "_serious3", "_serious3_blood", "_serious3_light", "_serious3_speed", "_serious3_up", "_serious3_up_blood", "_serious4", "_serious4_blood", "_serious4_light", "_serious4_up", "_serious4_up_blood", "_serious5", "_serious5_blood", "_serious5_up", "_serious5_up_blood", "_serious6", "_serious6_blood", "_serious6_up", "_serious6_up_blood", "_serious7", "_serious7_blood", "_serious7_up", "_serious7_up_blood", "_serious8", "_serious8_blood", "_serious8_up", "_serious8_up_blood", "_serious9", "_serious9_blood", "_serious9_up", "_serious9_up_blood", "_serious_a", "_serious_blood", "_serious_light", "_serious_shadow", "_serious_shadow3", "_serious_speed", "_serious_up", "_serious_up_blood", "_shadow", "_shadow2", "_shadow2_light", "_shadow2_speed", "_shadow3", "_shadow3_light", "_shadow_a", "_shadow_blood", "_shadow_light", "_shadow_speed", "_shadow_up", "_shadow_up_blood", "_shout", "_shout2", "_shout2_blood", "_shout2_light", "_shout2_shadow", "_shout2_speed", "_shout2_up", "_shout2_up_blood", "_shout3", "_shout3_blood", "_shout3_light", "_shout3_speed", "_shout3_up", "_shout3_up_blood", "_shout_a", "_shout_blood", "_shout_light", "_shout_shadow", "_shout_shadow2", "_shout_speed", "_shout_up", "_shout_up_blood", "_shy", "_shy2", "_shy2_a", "_shy2_light", "_shy2_up", "_shy_a", "_shy_light", "_shy_speed", "_shy_up", "_speed", "_speed2", "_stump", "_stump2", "_suddenly", "_suddenly2", "_suddenly2_up", "_suddenly2_up2", "_suddenly_light", "_suddenly_speed", "_suddenly_up", "_suddenly_up2", "_surprise", "_surprise2", "_surprise2_a", "_surprise2_blood", "_surprise2_light", "_surprise2_shadow", "_surprise2_speed", "_surprise2_up", "_surprise2_up_blood", "_surprise_a", "_surprise_blood", "_surprise_light", "_surprise_shadow", "_surprise_speed", "_surprise_up", "_surprise_up2", "_surprise_up3", "_surprise_up4", "_surprise_up_blood", "_think", "_think2", "_think2_light", "_think2_speed", "_think2_up", "_think3", "_think3_light", "_think3_up", "_think4", "_think4_up", "_think_a", "_think_light", "_think_shadow", "_think_speed", "_think_up", "_town_thug", "_up", "_up2", "_up3", "_up_a", "_up_blood", "_up_light", "_up_shadow", "_up_shadow2", "_up_shadow3", "_up_speed", "_valentine", "_valentine2", "_valentine_a", "_weak", "_weak_a", "_weak_light", "_weak_shadow", "_weak_speed", "_weak_up", "_white", "_whiteday", "_whiteday2", "_whiteday3", "_wink", "_wink_up"];
// add id here to disable some elements
const blacklist = [

];

var index = {}; // data index (loaded from data.json)
var searchHistory = []; // search history
var searchResults = []; // search results
var bookmarks = []; // bookmarks
var timestamp = Date.now(); // timestamp (loaded from changelog.json)
var updated = []; // list of recently updated elements (loaded from changelog.json)
var intervals = []; // on screen notifications
var typingTimer; // typing timer timeout
var audio = null; // last played audio
var previewhome = false; // preview for home art flag

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
    // localstorage retrocompatibility (remove in the future, maybe 2024+?)
    let tmp = localStorage.getItem("bookmark");
    if(tmp != null)
    {
        localStorage.setItem("gbfal-bookmark", tmp);
        localStorage.removeItem("bookmark");
    }
    tmp = localStorage.getItem("history");
    if(tmp != null)
    {
        localStorage.setItem("gbfal-history", tmp);
        localStorage.removeItem("history");
    }
    getJSON("json/changelog.json?" + timestamp, initChangelog, initChangelog, null); // load changelog
}

function initChangelog(unused)
{
    try{ // load content of changelog.json
        let json = JSON.parse(this.response);
        if(json.hasOwnProperty("new")) // set updated
            updated = json["new"].reverse();
        timestamp = json.timestamp; // set timestamp
        clock();
        if(json.hasOwnProperty("issues"))
        {
            let issues = json["issues"];
            if(issues.length > 0)
            {
                let el = document.getElementById("issues");
                el.innerHTML = "<ul>"
                for(let i = 0; i < issues.length; ++i) el.innerHTML += "<li>"+issues[i]+"</li>\n";
                el.innerHTML += "</ul>"
                el.parentNode.parentNode.style.display = null;
            }
        }
    } catch(err) {}
    // load data json
    getJSON("json/data.json?" + timestamp, initIndex, initIndex, null);
}

function clock()
{
    let now = new Date();
    let elapsed = (now - (new Date(timestamp))) / 1000;
    let msg = ""
    if(elapsed < 120) msg = Math.trunc(elapsed) + " seconds ago.";
    else if(elapsed < 7200) msg = Math.trunc(elapsed / 60) + " minutes ago.";
    else if(elapsed < 172800) msg = Math.trunc(elapsed / 3600) + " hours ago.";
    else if(elapsed < 5270400) msg = Math.trunc(elapsed / 86400) + " days ago.";
    else if(elapsed < 63115200) msg = Math.trunc(elapsed / 2635200) + " months ago.";
    else msg = Math.trunc(elapsed / 31557600) + " years ago.";
    document.getElementById('timestamp').innerHTML = "Last update: " + msg;
    setTimeout(clock, now.getTime() % 1000 + 1);
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
        console.error(err);
        init_err++;
        if(init_err >= 3) return;
        getJSON("json/data.json?" + timestamp, initIndex, initIndex, null); // try again
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

function customSortPair(a, b) // used to sort banter sound files
{
    const [empty1, string1, a1, b1] = a.split('_');
    const [empty2, string2, a2, b2] = b.split('_');

    const numA1 = parseInt(a1, 10);
    const numA2 = parseInt(a2, 10);
    const numB1 = parseInt(b1, 10);
    const numB2 = parseInt(b2, 10);

    if (numA1 !== numA2) {
        return numA1 - numA2;
    } else {
        return numB1 - numB2;
    }
}

function customSortSeasonal(a, b) // used to sort seasonal sound files
{
    const baseA = a.replace(/\d+$/, '');
    const baseB = b.replace(/\d+$/, '');

    if (baseA < baseB) return -1;
    if (baseA > baseB) return 1;

    const numA = parseInt(a.slice(baseA.length), 10);
    const numB = parseInt(b.slice(baseB.length), 10);

    return numA - numB;
}

// =================================================================================================
// main stuff
function loadIndexed(id, obj, check, indexed=true) // load an element from data.json
{
    let search_type;
    let tmp_last_id = last_id;
    let area_name = ""
    let area_extra = false;
    switch(id.length)
    {
        case 10:
            switch(id[0])
            {
                case '1':
                    area_name = "Weapon";
                    area_extra = true;
                    search_type = 1;
                    break;
                case '2':
                    area_name = "Summon";
                    area_extra = true;
                    search_type = 2;
                    break;
                case '3':
                    switch(id.slice(0, 3))
                    {
                        case '399':
                        case '305':
                            area_name = "NPC";
                            area_extra = obj[0] && indexed;
                            search_type = 5;
                            break;
                        case '384':
                        case '383':
                        case '382':
                        case '381':
                        case '388':
                        case '389':
                            area_name = "Partner";
                            search_type = 6;
                            break;
                        default:
                            area_name = "Character";
                            area_extra = true;
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
            area_name = "Enemy";
            search_type = 4;
            last_id = "e"+id;
            updateQuery("e"+id);
            break;
        case 6:
            if(check == "events")
            {
                area_name = "Event";
                search_type = 7;
                last_id = "q"+id;
                updateQuery("q"+id);
            }
            else
            {
                area_name = "Main Character";
                area_extra = true;
                indexed = (obj[7].length != 0) && indexed;
                search_type = 0;
                last_id = id;
                updateQuery(id);
            }
            break;
        case 4:
            if(check == "skills")
            {
                area_name = "Skill";
                search_type = 8;
                last_id = "sk"+id;
                updateQuery("sk"+id);
            }
            else if(check == "buffs")
            {
                area_name = "Buff";
                search_type = 9;
                last_id = "b"+id;
                updateQuery("b"+id);
            }
            break;
        default:
            return;
    }
    if(id == tmp_last_id && last_type == search_type) return; // quit if already loaded
    newArea(area_name, id, area_extra, indexed);
    last_type = search_type;
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
        case 7: // events
            assets = [
                ["Sky Compass", "", "", "", 20, true, false],
                ["Opening Arts", "sp/quest/scene/character/body/", "png", "img_low/", 2, false, false],
                ["Chapter 1 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 5, false, false],
                ["Chapter 2 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 6, false, false],
                ["Chapter 3 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 7, false, false],
                ["Chapter 4 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 8, false, false],
                ["Chapter 5 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 9, false, false],
                ["Chapter 6 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 10, false, false],
                ["Chapter 7 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 11, false, false],
                ["Chapter 8 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 12, false, false],
                ["Chapter 9 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 13, false, false],
                ["Chapter 10 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 14, false, false],
                ["Chapter 11 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 15, false, false],
                ["Chapter 12 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 16, false, false],
                ["Chapter 13 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 17, false, false],
                ["Chapter 14 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 18, false, false],
                ["Chapter 15 Arts", "sp/quest/scene/character/body/", "png", "img_low/", 19, false, false],
                ["Ending Arts", "sp/quest/scene/character/body/", "png", "img_low/", 3, false, false],
                ["Other Arts", "sp/quest/scene/character/body/", "png", "img_low/", 4, false, false]
            ];
            skycompass = ["https://media.skycompass.io/assets/archives/events/"+obj[1]+"/image/", "_free.png", true];
            break;
        case 8: // skills
            assets = [
                ["Skill Icons", "sp/ui/icon/ability/m/", "png", "img/", -1, false, false]
            ];
            files = [""+parseInt(id), ""+parseInt(id)+"_1", ""+parseInt(id)+"_2", ""+parseInt(id)+"_3", ""+parseInt(id)+"_4", ""+parseInt(id)+"_5"];
            break;
        case 9: // buffs
            assets = [
                ["Main Icon", "sp/ui/icon/status/x64/status_", "png", "img/", 0, false, false]
            ];
            let tmp = obj[0][0];
            let variations = obj[1];
            obj = [[]];
            if(!tmp.includes("_"))
                obj[0].push(""+parseInt(id));
            let v1 = variations.includes("1");
            let vu1 = variations.includes("_1");
            let vu10 = variations.includes("_10");
            let vu11 = variations.includes("_11");
            let vu101 = variations.includes("_101");
            let vu110 = variations.includes("_110");
            let vu30 = variations.includes("_30");
            let vu1u1 = variations.includes("_1_1");
            let vu2u1 = variations.includes("_2_1");
            let vu0u10 = variations.includes("_0_10");
            let vu1u10 = variations.includes("_1_10");
            let vu1u20 = variations.includes("_1_20");
            let vu2u10 = variations.includes("_2_10");
            if(vu1 && vu10)
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 0; i < 21; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+"_"+i);
            }
            else if(vu1)
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 0; i < 10; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+"_"+i);
            }
            if(v1) // weird exception for satyr and siete (among maybe others)
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 0; i < 10; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+""+i);
            }
            if(vu10 && vu30)
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 10; i < 70; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+"_"+i);
            }
            else if(!vu10 && vu11 && vu110)
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 0; i < 21; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+"_1"+i);
            }
            else if((vu10 && !vu1) || (!vu10 && vu11))
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 10; i < 111; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+"_"+i);
            }
            else if(vu101)
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 1; i < 21; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+"_1"+JSON.stringify(i).padStart(2, '0'));
            }
            if(vu0u10)
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 10; i < 101; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+"_0_"+i);
            }
            if(vu1u1 && vu1u10)
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 0; i < 21; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+"_1_"+i);
            }
            else if(vu1u1)
            {
                obj.push([]);
                assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                for(let i = 0; i < 11; ++i)
                    obj[obj.length-1].push(""+parseInt(id)+"_1_"+i);
            }
            else if(vu1u10)
            {
                for(let j = 0; j < 11; ++j)
                {
                    obj.push([]);
                    assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                    for(let i = 0; i < 101; ++i)
                        obj[obj.length-1].push(""+parseInt(id)+"_"+j+"_"+i);
                }
            }
            if(vu2u1 && vu2u10)
            {
                for(let j = 2; j < 7; ++j)
                {
                    obj.push([]);
                    assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                    for(let i = 0; i < 21; ++i)
                        obj[obj.length-1].push(""+parseInt(id)+"_"+j+"_"+i);
                }
            }
            else if(vu2u1)
            {
                for(let j = 2; j < 7; ++j)
                {
                    obj.push([]);
                    assets.push(["Variations #"+(obj.length-1), "sp/ui/icon/status/x64/status_", "png", "img/", obj.length-1, false, false])
                    for(let i = 0; i < 11; ++i)
                        obj[obj.length-1].push(""+parseInt(id)+"_"+j+"_"+i);
                }
            }
            
            break;
        case 3: // characters / skins
            assets = [
                ["Main Arts", "sp/assets/npc/zoom/", "png", "img_low/", 5, true, false], // index, skycompass, side form
                ["Home Arts", "sp/assets/npc/my/", "png", "img_low/", 5, false, false],
                ["Journal Arts", "sp/assets/npc/b/", "png", "img_low/", 5, false, false],
                ["Gacha Arts", "sp/assets/npc/gacha/", "png", "img_low/", 6, false, false],
                ["News Art", "sp/banner/notice/update_char_", "png", "img_low/", 6, false, false],
                ["Pose News Arts", "sp/assets/npc/add_pose/", "png", "img_low/", 6, false, false],
                ["Inventory Portraits", "sp/assets/npc/m/", "jpg", "img_low/", 5, false, false],
                ["Square Portraits", "sp/assets/npc/s/", "jpg", "img_low/", 5, false, false],
                ["Party Portraits", "sp/assets/npc/f/", "jpg", "img_low/", 5, false, false],
                ["Popup Portraits", "sp/assets/npc/qm/", "png", "img_mid/", 5, false, false],
                ["Result Popup Portraits", "sp/result/popup_char/", "png", "img_mid/", -2, false, false],
                ["Balloon Portraits", "sp/gacha/assets/balloon_s/", "png", "img/", 6, false, false],
                ["Party Select Portraits", "sp/assets/npc/quest/", "jpg", "img/", 5, false, false],
                ["Tower of Babyl Portraits", "sp/assets/npc/t/", "png", "img_low/", 5, false, false],
                ["EMP Up Portraits", "sp/assets/npc/result_lvup/", "png", "img_low/", 5, false, false],
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
                ["Forge Headers", "sp/archaic/", "", "img_low/", -3, false, false],
                ["Forge Portraits", "sp/archaic/", "", "img_mid/", -4, false, false],
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
                ["Full Arts", "sp/assets/leader/job_change/", "png", "img_low/", 3, true, false],
                ["Home Arts", "sp/assets/leader/my/", "png", "img_low/", 3, false, false],
                ["Outfit Preview Arts", "sp/assets/leader/skin/", "png", "img_low/", 3, false, false],
                ["Class Name Party Texts", "sp/ui/job_name/job_list/", "png", "img/", 0, false, false],
                ["Class Name Master Texts", "sp/assets/leader/job_name_ml/", "png", "img/", 0, false, false],
                ["Class Name Ultimate Texts", "sp/assets/leader/job_name_pp/", "png", "img/", 0, false, false],
                ["Class Change Buttons", "sp/assets/leader/jlon/", "png", "img/", 2, false, false],
                ["Party Class Big Portraits", "sp/assets/leader/jobon_z/", "png", "img_low/", 3, false, false],
                ["Party Class Portraits", "sp/assets/leader/p/", "png", "img_low/", 3, false, false],
                ["Profile Portraits", "sp/assets/leader/pm/", "png", "img_low/", 3, false, false],
                ["Profile Board Portraits", "sp/assets/leader/talk/", "png", "img/", 3, false, false],
                ["Party Select Portraits", "sp/assets/leader/quest/", "jpg", "img/", 3, false, false],
                ["Tower of Babyl Portraits", "sp/assets/leader/t/", "png", "img_low/", 3, false, false],
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
            switch(asset[4])
            {
                case -1: // for npc
                    files = files;
                    break;
                case -2: // for chara popup portraits
                    files = [id, id+"_001"];
                    break;
                case -3: // for weapon forge headers
                    files = ["job/header/"+id+".png", "number/header/"+id+".png", "seraphic/header/"+id+".png", "xeno/header/"+id+".png", "bahamut/header/"+id+".png", "omega/header/"+id+".png", "draconic/header/"+id+".png", "revans/header/"+id+".png"];
                    break;
                case -4: // for weapon forge portraits
                    files = ["job/result/"+id+".png", "number/result/"+id+".png", "seraphic/result/"+id+".png", "xeno/result/"+id+".png", "bahamut/result/"+id+".png", "omega/result/"+id+".png", "draconic/result/"+id+".png", "revans/result/"+id+".png"];
                    break;
                default:
                    files = obj[asset[4]];
                    break;
            }
            if(files.length == 0) continue; // empty list
            let is_home = false;
            // exceptions
            switch(asset[0])
            {
                case "Quest Portraits":
                    if(search_type == 2)
                        files = [files[0], files[0]+"_hard", files[0]+"_hard_plus", files[0]+"_ex", files[0]+"_ex_plus", files[0]+"_high", files[0]+"_high_plus"]; // summon quest icon
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
                case "Home Arts":
                    is_home = true;
                    break;
            };
            
            let div = addResult(asset[0], asset[0]);
            let file_count = indexed ? files.length : 0;
            if(is_home)
            {
                let img = document.createElement("img");
                img.src = "assets/ui/mypage.png";
                img.classList.add("clickable");
                img.classList.add("mypage-btn");
                img.onclick = togglePreview;
                div.appendChild(img);
            }
            for(let i = 0; i < files.length; ++i)
            {
                let file = files[i];
                if(file_count > 20 && i == DISPLAY_MINI)
                    div = hideNextFiles(div, file_count - DISPLAY_MINI);
                if(asset[3].length > 0)
                {
                    if(!asset[6] && (file.endsWith('_f') || file.endsWith('_f1'))) continue;
                    let img = document.createElement("img");
                    let ref = document.createElement('a');
                    let url_target = null;
                    if(file.endsWith(".png") || file.endsWith(".jpg"))
                    {
                        img.src = getMainEndpoint() + language + asset[3] + asset[1] + file;
                        url_target = img.src;
                    }
                    else
                    {
                        img.src = getMainEndpoint() + language + asset[3] + asset[1] + file + "." + asset[2];
                        url_target = img.src;
                    }
                    ref.setAttribute('href', url_target.replace("img_low", "img").replace("img_mid", "img"));
                    img.classList.add("loading");
                    if(is_home) img.classList.add("homepage"); // use this class name as a flag
                    img.setAttribute('loading', 'lazy');
                    img.onerror = function() {
                        let result = this.parentNode.parentNode;
                        this.parentNode.remove();
                        let n = (this.classList.contains("homepage") ? 3 : 2);
                        if(result.tagName.toLowerCase() == "details")
                        {
                            n -= 1;
                            result = result.parentNode;
                        }
                        this.remove();
                        if(result.childNodes.length <= n) result.remove();
                    };
                    img.onload = function() {
                        this.classList.remove("loading");
                        this.classList.add("asset");
                        if(this.classList.contains("homepage") && previewhome) // set homepage classes if this class if present
                        {
                            this.classList.remove("homepage");
                            this.classList.add("homepage-bg");
                            this.parentNode.classList.add("homepage-ui");
                        }
                    };
                    div.appendChild(ref);
                    ref.appendChild(img);
                }
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
        let file_count = indexed ? npcdata.length : 0;
        for(let asset of assets)
        {
            if(npcdata.length == 0) continue;
            let div = addResult(asset[0], asset[0], ((indexed && asset[0] == "Scene Arts") ? npcdata.length : 0));
            for(let i = 0; i < npcdata.length; ++i)
            {
                let file = npcdata[i];
                if(asset[0] == "Scene Arts" && file_count > 20 && i == 8)
                    div = hideNextFiles(div, file_count - 8);
                if(asset[0] == "Raid Bubble Arts" && no_bubble_scene_suffix.includes(file.split("_").slice(-1)[0])) continue; // ignore those
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
        // additional sorting
        if("Banter" in sorted_sound) sorted_sound["Banter"].sort(customSortPair);
        for(const k of ["Happy Birthday","Happy New Year","Valentine","White Day","Halloween","Christmas"])
        {
            try
            {
                if(k in sorted_sound) sorted_sound[k].sort(customSortSeasonal);
            } catch(errrr) {};
        }
        // loop over categories
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
                    elem.title = "Click to play " + id + sound + ".mp3";
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
                    a.title = "Click to open the link";
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

function loadUnindexed(id, check)// minimal load of an element not indexed or not fully indexed, this is only intended as a cheap placeholder
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
                                data = [true, ["","_up","_laugh","_laugh_up","_laugh2","_laugh2_up","_laugh3","_laugh3_up","_sad","_sad_speed","_sad_up","_angry","_angry_speed","_angry_up","_shadow","_shadow_up","_surprise","_surprise_speed","_surprise_up","_suddenly","_suddenly_up","_suddenly2","_suddenly2_up","_ef","_weak","_weak_up","_a","_b_sad","_town_thug","_narrator","_valentine","_valentine2","_birthday","_birthday2","_birthday3","_birthday3_a","_birthday3_b"],[]];
                                break;
                            default: // playable r, sr, ssr
                                data = [["npc_" + id + "_01.png","npc_" + id + "_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_02"],["" + id + "_01","" + id + "_02"],[],[]];
                                break;
                        };
                        break;
                    case '7': // skins
                        switch(id[2])
                        {
                            case '1': // skins
                                data = [["npc_" + id + "_01.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_01.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_02"],["" + id + "_01","" + id + "_02"],[],[]];
                                break;
                            default:
                                return;
                        };
                        break;
                    case '8': // partners
                        data = [["npc_" + id + "_01.png","npc_" + id + "_0_01.png","npc_" + id + "_1_01.png","npc_" + id + "_02.png","npc_" + id + "_0_02.png","npc_" + id + "_1_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_01_0","" + id + "_01_1","" + id + "_02","" + id + "_02_0","" + id + "_02_1"]];
                        break;
                    case '9': // npcs
                        data = [true, dummy_scene_strings,[]];
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
        updateQuery(last_id);
        loadIndexed(id, data, check, false);
    }
}

function lookup(id)
{
    try
    {
        main_endp_count = -1;
        f = document.getElementById('filter');
        if(
            (id.length == 10 && !isNaN(id)) || 
            (id.length == 5 && id.toLowerCase()[0] === 'b' && !isNaN(id.slice(1))) ||
            (id.length == 6 && id.toLowerCase().startsWith('sk') && !isNaN(id.slice(2))) ||
            (id.length == 7 && id.toLowerCase()[0] === 'q' && !isNaN(id.slice(1))) ||
            (id.length == 8 && id.toLowerCase()[0] === 'e' && !isNaN(id.slice(1))) ||
            (id.length == 6 && !isNaN(id))
        )
        {
            if(blacklist.includes(id)) return;
            // process id
            if(f.value == "" || f.value != id)
            {
                f.value = id;
            }
            let check = null;
            switch(id.length)
            {
                case 10:
                    switch(id.slice(0, 3))
                    {
                        case "305": case "399": check = "npcs"; break;
                        case "304": case "303": case "302": check = "characters"; break;
                        case "371": check = "skins"; break;
                        case "384": case "383": case "382": case "388": case "389": check = "partners"; break;
                        case "204": case "203": case "202": case "201": check = "summons"; break;
                        case "104": case "103": case "102": case "101": check = "weapons"; break;
                    }
                    break;
                case 8: // don't redo the lowercase letter check unless needed
                    id = id.slice(1);
                    check = "enemies";
                    break;
                case 7:
                    id = id.slice(1);
                    check = "events";
                    break;
                case 6:
                    if(id.toLowerCase().startsWith('sk'))
                    {
                        id = id.slice(2);
                        check = "skills";
                    }
                    else
                    {
                        check = "job";
                    }
                    break;
                case 5:
                    id = id.slice(1);
                    check = "buffs";
                    break;
            }
            // cleanup search results if not relevant to current id
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
                loadIndexed(id, index[check][id], check);
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
                loadUnindexed(id, check);
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
                    if(["ssr", "sr", "r", "female", "male"].includes(w))
                    {
                        if(!key.split(" ").includes(w))
                        {
                            matching = false;
                            break;
                        }
                    }
                    else if(!key.includes(w))
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
                if(f.value != id) f.value = id;
            }
            searchResults = positives;
        }
    } catch(error) {
        console.error("Exception thrown", error.stack);
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
    if((id.length == 10 && (id.slice(0, 3) == "302" || id.slice(0, 3) == "303" || id.slice(0, 3) == "304" || id.slice(0, 3) == "371" || id.slice(0, 2) == "10")) || (id.length == 6 && name == "Main Character"))
    {
        l = document.createElement('a');
        l.setAttribute('href', "https://mizagbf.github.io/GBFAP/?id=" + id);
        l.appendChild(document.createTextNode("Animation"));
        div.appendChild(l);
    }
    let did_lookup = false;
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
        did_lookup = true;
    }
    if(!indexed)
    {
        div.appendChild(document.createElement('br'));
        div.appendChild(document.createTextNode("This element isn't indexed, assets will be missing"));
    }
    else if(name == "Character" && id.slice(0, 2) == "30") // partner chara matching
    {
        let cid = "38" + id.slice(2);
        if("partners" in index && cid in index["partners"])
        {
            if(did_lookup) div.appendChild(document.createElement('br'));
            div.appendChild(document.createTextNode("Associated Partner:"));
            div.appendChild(document.createElement('br'));
            let i = document.createElement('i');
            i.classList.add("tag");
            i.onclick = function() {
                lookup(cid);
            };
            div.appendChild(i);
            updateDynamicList(i, [[cid, 6]]);
        }
    }
    else if(name == "Partner") // partner chara matching
    {
        let cid = "30" + id.slice(2);
        if("characters" in index && cid in index["characters"])
        {
            if(did_lookup) div.appendChild(document.createElement('br'));
            div.appendChild(document.createTextNode("Associated Character:"));
            div.appendChild(document.createElement('br'));
            let i = document.createElement('i');
            i.classList.add("tag");
            i.onclick = function() {
                lookup(cid);
            };
            div.appendChild(i);
            updateDynamicList(i, [[cid, 3]]);
        }
    }
    else if(name == "Event") // event
    {
        if("events" in index && id in index["events"] && index["events"][id][1] != null)
        {
            let img = document.createElement("img")
            img.src = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/archive/assets/island_m2/"+index["events"][id][1]+".png"
            div.appendChild(img);
        }
    }
    div.scrollIntoView();
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

function hideNextFiles(div, file_count)
{
    let details = document.createElement("details");
    let summary = document.createElement("summary");
    summary.classList.add("summary-wide");
    summary.innerHTML = "Try to load " + file_count + " Files";
    details.appendChild(summary);
    div.appendChild(details);
    result_area.appendChild(div);
    return details;
}

function togglePreview()
{
    const homepageElements = document.querySelectorAll(".homepage, .homepage-bg");

    homepageElements.forEach(e => {
        if (!previewhome) {
            e.classList.remove("homepage");
            e.classList.add("homepage-bg");
            e.parentNode.classList.add("homepage-ui");
        } else {
            e.classList.remove("homepage-bg");
            e.parentNode.classList.remove("homepage-ui");
            e.classList.add("homepage");
        }
    });

    previewhome = !previewhome;
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
                let onerr = null;
                if(uncap != "_01") onerr = function() {this.src = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/m/"+e[0]+"_01.jpg";};
                addIndexImage(dynarea, "sp/assets/npc/m/" + e[0] + uncap + ".jpg", e[0], onerr);
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
                addIndexImage(dynarea, "sp/assets/enemy/s/" + e[0] + ".png", "e" + e[0], null, "img/").className = "preview";
                break;
            }
            case 5: // npc
            {
                if("npcs" in index && e[0] in index["npcs"] && index["npcs"][e[0]] != 0)
                {
                    if(index["npcs"][e[0]][0])
                        addIndexImage(dynarea, "sp/assets/npc/m/" + e[0] + "_01.jpg", e[0], null);
                    else if(index["npcs"][e[0]][1].length > 0)
                        addIndexImage(dynarea, "sp/quest/scene/character/body/" + e[0] + index["npcs"][e[0]][1][0] + ".png", e[0], function() {
                            this.src = "assets/ui/sound_only.png";
                            this.className = "sound-only";
                        }).className = "preview";
                    else
                        addIndexImage(dynarea, "assets/ui/sound_only.png", e[0], null, "local").className = "sound-only";
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
            case 7: // events
            {
                if("events" in index && e[0] in index["events"] && index["events"][e[0]][0] >= 0)
                {
                    if(index["events"][e[0]][1] == null)
                        addIndexImage(dynarea, "assets/ui/event.png", "q"+e[0], null, "local").className = "sound-only";
                    else
                        addIndexImage(dynarea, "sp/archive/assets/island_m2/" + index["events"][e[0]][1] + ".png", "q"+e[0], null).className = "preview" + (index["events"][e[0]][index["events"][e[0]].length-1].length > 0 ? " sky-event" : "");
                }
                break;
            }
            case 8: // skills
            {
                if("skills" in index && e[0] in index["skills"])
                {
                    addIndexImage(dynarea, "sp/ui/icon/ability/m/" + index["skills"][e[0]][0][0] + ".png", "sk"+e[0], null).className = "preview";
                }
                break;
            }
            case 9: // buffs
            {
                if("buffs" in index && e[0] in index["buffs"])
                {
                    let tmp = addIndexImage(dynarea, "sp/ui/icon/status/x64/status_" + index["buffs"][e[0]][0][0] + ".png", "b"+e[0], null)
                    tmp.classList.add("preview");
                    if(index["buffs"][e[0]][1].length > 0)
                        tmp.classList.add("more");
                }
                break;
            }
            case 10: // backgrounds
            {
                var path = e[0].startsWith("main_") ? ["sp/guild/custom/bg/", ".png"] : ["sp/raid/bg/", ".jpg"];
                addIndexImageGeneric(dynarea, path[0] + e[0] + path[1], e[0], null);
                break;
            }
            case -1: // assets
            {
                let x = e[0].split(":");
                let id = x[1];
                x = x[0];
                switch(x)
                {
                    case "title":
                        addIndexImageGeneric(dynarea, "sp/top/bg/bg_" + id + ".jpg", id, null);
                        break;
                    case "suptix":
                        addIndexImageGeneric(dynarea, "sp/gacha/campaign/surprise/top_" + id + ".jpg", id, null, "preview-wide");
                        break;
                    case "subskills":
                        addIndexImageGeneric(dynarea, "sp/assets/item/ability/s/" + id + "_1.jpg", id+"_1", null);
                        addIndexImageGeneric(dynarea, "sp/assets/item/ability/s/" + id + "_2.jpg", id+"_2", null);
                        addIndexImageGeneric(dynarea, "sp/assets/item/ability/s/" + id + "_3.jpg", id+"_3", null);
                        break;
                }
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
    localStorage.removeItem('gbfal-bookmark');
    document.getElementById('bookmark').parentNode.style.display = "none";
    document.getElementById('favorite').src = "assets/ui/fav_0.png";
}

function exportBookmark()
{
    try
    {
        bookmarks = localStorage.getItem("gbfal-bookmark");
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
            let last_id_f = isNaN(last_id) ? last_id : last_id.replace(/\D/g,''); // strip letters
            while(i < tmp.length)
            {
                let e = tmp[i];
                if(typeof e != 'object' || e.length != 2 || typeof e[0] != 'string' || typeof e[1] != 'number') return;
                if(last_id_f == e[0] && last_type == e[1]) fav = true;
                ++i;
            }
            bookmarks = tmp;
            localStorage.setItem("gbfal-bookmark", JSON.stringify(bookmarks));
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
        bookmarks = localStorage.getItem("gbfal-bookmark");
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
        localStorage.setItem("gbfal-bookmark", JSON.stringify(bookmarks));
    }
    updateBookmark();
}

function clearHistory()
{
    localStorage.removeItem('gbfal-history');
    document.getElementById('history').parentNode.style.display = "none";
}

function updateHistory(id, search_type)
{
    // update local storage
    try
    {
        searchHistory = localStorage.getItem("gbfal-history");
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
        localStorage.setItem("gbfal-history", JSON.stringify(searchHistory));
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
    if("relations" in index && id in index["relations"])
    {
        relarea.innerHTML = "";
        for(let e of index["relations"][id])
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
                    if(val < sr_start || val >= sr_end) continue;
                    break;
                case "4":
                    if(val < ssr_start || val >= ssr_end) continue;
                    break;
            }
            let uncap = "_01";
            if(data != 0)
            {
                for(const f of data[6])
                    if(!f.includes("st") && f[11] != 8 && f.slice(11, 13) != "02" && (f[11] != 9 || (f[11] == 9 && !(["_03", "_04", "_05"].includes(uncap))))) uncap = f.slice(10);
            }
            let onerr = null;
            if(uncap != "_01") onerr = function() {this.src="https://prd-game-a4-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/m/"+id+"_01.jpg"};
            slist[id.padEnd(15, "0")] = ["sp/assets/npc/m/" + id + uncap + ".jpg", id, onerr];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
        {
            addIndexImage(node, slist[k][0], slist[k][1], slist[k][2]);
        }
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
            if(id.slice(0, 2) != i) continue;
            slist[id] = ["sp/assets/enemy/s/" + id + ".png", "e"+id];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            addIndexImage(node, slist[k][0], slist[k][1], null, "img/").className = "preview";;
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

function displayEventNPC(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areaevnpc');
    if("events" in index)
    {
        let slist = {};
        for(const id in index["events"])
        {
            let has_file = false;
            for(let i = 2; i < index["events"][id].length; ++i)
            {
                if(index["events"][id][i].length > 0)
                {
                    has_file = true;
                    break;
                }
            }
            if(has_file)
            {
                if(index["events"][id][1] == null)
                    slist[id] = ["assets/ui/event.png", "q"+id, "sound-only", 0];
                else
                    slist[id] = [ "sp/archive/assets/island_m2/" + index["events"][id][1] + ".png", "q"+id, (index["events"][id][index["events"][id].length-1].length > 0 ? " sky-event":"")];
            }
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
            if(slist[k][2] == "sound-only")
                addIndexImage(node, slist[k][0], slist[k][1], null, "local").className = slist[k][2];
            else
                addIndexImage(node, slist[k][0], slist[k][1]).className = "preview" + slist[k][2];
    }
    this.onclick = null;
}

function displayNPC(elem, i, n)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areanpc'+i);
    let start = 3990000000 + i * 1000;
    let end = 3990000000 + n * 1000;
    if("npcs" in index)
    {
        let slist = {};
        for(const [id, data]  of Object.entries(index["npcs"]))
        {
            let t = parseInt(id);
            if(t < start || t > end) continue;
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
                    addIndexImage(node, slist[k][0], slist[k][1], function() {
                            this.src = "assets/ui/sound_only.png";
                            this.className = "sound-only";
                        }).className = slist[k][2];
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

function displaySkill(elem, i)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areaskill'+i);
    let start = i;
    let end = i + 250;
    if("skills" in index)
    {
        const keys = Object.keys(index["skills"]).sort();
        for(const k of keys)
        {
            let id = parseInt(k);
            if(id >= start && id < end)
            {
                addIndexImage(node, "sp/ui/icon/ability/m/" + index["skills"][k][0][0] + ".png", "sk"+k, null).className = "preview";
            }
        }
    }
    this.onclick = null;
}

function displayBuff(elem, i)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areabuff'+i);
    let start = i;
    let end = i + 250;
    if("buffs" in index)
    {
        const keys = Object.keys(index["buffs"]).sort();
        for(const k of keys)
        {
            let id = parseInt(k);
            if(id >= start && id < end)
            {
                let tmp = addIndexImage(node, "sp/ui/icon/status/x64/status_" + index["buffs"][k][0][0] + ".png", "b"+k, null);
                tmp.classList.add("preview");
                if(index["buffs"][k][1].length > 0)
                    tmp.classList.add("more");
            }
        }
    }
    this.onclick = null;
}

function addIndexImageGeneric(node, path, id, onerr, className = "preview")
{
    let a = document.createElement("a");
    let img = document.createElement("img");
    a.appendChild(img);
    node.appendChild(a);
    img.classList.add("loading");
    img.setAttribute('loading', 'lazy');
    img.onload = function() {
        this.classList.remove("loading");
        this.classList.add(className);
        this.classList.add("link");
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
    img.title = "Click to open: " + img.src.split('/').slice(-1);
    a.href = img.src.replace("img_low/", "img/");
}

function displaySubSkill(elem)
{
    elem.removeAttribute("onclick");
    let node = document.getElementById('areasubskill');
    if("subskills" in index)
    {
        let slist = {};
        for(const id in index["subskills"])
        {
            slist[id.padStart(9, "0")] = id;
        }
        const keys = Object.keys(slist).sort();
        for(const k of keys)
        {
            const id = slist[k];
            addIndexImageGeneric(node, "sp/assets/item/ability/s/" + id + "_1.jpg", id+"_1", null);
            addIndexImageGeneric(node, "sp/assets/item/ability/s/" + id + "_2.jpg", id+"_2", null);
            addIndexImageGeneric(node, "sp/assets/item/ability/s/" + id + "_3.jpg", id+"_3", null);
        }
    }
    this.onclick = null;
}

function displayBG(elem, i=null)
{
    elem.removeAttribute("onclick");
    let node = (i==null ? document.getElementById('areabg') : document.getElementById('areabg'+i));
    if("background" in index)
    {
        let slist = {};
        for(const [id, data] of Object.entries(index["background"]))
        {
            slist[id.padStart(9, "0")] = [id, data];
        }
        const keys = Object.keys(slist).sort().reverse();
        for(const k of keys)
        {
            const id = slist[k][0];
            const data = slist[k][1];
            const path = id.startsWith("main_") ? ["sp/guild/custom/bg/", ".png"] : ["sp/raid/bg/", ".jpg"];
            if((i == null && !id.startsWith("common") && !id.startsWith("event") && !id.startsWith("main")) || id.startsWith(i))
            {
                for(let j = data[0].length - 1; j >= 0; --j)
                {
                    addIndexImageGeneric(node, path[0] + data[0][j] + path[1], data[0][j], null);
                }
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