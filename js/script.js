// =================================================================================================
// constant
const DISPLAY_MINI = 4; // number of file to display at the minimum if a lot of files are present
const HIDE_DISPLAY = 21; // number of file to trigger the "load more" button
const HISTORY_LENGTH = 20; // size limit of the history
// endpoints
const ENDPOINTS = [
    "https://prd-game-a-granbluefantasy.akamaized.net/",
    "https://prd-game-a1-granbluefantasy.akamaized.net/",
    "https://prd-game-a2-granbluefantasy.akamaized.net/",
    "https://prd-game-a3-granbluefantasy.akamaized.net/",
    "https://prd-game-a4-granbluefantasy.akamaized.net/",
    "https://prd-game-a5-granbluefantasy.akamaized.net/"
];
var endpoint_count = -1;
// list of known scene strings for unindexed characters
const DUMMY_SCENE = ["", "_a", "_b", "_up", "_laugh", "_wink", "_shout", "_sad", "_angry", "_cry", "_painful", "_shadow", "_light", "_close", "_serious", "_surprise", "_think", "_serious", "_mood", "_ecstasy", "_suddenly", "_speed", "_shy", "_weak", "_sleepy", "_open", "_bad", "_amaze", "_joy", "_pride", "_intrigue", "_motivation", "_melancholy", "_concentration", "_weapon", "_foot"];
// list of scene suffixes to ignore for raid bubbles
const NO_BUBBLE_FILTER = ["speed", "up", "up2", "u3", "up4", "shadow", "shadow2", "shadow3", "light", "blood"];
// HTML UI indexes
const CHARACTERS = [
    ["Year 2024 (Dragon)", "assets/ui/index_icon/year_2024_(dragon).png", [0, -1, 0, -1, 504, 999]],
    ["Year 2023 (Rabbit)", "assets/ui/index_icon/year_2023_(rabbit).png", [0, -1, 0, -1, 443, 504]],
    ["Year 2022 (Tiger)", "assets/ui/index_icon/year_2022_(tiger).png", [0, -1, 0, -1, 379, 443]],
    ["Year 2021 (Ox)", "assets/ui/index_icon/year_2021_(ox).png", [74, 75, 0, -1, 316, 379]],
    ["Year 2020 (Rat)", "assets/ui/index_icon/year_2020_(rat).png", [73, 74, 281, 323, 256, 316]],
    ["Year 2019 (Pig)", "assets/ui/index_icon/year_2019_(pig).png", [72, 73, 263, 281, 199, 256]],
    ["Year 2018 (Dog)", "assets/ui/index_icon/year_2018_(dog).png", [71, 72, 233, 263, 149, 199]],
    ["Year 2017 (Chicken)", "assets/ui/index_icon/year_2017_(chicken).png", [0, -1, 173, 233, 108, 149]],
    ["Year 2016 (Monkey)", "assets/ui/index_icon/year_2016_(monkey).png", [47, 71, 113, 173, 72, 108]],
    ["Year 2015 (Sheep)", "assets/ui/index_icon/year_2015_(sheep).png", [30, 47, 51, 113, 30, 72]],
    ["Year 2014", "assets/ui/index_icon/year_2014.png", [0, 30, 0, 51, 0, 30]]
];
const SKINS = [
    ["ID 200 to 299", [200, 300]],
    ["ID 100 to 199", [100, 200]],
    ["ID 000 to 099", [0, 100]]
];
const PARTNERS = [
    ["Main", "89", "assets/ui/icon/main.png"],
    ["Special", "88", "assets/ui/icon/other.png"],
    ["SSR", "84", "assets/ui/icon/ssr.png"],
    ["SR", "83", "assets/ui/icon/sr.png"],
    ["R", "82", "assets/ui/icon/r.png"]
];
const SUMMONS = [
    ["SSR ID 400 to 599", "4", [400, 600], "assets/ui/icon/ssr.png"],
    ["SSR ID 200 to 399", "4", [200, 400], "assets/ui/icon/ssr.png"],
    ["SSR ID 000 to 199", "4", [0, 200], "assets/ui/icon/ssr.png"],
    ["SR", "3", [0, 1000], "assets/ui/icon/sr.png"],
    ["R", "2", [0, 1000], "assets/ui/icon/r.png"],
    ["N", "1", [0, 1000], "assets/ui/icon/n.png"]
];
const WEAPONS_RARITY = [
    ["SSR", "4", "assets/ui/icon/ssr.png"],
    ["SR", "3", "assets/ui/icon/sr.png"],
    ["R", "2", "assets/ui/icon/r.png"],
    ["N", "1", "assets/ui/icon/n.png"]
];
const WEAPONS = [
    ["Sword", "0", "assets/ui/icon/sword.png"],
    ["Dagger", "1", "assets/ui/icon/dagger.png"],
    ["Spear", "2", "assets/ui/icon/spear.png"],
    ["Axe", "3", "assets/ui/icon/axe.png"],
    ["Staff", "4", "assets/ui/icon/staff.png"],
    ["Gun", "5", "assets/ui/icon/gun.png"],
    ["Melee", "6", "assets/ui/icon/melee.png"],
    ["Bow", "7", "assets/ui/icon/bow.png"],
    ["Harp", "8", "assets/ui/icon/harp.png"],
    ["Katana", "9", "assets/ui/icon/katana.png"]
];
const ENEMIES = [
    ["Beasts and Animals", "1", "assets/ui/index_icon/1.png", [["Flying", "assets/ui/index_icon/flying.png"], ["Beasts", "assets/ui/index_icon/beasts.png"], ["Monstrosities", "assets/ui/index_icon/monstrosities.png"]]],
    ["Plants and Insects", "2", "assets/ui/index_icon/2.png", [["Plants", "assets/ui/index_icon/plants.png"], ["Insects", "assets/ui/index_icon/insects.png"], ["???", "assets/ui/index_icon/unkn.png"]]],
    ["Fishes and Sea Life", "3", "assets/ui/index_icon/3.png", [["Sea Life", "assets/ui/index_icon/sea_life.png"], ["???", "assets/ui/index_icon/unkn.png"], ["???", "assets/ui/index_icon/unkn.png"]]],
    ["Golems and Robots", "4", "assets/ui/index_icon/4.png", [["Golems", "assets/ui/index_icon/golems.png"], ["Aberrations", "assets/ui/index_icon/aberrations.png"], ["Machines", "assets/ui/index_icon/machines.png"]]],
    ["Undeads and Otherworlders", "5", "assets/ui/index_icon/5.png", [["Otherwordly", "assets/ui/index_icon/otherwordly.png"], ["Undeads", "assets/ui/index_icon/undeads.png"], ["???", "assets/ui/index_icon/unkn.png"]]],
    ["Humans and Humanoids", "6", "assets/ui/index_icon/6.png", [["Goblins", "assets/ui/index_icon/goblins.png"], ["People", "assets/ui/index_icon/people.png"], ["Fairies", "assets/ui/index_icon/fairies.png"]]],
    ["Dragons and Wyverns", "7", "assets/ui/index_icon/7.png", [["Dragons", "assets/ui/index_icon/dragons.png"], ["Reptiles", "assets/ui/index_icon/reptiles.png"], ["True Dragons", "assets/ui/index_icon/true_dragons.png"]]],
    ["Primal Beasts", "8", "assets/ui/index_icon/8.png", [["Primals", "assets/ui/index_icon/primals.png"], ["Elementals", "assets/ui/index_icon/elementals.png"], ["Angel Cores", "assets/ui/index_icon/angel_cores.png"]]],
    ["Astrals and Others", "9", "assets/ui/index_icon/9.png", [["Others", "assets/ui/index_icon/others.png"], ["???", "assets/ui/index_icon/unkn.png"], ["???", "assets/ui/index_icon/unkn.png"]]]
];
const NPCS = [
    ["Special", "assets/ui/index_icon/special.png", "05", [0, 100000]],
    ["Year 2024 (Dragon)", "assets/ui/index_icon/year_2024_(dragon).png", "99", [3391, 100000]],
    ["Year 2023 (Rabbit)", "assets/ui/index_icon/year_2023_(rabbit).png", "99", [2915, 3188], [3188, 3391]],
    ["Year 2022 (Tiger)", "assets/ui/index_icon/year_2022_(tiger).png", "99", [2519, 2714], [2714, 2915]],
    ["Year 2021 (Ox)", "assets/ui/index_icon/year_2021_(ox).png", "99", [2008, 2248], [2248, 2519]],
    ["Year 2020 (Rat)", "assets/ui/index_icon/year_2020_(rat).png", "99", [1637, 1814], [1814, 2008]],
    ["Year 2019 (Pig)", "assets/ui/index_icon/year_2019_(pig).png", "99", [1254, 1432], [1432, 1637]],
    ["Year 2018 (Dog)", "assets/ui/index_icon/year_2018_(dog).png", "99", [981, 1092], [1092, 1254]],
    ["Year 2017 (Chicken)", "assets/ui/index_icon/year_2017_(chicken).png", "99", [603, 735], [735, 981]],
    ["Year 2016 (Monkey)", "assets/ui/index_icon/year_2016_(monkey).png", "99", [378, 476], [476, 603]],
    ["Years 2014 & 2015", "assets/ui/index_icon/years_2014_&_2015.png", "99", [0, 239], [239, 378]]
];
const SKILLS = [
    ["assets/ui/index_icon/skill1.png", [0, 250], [250, 500], [500, 750], [750, 1000]],
    ["assets/ui/index_icon/skill2.png", [1000, 1250], [1250, 1500], [1500, 1750], [1750, 2000]],
    ["assets/ui/index_icon/skill3.png", [2000, 2250], [2250, 2500], [2500, 2750], [2750, 3000]]
];
const BUFFS = [
    ["Old Set", "assets/ui/index_icon/old_set.png", [0, 1000]],
    ["Basic Set", "assets/ui/index_icon/basic_set.png", [1000, 1250], [1250, 1500], [1500, 1750], [1750, 2000], [2000, 2250], [2250, 2500], [2500, 2750], [2750, 3000]],
    ["Unique Set 1", "assets/ui/index_icon/unique_set_1.png", [3000, 3250], [3250, 3500], [3500, 3750], [3750, 4000]],
    ["Unique Set 2", "assets/ui/index_icon/unique_set_2.png", [4000, 4250], [4250, 4500], [4500, 4750], [4750, 5000]],
    ["Field Effect Set", "assets/ui/index_icon/field_effect_set.png", [5000, 5250], [5250, 5500], [5500, 5750], [5750, 6000]],
    ["Buff Set", "assets/ui/index_icon/buff_set.png", [6000, 6250], [6250, 6500], [6500, 6750], [6750, 7000], [7000, 7250], [7250, 7500], [7500, 7750], [7750, 8000]],
    ["Old Stack Set", "assets/ui/index_icon/old_stack_set.png", [8000, 10000]]
];
const BACKGROUNDS = [
    ["Mains", "main"],
    ["Commons", "common"],
    ["Events", "event"],
    ["Others", ""]
];


