/*jshint esversion: 11 */

// =================================================================================================
var items = {};
var lists = [[], [], []];
var sizes = [null, null, null];
const NPC = 0;
const MOON = 1;
const STONE = 2;
const COUNT = 3;
const HEIGHT = 50;
const DEFAULT_SIZE = [140, 80];
var resizeTimer = null;

// =================================================================================================
// initialization
function init_spark() // entry point, called by body onload
{
    getJSON("json/changelog.json?" + timestamp, initChangelog_spark); // load changelog
    beep(); // to preload Audio
}

function openSparkTab(tabName) // reset and then select a tab
{
    for(let btn of document.getElementsByClassName("spark-tab"))
    {
        if(btn.classList.contains("active"))
            btn.classList.remove("active");
    }
    for(let sel of document.getElementsByClassName("spark-select"))
        sel.style.display = "none";
    document.getElementById("spark-select-" + tabName).style.display = "";
    document.getElementById("spark-tab-btn-"+tabName).classList.add("active");
}

function initChangelog_spark() // load content of changelog.json
{
    try
    {
        let json = JSON.parse(this.response);
        if(json.hasOwnProperty("new")) // set updated
            updated = json["new"].reverse();
        timestamp = json.timestamp; // set timestamp
        clock(); // start the clock
        if(json.hasOwnProperty("stat")) stat_string = json["stat"];
        if(json.hasOwnProperty("issues")) // read issues, if any
        {
            let issues = json["issues"];
            if(issues.length > 0)
            {
                let el = document.getElementById("issues");
                el.innerHTML += "<ul>";
                for(let i = 0; i < issues.length; ++i) el.innerHTML += "<li>"+issues[i]+"</li>\n";
                el.innerHTML += "</ul>";
                el.style.display = null;
            }
        }
        if(HELP_FORM != null && json.hasOwnProperty("help")) // read issues, if any
        {
            if(json["help"])
            {
                const d = document.getElementById("notice");
                d.style.display = null;
                d.innerHTML = 'Looking for help to find the name of those <a href="?id=missing-help-wanted">elements</a>.<br>Contact me or use this <a href="' + HELP_FORM + '">form</a> to submit a name.';
            }
        }
    }
    catch(err)
    {
        console.error("Exception thrown", err.stack);
    }
    getJSON("json/data.json?" + timestamp, initData_spark); // load data.json next
}

function initData_spark() // load data.json
{
    try
    {
        index = JSON.parse(this.response); // read
        index["lookup_reverse"] = {} // create reversed lookup for search
        for(const [key, value] of Object.entries(index['lookup']))
        {
            if(!(value in index["lookup_reverse"])) index["lookup_reverse"][value] = [];
            index["lookup_reverse"][value].push(key);
        }
        setSparkList();
        loadSpark();
        loadSetting();
        audioMuted = false;
        document.getElementById("spark-container").scrollIntoView();
    }
    catch(err)
    {
        console.error("Exception thrown", err.stack);
        // put a message if GBFAL is broken
        let el = document.getElementById("issues");
        el.innerHTML = '<p>A critical error occured, please report the issue if it persists.<br>You can also try to clear your cache or do a CTRL+F5.<br><a href="https://mizagbf.github.io/">Home Page</a><br><a href="https://github.com/MizaGBF/GBFAL/issues">Github</a></p>';
        el.style.display = null;
    }
}

function setSparkList()
{
    let node = document.getElementById('spark-select-npc');
    node.innerHTML = "";
    let results = []
    const ckeys = Object.keys(index["characters"]).reverse();
    for(const id of ckeys)
    {
        if(id in index["lookup"] && !(id in index["premium"])) continue; // exclude non gacha characters (unless not in lookup = it's recent)
        const ret = display_characters(id, (index["characters"][id] !== 0 ? index["characters"][id] : null), [-1, -1, -1, -1, 0, 1000]);
        if(ret != null)
        {
            items[id] = addImage_spark(node, ret[0][1], ret[0][0], ret[0][2]);
        }
    }
    node = document.getElementById('spark-select-summon');
    const skeys = Object.keys(index["summons"]).reverse();
    for(const id of skeys)
    {
        if(id in index["lookup"] && !(id in index["premium"])) continue; // exclude non gacha summons (unless not in lookup = it's recent)
        const ret = display_summons(id, (index["summons"][id] !== 0 ? index["summons"][id] : null), "4", [0, 1000]);
        if(ret != null)
        {
            items[id] = addImage_spark(node, ret[0][1], ret[0][0], ret[0][2]);
        }
    }
}