// add id here to disable some elements
const BANNED = [

];

// =================================================================================================
// global variables
var output = null; // contain the html output element
var last_id = null; // last id loaded
var last_type = null; // last asset type loaded
var index = {}; // data index (loaded from data.json)
var searchHistory = []; // history
var searchResults = []; // search results
var searchID = null; // search result id
var bookmarks = []; // bookmarks
var timestamp = Date.now(); // timestamp (loaded from changelog.json)
var updated = []; // list of recently updated elements (loaded from changelog.json)
var intervals = []; // on screen notifications
var typingTimer; // typing timer timeout
var audio = null; // last played/playing audio
var previewhome = false; // boolean to keep track of mypage preview

// =================================================================================================
// initialization
function init() // entry point, called by body onload
{
    loadPreviewSetting();
    openTab('index'); // set to this tab by default
    output = document.getElementById('output'); // set output
    getJSON("json/changelog.json?" + timestamp, initChangelog); // load changelog
}

function getJSON(url, callback) { // generic function to request a file. will always call the callback no matter the result.
    var xhr = new XMLHttpRequest();
    xhr.ontimeout = function () {
        callback.apply(xhr);
    };
    xhr.onload = function() {
        if (xhr.readyState === 4) {
            callback.apply(xhr);
        }
    };
    xhr.open("GET", url, true);
    xhr.timeout = 60000;
    xhr.send(null);
}

function initChangelog() // load content of changelog.json
{
    try
    {
        let json = JSON.parse(this.response);
        if(json.hasOwnProperty("new")) // set updated
            updated = json["new"].reverse();
        timestamp = json.timestamp; // set timestamp
        clock(); // start the clock
        if(json.hasOwnProperty("issues")) // read issues, if any
        {
            let issues = json["issues"];
            if(issues.length > 0)
            {
                let el = document.getElementById("issues");
                el.innerHTML += "<ul>"
                for(let i = 0; i < issues.length; ++i) el.innerHTML += "<li>"+issues[i]+"</li>\n";
                el.innerHTML += "</ul>"
                el.style.display = null;
            }
        }
    }
    catch(err)
    {
        console.error("Exception thrown", err.stack);
    }
    getJSON("json/data.json?" + timestamp, initData); // load data.json next
}

function initData() // load data.json
{
    try
    {
        index = JSON.parse(this.response); // read
        index["lookup_reverse"] = swap(index["lookup"]); // create reversed lookup
        if(updated.length > 0) // init Updated list
        {
            updateList(document.getElementById('new'), updated);
        }
        toggleBookmark(); // init bookmark
        updateHistory(); // init history
    }
    catch(err)
    {
        console.error("Exception thrown", err.stack);
        // put a message if GBFAL is broken
        let el = document.getElementById("issues");
        el.innerHTML = '<p>A critical error occured, please report the issue if it persists.<br>You can also try to clear your cache or do a CTRL+F5.<br><a href="https://mizagbf.github.io/">Home Page</a><br><a href="https://github.com/MizaGBF/GBFAL/issues">Github</a></p>'
        el.style.display = null;
    }
    // init index
    initIndex();
    // load id if it's present in the url
    let params = new URLSearchParams(window.location.search);
    let id = params.get("id");
    if(id != null)
    {
        lookup(id);
    }
}

function initIndex() // build the html index. simply edit the constants above to change the index.
{
    let content = document.getElementById('index');
    try
    {
        content.innerHTML = "";
        let parents = null;
        let inter = null;
        let elems = null;
        parents = makeIndexSummary(content, "Characters", true, 0, "assets/ui/icon/characters.png");
        for(let i of CHARACTERS)
        {
            elems = makeIndexSummary(parents[0], i[0], false, 1, i[1]);
            const tmp = [elems[0], i[2]];
            elems[1].onclick = function (){
                display(tmp[0], 'characters', tmp[1], null, false, true);
                this.onclick = null;
            };
        }
        parents = makeIndexSummary(content, "Skins", true, 0, "assets/ui/icon/skins.png");
        for(let i of SKINS)
        {
            elems = makeIndexSummary(parents[0], i[0], false, 1);
            const tmp = [elems[0], i[1]];
            elems[1].onclick = function (){
                display(tmp[0], 'skins', tmp[1], null, false, true);
                this.onclick = null;
            };
        }
        parents = makeIndexSummary(content, "Partners", true, 0, "assets/ui/icon/partners.png");
        for(let i of PARTNERS)
        {
            elems = makeIndexSummary(parents[0], i[0], false, 1, i[2]);
            const tmp = [elems[0], i[1]];
            elems[1].onclick = function (){
                display(tmp[0], 'partners', tmp[1], null, false, true);
                this.onclick = null;
            };
        }
        parents = makeIndexSummary(content, "Summons", true, 0, "assets/ui/icon/summons.png");
        for(let i of SUMMONS)
        {
            elems = makeIndexSummary(parents[0], i[0], false, 1, i[3]);
            const tmp = [elems[0], i[1], i[2]];
            elems[1].onclick = function (){
                display(tmp[0], 'summons', tmp[1], tmp[2], false, true);
                this.onclick = null;
            };
        }
        parents = makeIndexSummary(content, "Weapons", true, 0, "assets/ui/icon/weapons.png");
        for(let i of WEAPONS_RARITY)
        {
            let inter = makeIndexSummary(parents[0], i[0], true, 1, i[2]);
            for(let j of WEAPONS)
            {
                elems = makeIndexSummary(inter[0], j[0], false, 2, j[2]);
                const tmp = [elems[0], i[1], j[1]];
                elems[1].onclick = function (){
                    display(tmp[0], 'weapons', tmp[1], tmp[2], false, true);
                    this.onclick = null;
                };
            }
        }
        elems = makeIndexSummary(content, "Main Character", false, 0, "assets/ui/icon/classes.png");
        {
            const tmp = elems[0];
            elems[1].onclick = function (){
                display(tmp, 'job', null, null, false, true);
                this.onclick = null;
            };
        }
        parents = makeIndexSummary(content, "Enemies", true, 0, "assets/ui/icon/enemies.png");
        for(let i of ENEMIES)
        {
            let inter = makeIndexSummary(parents[0], i[0], true, 1, i[2]);
            for(let j = 0; j < 3; ++j)
            {
                let k = i[3][j];
                elems = makeIndexSummary(inter[0], k[0], false, 2, k[1]);
                const tmp = [elems[0], i[1], j+1];
                elems[1].onclick = function (){
                    display(tmp[0], 'enemies', tmp[1], tmp[2], false, true);
                    this.onclick = null;
                };
            }
        }
        parents = makeIndexSummary(content, "NPCs", true, 0, "assets/ui/icon/npcs.png");
        for(let i of NPCS)
        {
            if(i.length > 4)
            {
                let inter = makeIndexSummary(parents[0], i[0], true, 1, i[1]);
                for(let j = 3; j < i.length; ++j)
                {
                    elems = makeIndexSummary(inter[0], (j == 3 ? "First Half" : (j == 4 ? "Second Half" : "???")), false, 2);
                    const tmp = [elems[0], i[2], i[j]];
                    elems[1].onclick = function (){
                        display(tmp[0], 'npcs', tmp[1], tmp[2], false, false);
                        this.onclick = null;
                    };
                }
            }
            else
            {
                elems = makeIndexSummary(parents[0], i[0], false, 1, i[1]);
                const tmp = [elems[0], i[2], i[3]];
                elems[1].onclick = function (){
                    display(tmp[0], 'npcs', tmp[1], tmp[2], false, false);
                    this.onclick = null;
                };
            }
        }
        elems = makeIndexSummary(content, "Valentine / White Day", false, 0, "assets/ui/index_icon/special.png");
        {
            const tmp = elems[0];
            elems[1].onclick = function (){
                display(tmp, 'valentines', null, null, false, false, override_text="This list accuracy isn't guaranted");
                this.onclick = null;
            };
        }
        elems = makeIndexSummary(content, "Main Story", false, 0, "assets/ui/icon/story.png");
        {
            const tmp = elems[0];
            elems[1].onclick = function (){
                display(tmp, 'story', null, null, false, true);
                this.onclick = null;
            };
        }
        elems = makeIndexSummary(content, "Events", false, 0, "assets/ui/icon/events.png");
        {
            const tmp = elems[0];
            elems[1].onclick = function (){
                display(tmp, 'events', null, null, false, true);
                this.onclick = null;
            };
        }
        parents = makeIndexSummary(content, "Skills", true, 0, "assets/ui/icon/skills.png");
        for(let i of SKILLS)
        {
            const name = "ID " + JSON.stringify(i[1][0]).padStart(4, "0") + " to " + JSON.stringify(i[i.length-1][1]-1).padStart(4, "0");
            let inter = makeIndexSummary(parents[0], name, true, 1, i[0]);
            for(let j = 1; j < i.length; ++j)
            {
                elems = makeIndexSummary(inter[0], "ID " + JSON.stringify(i[j][0]).padStart(4, "0") + " to " + JSON.stringify(i[j][1]-1).padStart(4, "0"), false, 2);
                const tmp = [elems[0], i[j]];
                elems[1].onclick = function (){
                    display(tmp[0], 'skills', tmp[1],null, false, false);
                    this.onclick = null;
                };
            }
        }
        elems = makeIndexSummary(content, "Sub Skills", false, 0, "assets/ui/icon/subskills.png");
        {
            const tmp = elems[0];
            elems[1].onclick = function (){
                display(tmp, 'subskills', null, null, false, false);
                this.onclick = null;
            };
        }
        parents = makeIndexSummary(content, "Buffs", true, 0, "assets/ui/icon/buffs.png");
        for(let i of BUFFS)
        {
            if(i.length > 3)
            {
                let inter = makeIndexSummary(parents[0], i[0], true, 1, i[1]);
                for(let j = 2; j < i.length; ++j)
                {
                    elems = makeIndexSummary(inter[0], "ID " + JSON.stringify(i[j][0]).padStart(4, "0") + " to " + JSON.stringify(i[j][1]-1).padStart(4, "0"), false, 2);
                    const tmp = [elems[0], i[j]];
                    elems[1].onclick = function (){
                        display(tmp[0], 'buffs', tmp[1], null, false, false);
                        this.onclick = null;
                    };
                }
            }
            else
            {
                elems = makeIndexSummary(parents[0], i[0], false, 1, i[1]);
                const tmp = [elems[0], i[2]];
                elems[1].onclick = function (){
                    display(tmp[0], 'buffs', tmp[1], null, false, false);
                    this.onclick = null;
                };
            }
        }
        parents = makeIndexSummary(content, "Backgrounds", true, 0, "assets/ui/icon/backgrounds.png");
        for(let i of BACKGROUNDS)
        {
            elems = makeIndexSummary(parents[0], i[0], false, 1);
            const tmp = [elems[0], i[1], i[2]];
            elems[1].onclick = function (){
                display(tmp[0], 'background', tmp[1], tmp[2], true, true);
                this.onclick = null;
            };
        }
        elems = makeIndexSummary(content, "Title Screens", true, 0, "assets/ui/icon/titles.png");
        {
            const tmp = elems[0];
            elems[1].onclick = function (){
                display(tmp, 'title', null, null, true, false);
                this.onclick = null;
            };
        }
        elems = makeIndexSummary(content, "Suprise Tickets", true, 0, "assets/ui/icon/suptix.png");
        {
            const tmp = elems[0];
            elems[1].onclick = function (){
                display(tmp, 'suptix', null, null, true, true);
                this.onclick = null;
            };
        }
    }
    catch(err)
    {
        if(content != null)
            content.innerHTML = '<div class="container">An error occured while loading the index.<br>Please notify me if you see this message.</div>';
    }
}

// =================================================================================================
// html related
function clock() // update the "last updated" clock
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

function resetTabs() // reset the tab state
{
    let tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++)
        tabcontent[i].style.display = "none";
    let tabbuttons = document.getElementsByClassName("tabbutton");
    for (let i = 0; i < tabbuttons.length; i++)
        tabbuttons[i].classList.remove("active");
}

function openTab(tabName) // reset and then select a tab
{
    resetTabs();
    document.getElementById(tabName).style.display = "";
    document.getElementById("tab-"+tabName).classList.add("active");
}

function togglePreview() // toggle mypage preview
{
    const homepageElements = document.querySelectorAll(".homepage, .homepage-bg");

    homepageElements.forEach(e => {
        if (!previewhome) {
            e.classList.remove("asset");
            e.classList.remove("homepage");
            e.classList.add("homepage-bg");
            e.src = e.src.replace('/img_low/', '/img/');
            e.parentNode.classList.add("homepage-ui");
        } else {
            e.classList.remove("homepage-bg");
            e.parentNode.classList.remove("homepage-ui");
            e.src = e.src.replace('/img/', '/img_low/');
            e.classList.add("asset");
            e.classList.add("homepage");
        }
    });

    previewhome = !previewhome;
    storePreviewSetting();
}

// =================================================================================================
// utility
function cycleEndpoint() // return one of the endpoint, one after the other (to benefit from the sharding)
{
    endpoint_count = (endpoint_count + 1) % ENDPOINTS.length;
    return ENDPOINTS[endpoint_count];
}