function addImage_spark(node, path, id, onerr) // add an image to an index. path must start with "GBF/" if it's not a local asset.
{
    let img = document.createElement("img");
    node.appendChild(img);
    img.title = id;
    img.classList.add("loading");
    img.classList.add("spark-image");
    img.setAttribute('loading', 'lazy');
    if(true || onerr == null)
    {
        img.onerror = function() {
            this.remove();
        };
    }
    else img.onerror = onerr;
    const isSummon = id.startsWith("20");
    const cid = id;
    img.onload = function() {
        this.classList.remove("loading");
        this.classList.add("clickable");
        this.onclick = function()
        {
            beep();
            if(!isSummon && (window.event.shiftKey || document.getElementById("moon-check").classList.contains("active")))
            {
                addImageResult_spark(MOON, id, this.src);
            }
            else
            {
                addImageResult_spark(isSummon ? STONE : NPC, id, this.src);
            }
            document.getElementById("spark-container").scrollIntoView();
            saveSpark();
        };
    };
    img.src = path.replace("GBF/", idToEndpoint(id));
    return img;
}

function addImageResult_spark(mode, id, path)
{
    let node;
    switch(mode)
    {
        case NPC: node = document.getElementById("spark-npc"); break;
        case MOON: node = document.getElementById("spark-moon"); break;
        case STONE: node = document.getElementById("spark-summon"); break;
        default: return;
    }
    let div = document.createElement("div");
    div.classList.add("spark-result");
    const cmode = mode;
    div.onclick = function()
    {
        beep();
        if(window.event.shiftKey || document.getElementById("spark-check").classList.contains("active"))
        {
            toggle_spark_state(div);
            saveSpark();
        }
        else
        {
            for(let i = 0; i < lists[cmode].length; ++i)
            {
                if(this === lists[cmode][i][1])
                {
                    lists[cmode].splice(i, 1);
                }
            }
            this.remove();
            update_node(cmode, false);
            saveSpark();
        }
    };
    let img = document.createElement("img");
    img.classList.add("spark-result-img");
    img.src = path;
    div.appendChild(img);
    node.appendChild(div);
    lists[mode].push([id, div]);
    update_node(mode, true);
    return div;
}

function toggle_spark_state(div)
{
    if(div.childNodes.length == 2) remove_spark(div);
    else if(div.childNodes.length == 1) add_spark(div);
}

function add_spark(div)
{
    if(div.childNodes.length == 2) return;
    let img = document.createElement("img");
    img.classList.add("spark-icon");
    img.src = "assets/spark/spark.png";
    div.appendChild(img);
}

function remove_spark(div)
{
    if(div.childNodes.length != 2) return;
    div.removeChild(div.childNodes[1]);
}

addEventListener("resize", (event) => {
    if(resizeTimer != null) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(update_all, 300);
});

function update_all()
{
    clearTimeout(resizeTimer);
    resizeTimer = null;
    update_node(NPC, false);
    update_node(MOON, false);
    update_node(STONE, false);
}

function update_node(mode, addition)
{
    let node;
    switch(mode)
    {
        case NPC: node = document.getElementById("spark-npc"); break;
        case MOON: node = document.getElementById("spark-moon"); break;
        case STONE: node = document.getElementById("spark-summon"); break;
        default: return;
    }
    updateRate();
    if(node.childNodes.length == 0) return;
    const nw = node.offsetWidth - 5;
    const nh = node.offsetHeight - 5;
    let current_size;
    const is_mobile = isOnMobile();
    if(addition)
    {
        current_size = sizes[mode];
    }
    
    {
        current_size = DEFAULT_SIZE;
        if(is_mobile)
        {
            current_size[0] *= 2;
            current_size[1] *= 2;
        }
        sizes[mode] = null;
    }
    let changed = false;
    while(true)
    {
        const cw = Math.floor(nw/current_size[0]);
        const ch = Math.floor(nh/current_size[1]) - 1;
        if(node.childNodes.length <= cw*ch)
        {
            break;
        }
        sizes[mode] = [current_size[0]*0.9, current_size[1]*0.9];
        current_size = sizes[mode];
        changed = true;
    }
    if(changed)
    {
        for(let i = 0; i < node.childNodes.length; ++i)
        {
            if(sizes[mode] == null)
            {
                node.childNodes[i].style.minWidth = null;
                node.childNodes[i].style.minHeight = null;
                node.childNodes[i].style.maxWidth = null;
                node.childNodes[i].style.maxHeight = null;
            }
            else
            {
                node.childNodes[i].style.minWidth = "" + Math.max(1, sizes[mode][0]) + "px";
                node.childNodes[i].style.minHeight = "" + Math.max(1, sizes[mode][1]) + "px";
                node.childNodes[i].style.maxWidth = "" + Math.max(1, sizes[mode][0]) + "px";
                node.childNodes[i].style.maxHeight = "" + Math.max(1, sizes[mode][1]) + "px";
            }
        }
    }
}