function idToEndpoint(id) // use the id as a seed to return one of the endpoints (to benefit from the sharding)
{
    return ENDPOINTS[parseInt(id.replace(/\D/g,'')) % ENDPOINTS.length];
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

function makeIndexSummary(node, name, is_parent, sub_level, icon = null) // used for the html. make the details/summary elements.
{
    let details = document.createElement("details");
    let summary = document.createElement("summary");
    summary.classList.add("element-detail");
    if(sub_level > 0)
    {
        summary.classList.add("sub-detail");
        if(sub_level > 1) summary.classList.add("sub-detail-child");
    }
    if(icon != null && icon != "")
    {
        let img = document.createElement("img");
        img.classList.add(sub_level ? "sub-detail-icon" : "detail-icon");
        img.src = icon;
        summary.appendChild(img);
    }
    else
    {
        let div = document.createElement("span");
        div.classList.add(sub_level ? "sub-detail-icon" : "detail-icon");
        summary.appendChild(div);
    }
    summary.appendChild(document.createTextNode(name));
    details.appendChild(summary);
    node.appendChild(details);
    if(is_parent)
    {
        let div = document.createElement("div");
        div.className = "subdetails";
        details.appendChild(div);
        return [div, details];
    }
    else
    {
        let h3 = document.createElement("h3");
        h3.className = "container mobile-big";
        details.appendChild(h3);
        return [h3, details];
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

window.addEventListener("popstate", (event) => { // load the appropriate element when user does back or forward
    let params = new URLSearchParams(window.location.search);
    let id = params.get("id");
    if(id)
    {
        lookup(id);
    }
});

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

function customSortBoss(a, b) // used to sort boss sound files
{
    let A = a.split('_');
    A = parseInt(A[A.length-1].replaceAll(/\D/g,''), 10);
    let B = b.split('_');
    B = parseInt(B[B.length-1].replaceAll(/\D/g,''), 10);
    return A-B;
}

function customSortSeasonal(a, b) // used to sort seasonal sound files
{
    const baseA = a.replaceAll(/\d+$/, '');
    const baseB = b.replaceAll(/\d+$/, '');

    if (baseA < baseB) return -1;
    if (baseA > baseB) return 1;

    const numA = parseInt(a.slice(baseA.length), 10);
    const numB = parseInt(b.slice(baseB.length), 10);

    return numA - numB;
}

// =================================================================================================
// visual elements management
function display(node, key, argA, argB, pad, reverse, override_text = null) // generic function to display the index lists
{
    let callback = null;
    let image_callback = addIndexImage;
    switch(key)
    {
        case "characters":
            callback = display_characters;
            break;
        case "skins":
            callback = display_skins;
            break;
        case "partners":
            callback = display_partners;
            break;
        case "summons":
            callback = display_summons;
            break;
        case "weapons":
            callback = display_weapons;
            break;
        case "job":
            callback = display_mc;
            break;
        case "enemies":
            callback = display_enemies;
            break;
        case "npcs":
            callback = display_npcs;
            break;
        case "valentines":
            callback = display_valentines;
            break;
        case "story":
            callback = display_story;
            image_callback = addTextImage;
            break;
        case "events":
            callback = display_events;
            break;
        case "skills":
            callback = display_skills;
            break;
        case "subskills":
            callback = display_subskills;
            break;
        case "buffs":
            callback = display_buffs;
            break;
        case "background":
            callback = display_backgrounds;
            break;
        case "title":
            callback = display_titles;
            break;
        case "suptix":
            callback = display_suptix;
            break;
    }
    if(key in index)
    {
        let slist = {};
        for(const [id, data] of Object.entries(index[key]))
        {
            let r = callback(id, data, argA, argB);
            if(r != null)
            {
                if(pad) slist[id.padStart(20, "0")] = r;
                else slist[id] = r;
            }
        }
        const keys = reverse ? Object.keys(slist).sort().reverse() : Object.keys(slist).sort();
        if(keys.length > 0)
        {
            if(override_text != null) node.innerHTML = "<div>"+override_text+"</div>";
            else node.innerHTML = reverse ? "<div>Newest first</div>" : "<div>Oldest first</div>";
        }
        else node.innerHTML = '<div>Empty</div><img src="assets/ui/sorry.png">'
        for(const k of keys)
        {
            for(let r of slist[k])
            {
                image_callback(node, r[1], r[0], r[2], r[3], r[4]);
            }
        }
    }
    else node.innerHTML = '<div>Empty</div><img src="assets/ui/sorry.png">';
}

function default_onerror()
{
    this.src=idToEndpoint("0") + "assets_en/img/sp/assets/npc/m/3999999999.jpg";
    this.classList.remove("preview");
    this.classList.remove("preview-noborder");
}

function display_characters(id, data, range, unused = null)
{
    let val = parseInt(id.slice(4, 7));
    switch(id[2])
    {
        case '4':
            if(val < range[4] || val >= range[5]) return null;
            break;
        case '3':
            if(val < range[2] || val >= range[3]) return null;
            break;
        case '2':
            if(val < range[0] || val >= range[1]) return null;
            break;
        default:
            return null;
    }
    let uncap = "_01";
    if(data)
    {
        for(const f of data[6])
            if(!f.includes("st") && f[11] != 8 && f.slice(11, 13) != "02" && (f[11] != 9 || (f[11] == 9 && !(["_03", "_04", "_05"].includes(uncap))))) uncap = f.slice(10);
    }
    let onerr = null;
    if(uncap != "_01")
        onerr = function() {this.src=idToEndpoint(id) + "assets_en/img_low/sp/assets/npc/m/"+id+"_01.jpg"; this.onerror=default_onerror;};
    else
        onerr = default_onerror;
    let path = "GBF/assets_en/img_low/sp/assets/npc/m/" + id + uncap + ".jpg";
    return [[id, path, onerr, "", false]];
}

function display_skins(id, data, range, unused = null)
{
    let val = parseInt(id.slice(4, 7));
    if(val < range[0] || val >= range[1]) return null;
    let uncap = "_01";
    if(data)
    {
        for(const f of data[6])
            if(!f.includes("st") && f[11] != 8 && f.slice(11, 13) != "02" && (f[11] != 9 || (f[11] == 9 && !(["_03", "_04", "_05"].includes(uncap))))) uncap = f.slice(10);
    }
    let onerr = null;
    if(uncap != "_01")
        onerr = function() {this.src=idToEndpoint(id) + "assets_en/img_low/sp/assets/npc/m/"+id+"_01.jpg"; this.onerror=default_onerror;};
    else
        onerr = default_onerror;
    let path = "GBF/assets_en/img_low/sp/assets/npc/m/" + id + uncap + ".jpg";
    return [[id, path, onerr, "", false]];
}

function display_partners(id, data, prefix, unused = null)
{
    if(id.slice(1, 3) != prefix) return null;
    let onerr = function() {
        this.src = idToEndpoint(id) + "assets_en/img_low/sp/assets/npc/raid_normal/3999999999.jpg";
    };
    let path = null;
    if(data && data[5].length > 0)
    {
        let onerr;
        if(data[5].length > 1)
        {
            onerr = function() { // failsafe
                this.onerror = function() {
                    this.src =  idToEndpoint(id) + "assets_en/img_low/sp/assets/npc/raid_normal/3999999999.jpg";
                };
                this.src =  idToEndpoint(id) + "assets_en/img_low/sp/assets/npc/raid_normal/" + data[5][1] + ".jpg";
            };
        }
        path =  "GBF/assets_en/img_low/sp/assets/npc/raid_normal/" + data[5][0] + ".jpg";
    }
    else
    {
        path =  "GBF/assets_en/img_low/sp/assets/npc/raid_normal/" + id + "_01.jpg";
    }
    return [[id, path, onerr, "preview", false]];
}

function display_summons(id, data, rarity, range)
{
    if(id[2] != rarity) return null;
    let val = parseInt(id.slice(4, 7));
    if(val < range[0] || val >= range[1]) return null;
    let uncap = "";
    if(data)
    {
        for(const f of data[0])
            if(f.includes("_")) uncap = f.slice(10);
    }
    let onerr = null;
    if(uncap != "")
        onerr = function() {this.src=idToEndpoint(id) + "assets_en/img_low/sp/assets/summon/m/"+id+".jpg"; this.onerror=default_onerror;};
    else
        onerr = default_onerror;
    let path = "GBF/assets_en/img_low/sp/assets/summon/m/" + id + uncap + ".jpg";
    return [[id, path, onerr, "", false]];
}

function display_weapons(id, data, rarity, proficiency)
{
    if(id[2] != rarity || id[4] != proficiency) return null;
    let uncap = "";
    if(data)
    {
        for(const f of data[0])
            if(f.includes("_")) uncap = f.slice(10);
    }
    let onerr = null;
    if(uncap != "")
        onerr = function() {this.src=idToEndpoint(id) + "assets_en/img_low/sp/assets/weapon/m/"+id+".jpg"; this.onerror=default_onerror;};
    else
        onerr = default_onerror;
    let path = "GBF/assets_en/img_low/sp/assets/weapon/m/" + id + uncap + ".jpg";
    return [[id, path, onerr, "", false]];
}

function display_mc(id, data, unusedA = null, unusedB = null)
{
    return [[id, "GBF/assets_en/img_low/sp/assets/leader/m/" + id + "_01.jpg", default_onerror, "", false]];
}

function display_enemies(id, data, type, size)
{
    if(id[0] != type || id[1] != size) return null;
    return [["e"+id, "GBF/assets_en/img/sp/assets/enemy/s/" + id + ".png", default_onerror, "preview", false]];
}

function display_npcs(id, data, prefix, range)
{
    if(id.slice(1, 3) != prefix) return null;
    let val = parseInt(id.slice(3, 7));
    if(val < range[0] || val >= range[1]) return null;
    let path = ""
    let className = "";
    if(data)
    {
        if(data[0])
        {
            path = "GBF/assets_en/img_low/sp/assets/npc/m/" + id + "_01.jpg";
        }
        else if(data[1].length > 0)
        {
            path = "GBF/assets_en/img_low/sp/quest/scene/character/body/" + id + data[1][0] + ".png";
            className = "preview";
        }
        else
        {
            path = "assets/ui/sound_only.png";
            className = "preview-noborder";
        }
    }
    else return null;
    let onerr = function()
    {
        this.src=this.src.replace("sp/quest/scene/character/body", "sp/raid/navi_face");
        this.onerror = default_onerror;
    };
    return [[id, path, onerr, className, false]];
}

function display_valentines(id, data = null, unusedA = null, unusedB = null)
{
    switch(id.slice(0, 3)) // we hook up to existing functions
    {
        case "304":case "302":case "303": return display_characters(id, index["characters"][id], parseInt(id[2]), null);
        case "399":case "305": return display_npcs(id, index["npcs"][id], parseInt(id.slice(1,3)), [0, 10000]);
        default: return null;
    }
}

function display_story(id, data, unusedA = null, unusedB = null)
{
    if(data[0].length == 0) return null;
    return [["ms"+id, "story", "Chapter " + parseInt(id), null, null]];
}

function display_events(id, data, unusedA = null, unusedB = null)
{
    if(!data) return null;
    let has_file = false;
    let path = "";
    let className = ""
    for(let i = 2; i < data.length; ++i)
    {
        if(data[i].length > 0)
        {
            has_file = true;
            break;
        }
    }
    if(has_file)
    {
        if(index["events"][id][1] == null)
        {
            path = "assets/ui/event.png"
            className = "preview-noborder";
        }
        else
        {
            path = "GBF/assets_en/img_low/sp/archive/assets/island_m2/" + index["events"][id][1] + ".png"
            className = (data[data.length-1].length > 0 ? "preview sky-event":"preview");
        }
    }
    else return null;
    return [["q"+id, path, null, className, false]];
}

function display_skills(id, data, range, unused = null)
{
    if(!data) return null;
    let val = parseInt(id);
    if(val < range[0] || val >= range[1]) return null;
    return [["sk"+id, "GBF/assets_en/img_low/sp/ui/icon/ability/m/" + data[0][0] + ".png", null, "preview", false]];
}

function display_subskills(id, data, unusedA = null, unusedB = null)
{
    return [
        [id+"_1", "GBF/assets_en/img_low/sp/assets/item/ability/s/" + id + "_1.jpg", null, "preview", true],
        [id+"_2", "GBF/assets_en/img_low/sp/assets/item/ability/s/" + id + "_2.jpg", null, "preview", true],
        [id+"_3", "GBF/assets_en/img_low/sp/assets/item/ability/s/" + id + "_3.jpg", null, "preview", true]
    ]
}

function display_buffs(id, data, range, unused = null)
{
    if(!data) return null;
    let val = parseInt(id);
    if(val < range[0] || val >= range[1]) return null;
    return [["b"+id, "GBF/assets_en/img_low/sp/ui/icon/status/x64/status_" + data[0][0] + ".png", null, "preview" + (data[1].length > 0 ? " more" : ""), false]];
}

function display_backgrounds(id, data, key, unused = null)
{
    if(!data) return null;
    let path = null;
    switch(id.split('_')[0])
    {
        case "common":
            if(key != "common") return null;
            path = ["sp/raid/bg/", ".jpg"];
            break;
        case "main":
            if(key != "main") return null;
            path = ["sp/guild/custom/bg/", ".png"];
            break;
        case "event":
            if(key != "event") return null;
            path = ["sp/raid/bg/", ".jpg"];
            break;
        default:
            if(key != "") return null;
            path = ["sp/raid/bg/", ".jpg"];
            break;
    };
    let ret = [];
    for(let i of data[0])
    {
        ret.push([i, "GBF/assets_en/img_low/" + path[0] + i + path[1], null, "preview", true]);
    }
    return ret;
}

function display_titles(id, data, unusedA = null, unusedB = null)
{
    return [[id, "GBF/assets_en/img_low/sp/top/bg/bg_" + id + ".jpg", null, "preview", true]];
}

function display_suptix(id, data, unusedA = null, unusedB = null)
{
    return [[id, "GBF/assets_en/img_low/sp/gacha/campaign/surprise/top_" + id + ".jpg", null, "preview", true]];
}

function addIndexImage(node, path, id, onerr, className, is_link) // add an image to an index. path must start with "GBF/" if it's not a local asset.
{
    if(is_link) // two behavior based on is_link
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
        img.src = path.replace("GBF/", idToEndpoint(id));
        img.title = "Click to open: " + id;
        a.href = img.src.replace("img_low/", "img/");
    }
    else
    {
        let img = document.createElement("img");
        node.appendChild(img);
        img.title = id;
        if(className != "") img.className = className;
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
            this.classList.add("index-image");
            this.onclick = function()
            {
                window.scrollTo(0, 0);
                lookup(id);
            };
        };
        img.src = path.replace("GBF/", idToEndpoint(id));
    }
}

function addTextImage(node, className, id, string, unusedA, unusedB) // like addIndexImage but currently story specific
{
    let elem = document.createElement("div");
    elem.classList.add(className);
    elem.classList.add("preview-noborder");
    elem.classList.add("clickable");
    elem.onclick = function()
    {
        window.scrollTo(0, 0);
        lookup(id);
    };
    elem.title = id;
    elem.appendChild(document.createTextNode(string));
    node.appendChild(elem);
}

// =================================================================================================
// bookmark, history, settings...
function updateList(node, elems) // update a list of elements
{
    node.innerHTML = "";
    for(let e of elems)
    {
        let res = null;
        let image_callback = addIndexImage;
        switch(e[1])
        {
            case 3:
                if(e[0].slice(1, 3) == "71")
                {
                    res = display_skins(e[0], (e[0] in index['skins']) ? index['skins'][e[0]] : null, [0, 1000]);
                }
                else
                {
                    res = display_characters(e[0], (e[0] in index['characters']) ? index['characters'][e[0]] : null, [0, 1000, 0, 1000, 0, 1000]);
                }
                break;
            case 2:
                res = display_summons(e[0], (e[0] in index['summons']) ? index['summons'][e[0]] : null, e[0][2], [0, 1000]);
                break;
            case 1:
                res = display_weapons(e[0], (e[0] in index['weapons']) ? index['weapons'][e[0]] : null, e[0][2], e[0][4]);
                break;
            case 0:
                res = display_mc(e[0], (e[0] in index['job']) ? index['job'][e[0]] : null);
                break;
            case 4:
                res = display_enemies(e[0], (e[0] in index['enemies']) ? index['enemies'][e[0]] : null, e[0][0], e[0][1]);
                break;
            case 5:
                res = display_npcs(e[0], (e[0] in index['npcs']) ? index['npcs'][e[0]] : null, e[0].slice(1, 3), [0, 10000]);
                break;
            case 6:
                res = display_partners(e[0], (e[0] in index['partners']) ? index['partners'][e[0]] : null, e[0].slice(1, 3));
                break;
            case 7:
                res = display_events(e[0], (e[0] in index['events']) ? index['events'][e[0]] : null);
                break;
            case 8:
                res = display_skills(e[0], (e[0] in index['skills']) ? index['skills'][e[0]] : null, [0, 10000]);
                break;
            case 9:
                res = display_buffs(e[0], (e[0] in index['buffs']) ? index['buffs'][e[0]] : null, [0, 10000]);
                break;
            case 10:
                if(e[0] in index['background'])
                {
                    let tmp = e[0].split('_')[0];
                    res = display_backgrounds(e[0], index['background'][e[0]], (["common", "main", "event"].includes(tmp) ? tmp : ""));
                }
                break;
            case 11:
                res = display_story(e[0], (e[0] in index['story']) ? index['story'][e[0]] : null);
                image_callback = addTextImage;
                break;
            case "subskills":
                if(e[0] in index['subskills'])
                {
                    let tmp = e[0].split('_')[0];
                    res = display_subskills(e[0], index['subskills'][e[0]]);
                }
                break;
            case "title":
                if(e[0] in index['title'])
                {
                    let tmp = e[0].split('_')[0];
                    res = display_titles(e[0], index['title'][e[0]]);
                }
                break;
            case "suptix":
                if(e[0] in index['suptix'])
                {
                    let tmp = e[0].split('_')[0];
                    res = display_suptix(e[0], index['suptix'][e[0]]);
                }
                break;
        }
        if(res != null)
        {
            for(let r of res)
            {
                image_callback(node, r[1], r[0], r[2], r[3], r[4]);
            }
        }
    }
}

function loadPreviewSetting() // load home page preview button setting
{
    let tmp = localStorage.getItem("gbfal-previewhome");
    if(tmp != null) previewhome = !!JSON.parse(tmp);
}

function storePreviewSetting() // set home page preview button setting
{
    localStorage.setItem("gbfal-previewhome", JSON.stringify(previewhome));
}

function favButton(state, id = null, search_type = null) // favorite button control
{
    let fav = document.getElementById('fav-btn');
    if(state)
    {
        fav.style.display = null;
        fav.onclick = function() { toggleBookmark(id, search_type); };
        for(let e of bookmarks)
        {
            if(e[0] == id)
            {
                setBookmarkButton(true);
                return;
            }
        }
        setBookmarkButton(false);
    }
    else
    {
        fav.style.display = "none";
        fav.onclick = null;
    }
}

function updateBookmark() // update bookmark list
{
    let node = document.getElementById('bookmark');
    if(bookmarks.length == 0)
    {
        node.innerHTML = "";
        node.appendChild(document.createTextNode("No bookmarked elements."));
        return;
    }
    updateList(node, bookmarks);
    node.appendChild(document.createElement("br"));
    let div = document.createElement("div");
    div.classList.add("std-button-container");
    let btn = document.createElement("button");
    btn.className = "std-button";
    btn.innerHTML = "Clear";
    btn.onclick = clearBookmark;
    div.appendChild(btn);
    btn = document.createElement("button");
    btn.className = "std-button";
    btn.innerHTML = "Export";
    btn.onclick = exportBookmark;
    div.appendChild(btn);
    btn = document.createElement("button");
    btn.className = "std-button";
    btn.innerHTML = "Import";
    btn.onclick = importBookmark;
    div.appendChild(btn);
    node.appendChild(div);
}

function clearBookmark() // clear the bookmark list
{
    localStorage.removeItem('gbfal-bookmark');
    let fav = document.getElementById('fav-btn');
    fav.classList.remove("fav-on");
    fav.innerHTML = "☆";
    bookmarks = [];
    updateBookmark();
}

function exportBookmark() // export the bookmark list to the clipboard
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
        navigator.clipboard.writeText(JSON.stringify(bookmarks));
        pushPopup("Bookmarks have been copied");
    }
    catch(err)
    {
        console.error("Exception thrown", err.stack);
        bookmarks = [];
    }
}

function importBookmark() // import the bookmark list from the clipboard. need localhost or a HTTPS host
{
    navigator.clipboard.readText().then((clipText) => {
        try
        {
            let tmp = JSON.parse(clipText);
            if(typeof tmp != 'object') return;
            let val = false;
            let i = 0;
            let last_id_f = (last_id == null) ? null : (isNaN(last_id) ? last_id : last_id.replaceAll(/\D/g,'')); // strip letters
            while(i < tmp.length)
            {
                let e = tmp[i];
                if(typeof e != 'object' || e.length != 2 || typeof e[0] != 'string' || typeof e[1] != 'number') return;
                if(last_id_f == e[0] && last_type == e[1]) val = true;
                ++i;
            }
            bookmarks = tmp;
            localStorage.setItem("gbfal-bookmark", JSON.stringify(bookmarks));
            setBookmarkButton(val);
            updateBookmark();
            pushPopup("Bookmarks have been imported with success");
        }
        catch(err)
        {
            console.error("Exception thrown", err.stack);
        }
    });
}

function pushPopup(string) // display a popup on the top left corner
{
    let div = document.createElement('div');
    div.className = 'popup';
    div.textContent = string;
    document.body.appendChild(div);
    intervals.push(setInterval(rmPopup, 2500, div));
}

function rmPopup(popup) // remove a popup
{
    popup.parentNode.removeChild(popup);
    clearInterval(intervals[0]);
    intervals.shift();
}

function toggleBookmark(id = null, search_type = null) // toggle bookmark state
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
        let fav = document.getElementById('fav-btn');
        if(!fav.classList.contains("fav-on"))
        {
            bookmarks.push([id, search_type]);
            setBookmarkButton(true);
            pushPopup("" + id + " has been bookmarked.");
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
            setBookmarkButton(false);
            pushPopup("" + id + " has been removed from the bookmarks.");
        }
        localStorage.setItem("gbfal-bookmark", JSON.stringify(bookmarks));
    }
    updateBookmark();
}

function setBookmarkButton(val) // set bookmark button state
{
    let fav = document.getElementById('fav-btn');
    if(val)
    {
        fav.classList.add("fav-on");
        fav.innerHTML = "★";
    }
    else
    {
        fav.classList.remove("fav-on");
        fav.innerHTML = "☆";
    }
}

function clearHistory() // clear the history
{
    localStorage.removeItem('gbfal-history');
    updateHistory();
}

function updateHistory(id = null, search_type = null) // update the history list
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
            if(searchHistory.length > HISTORY_LENGTH) searchHistory = searchHistory.slice(searchHistory.length - HISTORY_LENGTH); // resize if too big to not cause problems
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
        if(searchHistory.length > HISTORY_LENGTH) searchHistory = searchHistory.slice(searchHistory.length - HISTORY_LENGTH);
        localStorage.setItem("gbfal-history", JSON.stringify(searchHistory));
    }
    let node = document.getElementById('history');
    if(searchHistory.length == 0)
    {
        node.innerHTML = "";
        node.appendChild(document.createTextNode("No elements in your history."));
        return;
    }
    updateList(node, searchHistory.slice().reverse());
    node.appendChild(document.createElement("br"));
    let div = document.createElement("div");
    div.classList.add("std-button-container");
    let btn = document.createElement("button");
    btn.innerHTML = "Clear";
    btn.className = "std-button";
    btn.onclick = clearHistory;
    div.appendChild(btn);
    node.appendChild(div);
}

// =================================================================================================
// element lookup
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

function lookup(id) // check element validity and either load it or return search results
{
    try
    {
        let filter = document.getElementById('filter');
        if(filter.value == "" || filter.value != id)
        {
            filter.value = id;
        }
        let target = null;
        switch(id.length)
        {
            case 10:
                if(!isNaN(id))
                {
                    switch(id.slice(0, 3))
                    {
                        case "305": case "399": target = "npcs"; break;
                        case "304": case "303": case "302": target = "characters"; break;
                        case "371": target = "skins"; break;
                        case "384": case "383": case "382": case "388": case "389": target = "partners"; break;
                        case "290": case "204": case "203": case "202": case "201": target = "summons"; break;
                        case "104": case "103": case "102": case "101": target = "weapons"; break;
                    };
                }
                break;
            case 8:
                if(id.toLowerCase()[0] === 'e' && !isNaN(id.slice(1)))
                {
                    target = "enemies";
                    id = id.slice(1);
                }
                break;
            case 7:
                if(id.toLowerCase()[0] === 'q' && !isNaN(id.slice(1)))
                {
                    target = "events";
                    id = id.slice(1);
                }
                break;
            case 6:
                if(id.toLowerCase().startsWith('sk') && !isNaN(id.slice(2)))
                {
                    target = "skills";
                    id = id.slice(2);
                }
                else if(!isNaN(id))
                {
                    target = "job";
                }
                break;
            case 5:
                if(id.toLowerCase()[0] === 'b' && !isNaN(id.slice(1)))
                {
                    target = "buffs";
                    id = id.slice(1);
                }
                else if(id.toLowerCase().slice(0, 2) === 'ms' && !isNaN(id.slice(2)))
                {
                    target = "story";
                    id = id.slice(2);
                }
                break;
        };
        if(target != null && BANNED.includes(id)) return;
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
            searchID = null;
        }
        // remove fav button before loading
        favButton(false);
        // execute
        if(target != null)
        {
            if(id in index[target])
            {
                if(index[target][id] !== 0)
                {
                    loadAssets(id, index[target][id], target);
                }
                else
                {
                    loadDummy(id, target);
                }
            }
            else
            {
                loadDummy(id, target);
            }
        }
        else search(id);
    } catch(err) {
        console.error("Exception thrown", err.stack);
    }
}

function search(id) // generate search results
{
    if(id == "" || id == searchID) return;
    // search
    let words = id.toLowerCase().replace("@@", "").split(' ');
    let positives = [];
    for(const [key, value] of Object.entries(index['lookup_reverse']))
    {
        let matching = true;
        for(const w of words)
        {
            if(w == "")
            {
                continue;
            }
            else if(["ssr", "sr", "r", "female", "male"].includes(w))
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
            positives.push([value, (value.length == 6 ? 0 : (["305", "399"].includes(value.slice(0, 3)) ? 5 : parseInt(value[0])))]);
        }
    }
    // sort (per type (npcs > character > summon > weapon > classes) and per id)
    positives.sort(function(x, y) {
        if (x[1] > y[1]) {
            return -1;
        }
        else if (x[1] < y[1]) {
            return 1;
        }
        if (x[0] < y[0]) {
            return -1;
        }
        else if (x[0] > y[0]) {
            return 1;
        }
        return 0;
    });
    searchResults = positives;
    searchID = id;
    if(searchResults.length > 0)
    {
        let filter = document.getElementById('filter');
        if(filter.value != id) filter.value = id;
    }
    updateSearchResuls();
}

function updateSearchResuls()
{
    if(searchResults.length == 0) return;
    // read
    let searchFilters = localStorage.getItem("gbfal-search");
    if(searchFilters != null)
    {
        try
        {
            searchFilters = JSON.parse(searchFilters);
            while(searchFilters.length < 6) searchFilters.push(true); // retrocompability
        }
        catch(err)
        {
            console.error("Exception thrown", err.stack);
            searchFilters = [true, true, true, true, true, true];
        }
    }
    else searchFilters = [true, true, true, true, true, true];
    // filter results
    let results = [];
    for(let e of searchResults)
    {
        switch(e[1])
        {
            case 0:
                if(searchFilters[5]) // classes
                    results.push(e);
                break;
            case 1:
            case 2: // skins or characters or summons or weapons
            case 3:
                if(searchFilters[e[0].slice(0, 2) == "37" ? 3 : e[1]-1])
                    results.push(e);
                break;
            case 5:
                if(searchFilters[4]) // npcs
                    results.push(e);
                break;
            default:
                continue
        };
        if(results.length >= 50)
            break;
    }
    let node = document.getElementById('results');
    node.style.display = null;
    if(results.length == 0)
    {
        node.innerHTML = "No Results";
    }
    else
    {
        updateList(node, results);
        node.insertBefore(document.createElement("br"), node.firstChild);
        node.insertBefore(document.createTextNode((results.length >= 50) ? "First 50 Results for \"" + searchID + "\"" : "Results for \"" + searchID + "\""), node.firstChild);
    }
    // add checkboxes
    node.appendChild(document.createElement("br"));
    node.appendChild(document.createElement("br"));
    let div = document.createElement("div");
    div.classList.add("std-button-container");
    node.appendChild(div);
    for(const e of [[0, "Weapons"], [1, "Summons"], [2, "Characters"], [3, "Skins"], [4, "NPCs"], [5, "Classes"]])
    {
        let input = document.createElement("input");
        input.type = "checkbox";
        input.classList.add("checkbox");
        input.name = e[1];
        input.onclick = function() {toggleSearchFilter(e[0]);};
        input.checked = searchFilters[e[0]];
        div.appendChild(input);
        let label = document.createElement("label");
        label.classList.add("checkbox-label");
        label.for = e[1];
        label.innerHTML = e[1];
        div.appendChild(label);
    }
    // scroll up if needed
    let filter = document.getElementById('filter');
    var rect = filter.getBoundingClientRect();
    if(
        rect.bottom < 0 ||
        rect.right < 0 ||
        rect.top > (window.innerHeight || document.documentElement.clientHeight) ||
        rect.left > (window.innerWidth || document.documentElement.clientWidth)
    )
    filter.scrollIntoView();
}