function updateRate()
{
    let v;
    try
    {
        v = parseInt(document.getElementById("spark-roll-input").value);
        if(isNaN(v) || v <= 0) return;
        let c = lists[NPC].length + lists[MOON].length + lists[STONE].length;
        if(v < c) v = c;
        document.getElementById("spark-rate").innerHTML = "" + c + " / " + v + "<br>" + (Math.round(c / v * 1000) / 10) + "% SSR";
    }
    catch(err)
    {
        console.error("Exception thrown", err.stack);
        return;
    }
}

function spark_clear()
{
    localStorage.removeItem('gbfal-spark');
    lists = [[], [], []];
    for(let i = 0; i < COUNT; ++i)
    {
        let node;
        switch(i)
        {
            case NPC: node = document.getElementById("spark-npc"); break;
            case MOON: node = document.getElementById("spark-moon"); break;
            case STONE: node = document.getElementById("spark-summon"); break;
            default: continue;
        }
        node.innerHTML = "";
    }
    update_all();
    updateRate();
}

function saveSpark()
{
    let tmp = [[], [], [], document.getElementById("spark-roll-input").value];
    for(let i = 0; i < COUNT; ++i)
    {
        for(let j = 0; j < lists[i].length; ++j)
        {
            tmp[i].push([lists[i][j][0], lists[i][j][1].childNodes.length == 2]);
        }
    }
    localStorage.setItem("gbfal-spark", JSON.stringify(tmp));
}

function loadSpark()
{
    try
    {
        let tmp = localStorage.getItem("gbfal-spark");
        if(tmp == null)
        {
            tmp = [[], [], [], 300];
        }
        else
        {
            tmp = JSON.parse(tmp);
        }
        if(tmp[COUNT] != undefined)
            document.getElementById("spark-roll-input").value = tmp[COUNT];
        lists = [[], [], []];
        for(let i = 0; i < COUNT; ++i)
        {
            let node;
            switch(i)
            {
                case NPC: node = document.getElementById("spark-npc"); break;
                case MOON: node = document.getElementById("spark-moon"); break;
                case STONE: node = document.getElementById("spark-summon"); break;
                default: continue;
            }
            for(let j = 0; j < tmp[i].length; ++j)
            {
                if(tmp[i][j][0] in items)
                {
                    let div = addImageResult_spark(i, tmp[i][j][0], items[tmp[i][j][0]].src);
                    if(tmp[i][j][1])
                        add_spark(div);
                }
            }
        }
        updateRate();
    }
    catch(err)
    {
        console.error("Exception thrown", err.stack);
    }
}

function saveSetting()
{
    let tmp = [document.getElementById("moon-check").classList.contains("active"), document.getElementById("spark-check").classList.contains("active")];
    localStorage.setItem("gbfal-spark-settings", JSON.stringify(tmp));
}

function loadSetting()
{
    try
    {
        let tmp = localStorage.getItem("gbfal-spark-settings");
        if(tmp == null) return;
        tmp = JSON.parse(tmp);
        if(tmp[0]) document.getElementById("moon-check").classList.add("active");
        if(tmp[1]) document.getElementById("spark-check").classList.add("active");
    }
    catch(err)
    {
        console.error("Exception thrown", err.stack);
    }
}

function spark_filter()
{
    clearTimeout(typingTimer);
    typingTimer = setTimeout(function(){
        filter(document.getElementById('spark-filter').value.trim().toLowerCase());
    }, 1000);
}

function filter(content)
{
    if(content == "")
    {
        for(let k in items)
        {
            items[k].style.display = null;
        }
    }
    else
    {
        for(let k in items)
        {
            items[k].style.display = "none";
        }
        search(content, 1);
        for(let i = 0; i < searchResults.length; ++i)
        {
            if(searchResults[i][1] == 2 || searchResults[i][1] == 3) // only chara and summon
            {
                if(searchResults[i][0] in items)
                    items[searchResults[i][0]].style.display = null;
            }
            else if(searchResults[i][1] == 1 && searchResults[i][0] in index["premium"])
            {
                const id = index["premium"][searchResults[i][0]];
                if(id in items)
                    items[id].style.display = null;
            }
        }
    }
}

function toggle_moon()
{
    if(document.getElementById("moon-check").classList.contains("active"))
        document.getElementById("moon-check").classList.remove("active");
    else
        document.getElementById("moon-check").classList.add("active");
    saveSetting();
}

function toggle_spark()
{
    if(document.getElementById("spark-check").classList.contains("active"))
        document.getElementById("spark-check").classList.remove("active");
    else
        document.getElementById("spark-check").classList.add("active");
    saveSetting();
}