function toggleSearchFilter(indice)
{
    // read
    let searchFilters = localStorage.getItem("gbfal-search");
    if(searchFilters != null)
    {
        try
        {
            searchFilters = JSON.parse(searchFilters);
            while(searchFilters.length < 6) searchFilters.push(true); // retrocompability
        }
        catch(err)
        {
            console.error("Exception thrown", err.stack);
            searchFilters = [true, true, true, true, true, true];
        }
    }
    else searchFilters = [true, true, true, true, true, true];
    // toggle
    searchFilters[indice] = !searchFilters[indice];
    // write
    try
    {
        localStorage.setItem("gbfal-search", JSON.stringify(searchFilters));
    }
    catch(err)
    {
        console.error("Exception thrown", err.stack);
    }
    // update
    updateSearchResuls();
}

function loadDummy(id, target)// minimal load of an element not indexed or not fully indexed, this is only intended as a cheap placeholder
{
    data = null;
    switch(target)
    {
        case "weapons":
            data = [[id],["phit_" + id + ".png","phit_" + id + "_1.png","phit_" + id + "_2.png"],["sp_" + id + "_0_a.png","sp_" + id + "_0_b.png","sp_" + id + "_1_a.png","sp_" + id + "_1_b.png"]];
            break;
        case "summons":
            data = [[id,id + "_02"],["summon_" + id + "_01_attack_a.png","summon_" + id + "_01_attack_b.png","summon_" + id + "_01_attack_c.png","summon_" + id + "_01_attack_d.png","summon_" + id + "_02_attack_a.png","summon_" + id + "_02_attack_b.png","summon_" + id + "_02_attack_c.png"],["summon_" + id + "_01_damage.png","summon_" + id + "_02_damage.png"]];
            break;
        case "characters":
            data = [["npc_" + id + "_01.png","npc_" + id + "_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_02"],["" + id + "_01","" + id + "_02"],DUMMY_SCENE,[]];
            break;
        case "skins":
            data = [["npc_" + id + "_01.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_01.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_02"],["" + id + "_01","" + id + "_02"],DUMMY_SCENE,[]];
            break;
        case "partners":
            data = [["npc_" + id + "_01.png","npc_" + id + "_0_01.png","npc_" + id + "_1_01.png","npc_" + id + "_02.png","npc_" + id + "_0_02.png","npc_" + id + "_1_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_01_0","" + id + "_01_1","" + id + "_02","" + id + "_02_0","" + id + "_02_1"]];
            break;
        case "npcs":
            data = [true, DUMMY_SCENE, []];
            break;
        case "enemies":
            data = [[id],["enemy_" + id + "_a.png","enemy_" + id + "_b.png","enemy_" + id + "_c.png"],["raid_appear_" + id + ".png"],["ehit_" + id + ".png"],["esp_" + id + "_01.png","esp_" + id + "_02.png","esp_" + id + "_03.png"],["esp_" + id + "_01_all.png","esp_" + id + "_02_all.png","esp_" + id + "_03_all.png"]];
            break;
        case "job":
            data = [[id],[id + "_01"],[],[],[],[id],[],[],[],[]];
            break;
        case "skills":
            data = [[JSON.stringify(parseInt(id))]];
            break;
        case "buffs":
            data = [[JSON.stringify(parseInt(id))],["_1","_10"]];
            break;
        default:
            break
    }
    if(data != null)
    {
        loadAssets(id, data, target, false);
    }
}

function loadAssets(id, data, target, indexed = true)
{
    endpoint_count = -1;
    let tmp_last_id = last_id;
    let area_name = ""
    let include_link = false;
    let search_type = null;
    let assets = null;
    let skycompass = null;
    let mc_skycompass = false;
    let npcdata = null;
    let files = null;
    let sounds = null;
    let melee = false;
    switch(target)
    {
        case "weapons":
            area_name = "Weapon";
            include_link = true;
            last_id = id;
            search_type = 1;
            assets = [
                ["Main Arts", "sp/assets/weapon/b/", "png", 0, false, true], // index, skycompass, side form
                ["Gacha Arts", "sp/assets/weapon/g/", "png", 0, false, true],
                ["Gacha Covers", "sp/gacha/cjs_cover/", "png", 0, false, true],
                ["Gacha Headers", "sp/gacha/header/", "png", 0, false, true],
                ["Transcendence Headers", "sp/assets/weapon/weapon_evolution/main/", "png", 0, false, true],
                ["Inventory Portraits", "sp/assets/weapon/m/", "jpg", 0, false, true],
                ["Square Portraits", "sp/assets/weapon/s/", "jpg", 0, false, true],
                ["Main Hand Portraits", "sp/assets/weapon/ls/", "jpg", 0, false, true],
                ["Forge Headers", "sp/archaic/", "", -3, false, true],
                ["Forge Portraits", "sp/archaic/", "", -4, false, true],
                ["Battle Sprites", "sp/cjs/", "png", 0, false, true],
                ["Attack Effects", "sp/cjs/", "png", 1, false, true],
                ["Charge Attack Sheets", "sp/cjs/", "png", 2, false, true]
            ];
            melee = (id[4] == "6");
            break;
        case "summons":
            area_name = "Summon";
            include_link = true;
            last_id = id;
            search_type = 2;
            assets = [
                ["Main Arts", "sp/assets/summon/b/", "png", 0, true, true], // index, skycompass, side form
                ["Home Arts", "sp/assets/summon/my/", "png", 0, false, true],
                ["Gacha Art", "sp/assets/summon/g/", "png", 0, false, true],
                ["Gacha Header", "sp/gacha/header/", "png", 0, false, true],
                ["Detail Arts", "sp/assets/summon/detail/", "png", 0, false, true],
                ["Inventory Portraits", "sp/assets/summon/m/", "jpg", 0, false, true],
                ["Square Portraits", "sp/assets/summon/s/", "jpg", 0, false, true],
                ["Main Summon Portraits", "sp/assets/summon/party_main/", "jpg", 0, false, true],
                ["Sub Summon Portraits", "sp/assets/summon/party_sub/", "jpg", 0, false, true],
                ["Raid Portraits", "sp/assets/summon/raid_normal/", "jpg", 0, false, true],
                ["Result Portraits", "sp/assets/summon/btn/", "png", 0, false, true],
                ["Quest Portraits", "sp/assets/summon/qm/", "png", -7, false, true],
                ["Summon Call Sheets", "sp/cjs/", "png", 1, false, true],
                ["Summon Damage Sheets", "sp/cjs/", "png", 2, false, true]
            ];
            skycompass = ["https://media.skycompass.io/assets/archives/summons/", "/detail_l.png", false];
            break;
        case "skins":
        case "characters":
            area_name = target == "characters" ? "Character" : "Skin";
            include_link = true;
            last_id = id;
            search_type = 3;
            assets = [
                ["Main Arts", "sp/assets/npc/zoom/", "png", 5, true, false], // index, skycompass, side form
                ["Home Arts", "sp/assets/npc/my/", "png", 5, false, false],
                ["Journal Arts", "sp/assets/npc/b/", "png", 5, false, false],
                ["Gacha Arts", "sp/assets/npc/gacha/", "png", 6, false, false],
                ["News Art", "sp/banner/notice/update_char_", "png", 6, false, false],
                ["Pose News Arts", "sp/assets/npc/add_pose/", "png", 6, false, false],
                ["Inventory Portraits", "sp/assets/npc/m/", "jpg", 5, false, false],
                ["Square Portraits", "sp/assets/npc/s/", "jpg", 5, false, false],
                ["Party Portraits", "sp/assets/npc/f/", "jpg", 5, false, false],
                ["Popup Portraits", "sp/assets/npc/qm/", "png", 5, false, false],
                ["Result Popup Portraits", "sp/result/popup_char/", "png", -2, false, false],
                ["Balloon Portraits", "sp/gacha/assets/balloon_s/", "png", 6, false, false],
                ["Party Select Portraits", "sp/assets/npc/quest/", "jpg", 5, false, false],
                ["Tower of Babyl Portraits", "sp/assets/npc/t/", "png", 5, false, false],
                ["EMP Up Portraits", "sp/assets/npc/result_lvup/", "png", 5, false, false],
                ["Detail Banners", "sp/assets/npc/detail/", "png", 5, false, false],
                ["Sprites", "sp/assets/npc/sd/", "png", 6, false, false],
                ["Custom Skill Previews", "sp/assets/npc/sd_ability/", "png", -6, false, false],
                ["Raid Portraits", "sp/assets/npc/raid_normal/", "jpg", 5, false, true],
                ["Twitter Arts", "sp/assets/npc/sns/", "jpg", 5, false, false],
                ["Charge Attack Cutins", "sp/assets/npc/cutin_special/", "jpg", 5, false, false],
                ["Chain Cutins", "sp/assets/npc/raid_chain/", "jpg", 5, false, false],
                ["Character Sheets", "sp/cjs/", "png", 0, false, true],
                ["Attack Effect Sheets", "sp/cjs/", "png", 1, false, true],
                ["Charge Attack Sheets", "sp/cjs/", "png", 2, false, true],
                ["AOE Skill Sheets", "sp/cjs/", "png", 3, false, true],
                ["Single Target Skill Sheets", "sp/cjs/", "png", 4, false, true]
            ];
            skycompass = ["https://media.skycompass.io/assets/customizes/characters/1138x1138/", ".png", true];
            npcdata = data[7];
            sounds = data[8];
            break;
        case "partners":
            area_name = "Partner";
            last_id = id;
            search_type = 6;
            assets = [
                ["Party Select Portraits", "sp/assets/npc/quest/", "jpg", 5, false, false],
                ["Raid Portraits", "sp/assets/npc/raid_normal/", "jpg", 5, false, true],
                ["Charge Attack Cutins", "sp/assets/npc/cutin_special/", "jpg", 5, false, false],
                ["Chain Cutins", "sp/assets/npc/raid_chain/", "jpg", 5, false, false],
                ["Character Sheets", "sp/cjs/", "png", 0, false, true],
                ["Attack Effect Sheets", "sp/cjs/", "png", 1, false, true],
                ["Charge Attack Sheets", "sp/cjs/", "png", 2, false, true],
                ["AOE Skill Sheets", "sp/cjs/", "png", 3, false, true],
                ["Single Target Skill Sheets", "sp/cjs/", "png", 4, false, true]
            ];
            break;
        case "npcs":
            area_name = "NPC";
            include_link = data[0] && indexed;
            last_id = id;
            search_type = 5;
            assets = [
                ["Main Arts", "sp/assets/npc/zoom/", "png", -1, false, true], // index, skycompass, side form
                ["Journal Arts", "sp/assets/npc/b/", "png", -1, false, true],
                ["Inventory Portraits", "sp/assets/npc/m/", "jpg", -1, false, true]
            ];
            npcdata = data[1];
            sounds = data[2];
            files = [id, id + "_01"];
            break;
        case "enemies":
            area_name = "Enemy";
            last_id = "e"+id;
            search_type = 4;
            assets = [
                ["Big Icon", "sp/assets/enemy/m/", "png", 0, false, true],
                ["Small Icon", "sp/assets/enemy/s/", "png", 0, false, true],
                ["Sprite Sheets", "sp/cjs/", "png", 1, false, true],
                ["Raid Appear Sheets", "sp/cjs/", "png", 2, false, true],
                ["Attack Effect Sheets", "sp/cjs/", "png", 3, false, true],
                ["Charge Attack Sheets", "sp/cjs/", "png", 4, false, true],
                ["AOE Charge Attack Sheets", "sp/cjs/", "png", 5, false, true]
            ];
            break;
        case "job":
            area_name = "Main Character";
            include_link = true;
            indexed = (data[7].length != 0) && indexed;
            last_id = id;
            search_type = 0;
            assets = [
                ["Job Icons", "sp/ui/icon/job/", "png", 0, false, true], // index, skycompass, side form
                ["Inventory Portraits", "sp/assets/leader/m/", "jpg", 1, false, true],
                ["Outfit Portraits", "sp/assets/leader/sd/m/", "jpg", 1, false, true],
                ["Outfit Description Arts", "sp/assets/leader/skin/", "png", 1, false, true],
                ["Full Arts", "sp/assets/leader/job_change/", "png", 3, true, true],
                ["Home Arts", "sp/assets/leader/my/", "png", 3, false, true],
                ["Outfit Preview Arts", "sp/assets/leader/skin/", "png", 3, false, true],
                ["Class Name Party Texts", "sp/ui/job_name/job_list/", "png", 0, false, true],
                ["Class Name Master Texts", "sp/assets/leader/job_name_ml/", "png", 0, false, true],
                ["Class Name Ultimate Texts", "sp/assets/leader/job_name_pp/", "png", 0, false, true],
                ["Class Change Buttons", "sp/assets/leader/jlon/", "png", 2, false, true],
                ["Party Class Big Portraits", "sp/assets/leader/jobon_z/", "png", 3, false, true],
                ["Square Portraits", "sp/assets/leader/s/", "jpg", 3, false, true],
                ["Party Class Portraits", "sp/assets/leader/p/", "png", 3, false, true],
                ["Profile Portraits", "sp/assets/leader/pm/", "png", 3, false, true],
                ["Profile Board Portraits", "sp/assets/leader/talk/", "png", 3, false, true],
                ["Party Select Portraits", "sp/assets/leader/quest/", "jpg", 3, false, true],
                ["Tower of Babyl Portraits", "sp/assets/leader/t/", "png", 3, false, true],
                ["Raid Portraits", "sp/assets/leader/raid_normal/", "jpg", 3, false, true],
                ["Result Portraits", "sp/assets/leader/btn/", "png", 3, false, true],
                ["Raid Log Portraits", "sp/assets/leader/raid_log/", "png", 3, false, true],
                ["Raid Result Portraits", "sp/assets/leader/result_ml/", "jpg", 3, false, true],
                ["Mastery Portraits", "sp/assets/leader/zenith/", "png", 2, false, true],
                ["Master Level Portraits", "sp/assets/leader/master_level/", "png", 2, false, true],
                ["Sprites", "sp/assets/leader/sd/", "png", 4, false, true],
                ["Custom Skill Previews", "sp/assets/leader/sd_ability/", "png", -5, false, true],
                ["Character Sheets", "sp/cjs/", "png", 7, false, true],
                ["Attack Effects", "sp/cjs/", "png", 8, false, true],
                ["Charge Attack Sheets", "sp/cjs/", "png", 9, false, true]
            ];
            skycompass = ["https://media.skycompass.io/assets/customizes/jobs/1138x1138/", ".png", true];
            mc_skycompass = true;
            break;
        case "story":
            area_name = "Main Story Chapter";
            last_id = "ms"+id;
            search_type = 11;
            assets = [
                ["Arts", "sp/quest/scene/character/body/", "png", 0, false, true]
            ];
            break;
        case "events":
            area_name = "Event";
            last_id = "q"+id;
            search_type = 7;
            assets = [
                ["Sky Compass", "", "", 20, true, false],
                ["Opening Arts", "sp/quest/scene/character/body/", "png", 2, false, true],
                ["Chapter 1 Arts", "sp/quest/scene/character/body/", "png", 5, false, true],
                ["Chapter 2 Arts", "sp/quest/scene/character/body/", "png", 6, false, true],
                ["Chapter 3 Arts", "sp/quest/scene/character/body/", "png", 7, false, true],
                ["Chapter 4 Arts", "sp/quest/scene/character/body/", "png", 8, false, true],
                ["Chapter 5 Arts", "sp/quest/scene/character/body/", "png", 9, false, true],
                ["Chapter 6 Arts", "sp/quest/scene/character/body/", "png", 10, false, true],
                ["Chapter 7 Arts", "sp/quest/scene/character/body/", "png", 11, false, true],
                ["Chapter 8 Arts", "sp/quest/scene/character/body/", "png", 12, false, true],
                ["Chapter 9 Arts", "sp/quest/scene/character/body/", "png", 13, false, true],
                ["Chapter 10 Arts", "sp/quest/scene/character/body/", "png", 14, false, true],
                ["Chapter 11 Arts", "sp/quest/scene/character/body/", "png", 15, false, true],
                ["Chapter 12 Arts", "sp/quest/scene/character/body/", "png", 16, false, true],
                ["Chapter 13 Arts", "sp/quest/scene/character/body/", "png", 17, false, true],
                ["Chapter 14 Arts", "sp/quest/scene/character/body/", "png", 18, false, true],
                ["Chapter 15 Arts", "sp/quest/scene/character/body/", "png", 19, false, true],
                ["Ending Arts", "sp/quest/scene/character/body/", "png", 3, false, true],
                ["Arts", "sp/quest/scene/character/body/", "png", 4, false, true]
            ];
            skycompass = ["https://media.skycompass.io/assets/archives/events/"+data[1]+"/image/", "_free.png", true];
            break;
        case "skills":
            area_name = "Skill";
            last_id = "sk"+id;
            search_type = 8;
            assets = [
                ["Skill Icons", "sp/ui/icon/ability/m/", "png", -1, false, true]
            ];
            files = [""+parseInt(id), ""+parseInt(id)+"_1", ""+parseInt(id)+"_2", ""+parseInt(id)+"_3", ""+parseInt(id)+"_4", ""+parseInt(id)+"_5"];
            break;
        case "buffs":
            area_name = "Buff";
            last_id = "b"+id;
            search_type = 9;
            assets = [
                ["Icons", "sp/ui/icon/status/x64/status_", "png", 0, false, true]
            ];
            let tmp = getBuffSets(id, data, assets);
            data = tmp[0];
            assets = tmp[1];
            break;
        default:
            return;
    };
    updateQuery(last_id);
    if(id == tmp_last_id && last_type == search_type) return; // quit if already loaded
    last_type = search_type;
    if(indexed)
    {
        updateHistory(id, search_type);
        favButton(true, id, search_type);
    }
    prepareOuputAndHeader(area_name, id, data, include_link, indexed);
    if(assets != null)
    {
        for(let asset of assets)
        {
            // special exceptions
            switch(asset[3])
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
                case -5: // custom MC skin skills
                    files = [id+"_0_attack", id+"_1_attack"];
                    for(let i = 1; i < 5; ++i)
                        for(let j = 0; j < 2; ++j)
                            files.push(id+"_"+j+"_vs_motion_"+i);
                    break;
                case -6: // custom character skin skills
                    files = [id+"_01_attack"];
                    for(let i = 1; i < 5; ++i)
                        files.push(id+"_01_vs_motion_"+i);
                    break;
                case -7: // custom summon quest portraits
                    files = [id, id+"_hard", id+"_hard_plus", id+"_ex", id+"_ex_plus", id+"_high", id+"_high_plus"]; 
                    break;
                default:
                    files = data[asset[3]];
                    break;
            }
            if(files.length == 0) continue; // empty list
            let is_home = false;
            // exceptions
            switch(asset[0])
            {
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
            // add section
            let div = addResult(asset[0], asset[0]);
            // get file count
            let file_count = indexed ? files.length : 0;
            // add mypage preview
            if(is_home)
            {
                let img = document.createElement("img");
                img.src = "assets/ui/mypage.png";
                img.classList.add("clickable");
                img.classList.add("mypage-btn");
                img.onclick = togglePreview;
                div.appendChild(img);
            }
            // for each file
            for(let i = 0; i < files.length; ++i)
            {
                let file = files[i];
                // hide files if too many
                if(file_count > HIDE_DISPLAY && i == DISPLAY_MINI)
                    div = hideNextFiles(div, file_count - DISPLAY_MINI);
                if(asset[0] != "Sky Compass") // event sky compass exception
                {
                    if(!addImage(div, file, asset, is_home))
                        continue;
                }
                if(skycompass != null && asset[4]) // skycompass
                {
                    addImageSkycompass(div, file, id, data, asset, skycompass, mc_skycompass);
                }
            }
        }
    }
    if(npcdata != null) // indexed npc data
    {
        assets = [
            ["Raid Bubble Arts", "sp/raid/navi_face/", "png"],
            ["Scene Arts", "sp/quest/scene/character/body/", "png"]
        ];
        let file_count = indexed ? npcdata.length : 0;
        for(let asset of assets)
        {
            if(npcdata.length == 0) continue;
            let div = addResult(asset[0], asset[0], ((indexed && asset[0] == "Scene Arts") ? npcdata.length : 0));
            for(let i = 0; i < npcdata.length; ++i)
            {
                let file = npcdata[i];
                if(asset[0] == "Scene Arts" && file_count > HIDE_DISPLAY && i == 8)
                    div = hideNextFiles(div, file_count - 8);
                if(asset[0] == "Raid Bubble Arts" && NO_BUBBLE_FILTER.includes(file.split("_").slice(-1)[0])) continue; // ignore those
                addImageScene(div, file, id, asset);
            }
        }
    }
    if(sounds != null && sounds.length > 0) // indexed sounds data for characters
    {
        let sorted_sound = {"Generic":[]}
        let checks = {
            "": "Generic",
            "_boss_v_": "Boss",
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
        if("Boss" in sorted_sound) sorted_sound["Boss"].sort(customSortBoss);
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
                    addSound(div, id, sound);
                }
            }
        }
    }
}

function prepareOuputAndHeader(name, id, data, include_link, indexed=true) // prepare the output element by cleaning it up and create its header
{
    // open tab
    openTab("view");
    // cleanup output
    while(true)
    {
        let child = output.lastElementChild;
        if(!child) break;
        output.removeChild(child);
    }
    // create header
    let div = (name == "Event") ? addResult("Result Header", name + ": " + id + " (20"+id.substr(0,2)+"/"+id.substr(2,2)+"/"+id.substr(4,2)+")") : addResult("Result Header", name + ": " + id);
    // include wiki link
    if(include_link)
    {
        let l = document.createElement('a');
        try
        {
            if(id in index["lookup"] && index["lookup"][id].includes("@@"))
                l.setAttribute('href', "https://gbf.wiki/" + index["lookup"][id].split("@@")[1].split(" ")[0]);
            else
                l.setAttribute('href', "https://gbf.wiki/index.php?title=Special:Search&search=" + id);
        } catch(err) {
            l.setAttribute('href', "https://gbf.wiki/index.php?title=Special:Search&search=" + id);
        }
        l.title = "Wiki search for " + id;
        let img = document.createElement('img');
        img.src = "assets/ui/icon/wiki.png";
        img.classList.add("img-link");
        l.appendChild(img);
        div.appendChild(l);
    }
    let did_lookup = false;
    // include GBFAP link if element is compatible
    if((id.length == 10 && ["302", "303", "304", "371", "101", "102", "103", "104", "201", "202", "203", "204", "290"].includes(id.slice(0, 3))) || (id.length == 6 && name == "Main Character") || (id.length == 7 && name == "Enemy"))
    {
        let uncaps = [""];
        if(["101", "102", "103", "104"].includes(id.slice(0, 3))) // get weapon uncaps to add additional links
        {
            for(let e of data[0])
                if(e != id)
                    uncaps.push(e.replace(id, ""));
        }
        for(let u of uncaps)
        {
            l = document.createElement('a');
            l.setAttribute('href', "https://mizagbf.github.io/GBFAP/?id=" + id + u);
            l.title = "Animations of " + id + u;
            let img = document.createElement('img');
            img.src = "assets/ui/icon/GBFAP.png";
            img.classList.add("img-link");
            l.appendChild(img);
            div.appendChild(l);
        }
        did_lookup = true;
    }
    // add tags if they exist
    if(id in index["lookup"] && index["lookup"][id].split(' ').length > 1)
    {
        div.appendChild(document.createElement('br'));
        let i = document.createElement('i');
        i.appendChild(document.createTextNode("Search Tags: "));
        div.appendChild(i);
        for(let t of index["lookup"][id].split(' '))
        {
            if(t.substr(0, 2) == "@@") continue;
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
    // add non indexed warning if it's not indexed
    if(!indexed)
    {
        div.appendChild(document.createElement('br'));
        div.appendChild(document.createTextNode("This element isn't indexed, assets will be missing"));
    }
    // add related partner for character
    else if(name == "Character")
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
            updateList(i, [[cid, 6]]);
        }
    }
    // add related character for partner
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
            updateList(i, [[cid, 3]]);
        }
    }
    // add event thumbnail
    else if(name == "Event") // event
    {
        if("events" in index && id in index["events"] && index["events"][id][1] != null)
        {
            let img = document.createElement("img")
            img.src = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/archive/assets/island_m2/"+index["events"][id][1]+".png"
            div.appendChild(img);
        }
    }
    // scroll to output
    div.scrollIntoView();
}

function addResult(identifier, name) // add an asset category
{
    let div = document.createElement("div");
    div.classList.add("container");
    if(identifier == "Result Header") div.classList.add("container-header");
    div.setAttribute("data-id", identifier);
    div.appendChild(document.createTextNode(name));
    div.appendChild(document.createElement("br"));
    output.appendChild(div);
    return div;
}

function addVoiceResult(identifier, name, file_count) // add a voice category
{
    let div = document.createElement("div");
    div.classList.add("result");
    div.setAttribute("data-id", identifier);
    div.appendChild(document.createTextNode(name));
    div.appendChild(document.createElement("br"));
    let details = document.createElement("details");
    let summary = document.createElement("summary");
    summary.classList.add("element-detail");
    summary.classList.add("sub-detail");
    summary.innerHTML = file_count + " Files";
    details.appendChild(summary);
    div.appendChild(details);
    output.appendChild(div);
    return details;
}

function hideNextFiles(div, file_count) // used to hide files when too many of them are present
{
    let details = document.createElement("details");
    let summary = document.createElement("summary");
    summary.classList.add("element-detail");
    summary.classList.add("sub-detail");
    summary.innerHTML = "Try to load " + file_count + " more files";
    details.appendChild(summary);
    div.appendChild(details);
    output.appendChild(div);
    return details;
}

function addImage(div, file, asset, is_home) // add an asset
{
    if(!asset[5] && (file.endsWith('_f') || file.endsWith('_f1'))) return false;
    let img = document.createElement("img");
    let ref = document.createElement('a');
    if(file.endsWith(".png") || file.endsWith(".jpg")) // if extension is already set
        img.src = cycleEndpoint() + "assets_en/img_low/" + asset[1] + file;
    else
        img.src = cycleEndpoint() + "assets_en/img_low/" + asset[1] + file + "." + asset[2];
    ref.setAttribute('href', img.src.replace("img_low", "img").replace("img_mid", "img")); // set link
    img.classList.add("loading");
    if(is_home) img.classList.add("homepage"); // use this for mypage previews
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
        if(this.classList.contains("homepage") && previewhome) // toggle state of previewhome is true
        {
            this.classList.remove("homepage");
            this.classList.add("homepage-bg");
            this.src = this.src.replace('/img_low/', '/img/');
            this.parentNode.classList.add("homepage-ui");
        }
        else this.classList.add("asset");
        this.onload = null;
    };
    div.appendChild(ref);
    ref.appendChild(img);
    return true;
}

function addImageScene(div, file, id, asset) // add a npc/scene asset
{
    let img = document.createElement("img");
    let ref = document.createElement('a');
    img.src = cycleEndpoint() + "assets_en/img_low/" + asset[1] + id + file + "." + asset[2];
    if(file != "") img.title = file.replaceAll('_', ' ').trim();
    ref.setAttribute('href', img.src.replaceAll("img_low", "img"));
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

function addImageSkycompass(div, file, id, data, asset, skycompass, mc_skycompass) // add a skycompass asset
{
    let img = document.createElement("img");
    img.setAttribute('loading', 'lazy');
    let ref = document.createElement('a');
    if(!skycompass[2]) // if false, use first file string and no uncap suffix
    {
        if(file != data[asset[3]][0]) return false;
        ref.setAttribute('href', skycompass[0] + file.split('_')[0] + skycompass[1]);
        img.src = skycompass[0] + file.split('_')[0] + skycompass[1];
    }
    else if(mc_skycompass) // for classes only
    {
        ref.setAttribute('href', skycompass[0] + id + '_' + file.split('_')[2] + skycompass[1]);
        img.src = skycompass[0] + id + '_' + file.split('_')[2] + skycompass[1];
    }
    else // standard stuff
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
    return true;
}

function addSound(div, id, sound) // add a sound asset
{
    let elem = document.createElement("div");
    elem.classList.add("sound-file");
    elem.classList.add("clickable");
    elem.title = "Click to play " + id + sound + ".mp3";
    // format element text
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
    // onclick play the audio
    elem.onclick = function() {
        if(audio != null) audio.pause(); // stop existing audio
        audio = new Audio("https://prd-game-a5-granbluefantasy.akamaized.net/assets_en/sound/voice/" + id + sound + ".mp3");
        audio.play();
    };
    // add link
    let a = document.createElement("a");
    a.href = "https://prd-game-a5-granbluefantasy.akamaized.net/assets_en/sound/voice/" + id + sound + ".mp3";
    a.classList.add("sound-link");
    a.onclick = function(event) {
        event.stopPropagation();
    };
    a.title = "Click to open the link";
    elem.appendChild(a);
    div.appendChild(elem);
}

function getBuffSets(id, data, assets) // MESS WARNING!! buffs are a pain to deal with, this is the best I can do for now
{
    let iid = parseInt(id);
    let tmp = data[0][0];
    let variations = data[1];
    data = [[]];
    if(!tmp.includes("_"))
        data[0].push(""+parseInt(id));
    let v1 = variations.includes("1");
    let vu1 = variations.includes("_1");
    let vu10 = variations.includes("_10");
    let vu11 = variations.includes("_11");
    let vu101 = variations.includes("_101");
    let vu110 = variations.includes("_110");
    let vu111 = variations.includes("_111");
    let vu30 = variations.includes("_30");
    let vu1u1 = variations.includes("_1_1");
    let vu2u1 = variations.includes("_2_1");
    let vu0u10 = variations.includes("_0_10");
    let vu1u10 = variations.includes("_1_10");
    let vu1u20 = variations.includes("_1_20");
    let vu2u10 = variations.includes("_2_10");
    if(vu1 && vu10)
    {
        for(let i = 0; i < 31; ++i)
            data[data.length-1].push(""+iid+"_"+i);
    }
    else if(vu1)
    {
        for(let i = 0; i < 10; ++i)
            data[data.length-1].push(""+iid+"_"+i);
    }
    if(v1) // weird exception for satyr and siete (among maybe others)
    {
        for(let i = 0; i < 21; ++i)
            data[data.length-1].push(""+iid+""+i);
    }
    if(vu10 && vu30)
    {
        for(let i = 10; i < 100; ++i)
            data[data.length-1].push(""+iid+"_"+i);
    }
    else if(!vu10)
    {
        if(vu11)
        {
            if(vu111)
            {
                for(let i = 0; i < 200; ++i)
                    data[data.length-1].push(""+iid+"_"+i);
            }
            else if(vu110)
            {
                for(let i = 0; i < 21; ++i)
                    data[data.length-1].push(""+iid+"_1"+i);
            }
            else
            {
                for(let i = 10; i < 111; ++i)
                    data[data.length-1].push(""+iid+"_"+i);
            }
        }
        else if(vu101)
        {
            for(let i = 1; i < 21; ++i)
                data[data.length-1].push(""+iid+"_1"+JSON.stringify(i).padStart(2, '0'));
        }
    }
    if(vu0u10 && !vu1u10)
    {
        for(let i = 10; i < 101; ++i)
        {
            data[data.length-1].push(""+iid+"_0_"+i);
        }
    }
    // elem stuff
    let lim = 0
    if(vu1u20) lim = 101;
    else if(vu1u10 || vu2u10) lim = 21;
    else if(vu1u1 || vu2u1) lim = 11;
    for(let i = 0; i < 9; ++i)
    {
        for(let j = 0; j < lim; ++j)
        {
            data[data.length-1].push(""+iid+"_"+i+"_"+j);
        }
    }
    return [data, assets];
}