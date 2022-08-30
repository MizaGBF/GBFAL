

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
function getEndpoint()
{
    var e = endpoints[counter];
    counter = (counter + 1) % endpoints.length;
    return e;
}

function init()
{
    var params = new URLSearchParams(window.location.search);
    var id = params.get("id");
    if(id != null)
        window.location.replace("search.html?id=" + id);
}

function addImage(node, path, id)
{
    var img = document.createElement("img");
    var ref = document.createElement('a');
    ref.setAttribute('href', "search.html?id=" + id);
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
    var node = document.getElementById('areacharacters');  
    for(let id of characters)
    {
        var el = id.split("_");
        if(el.length == 2)
            addImage(node, "sp/assets/npc/m/" + el[0] + "_01_" + el[1] + ".jpg", id);
        else
            addImage(node, "sp/assets/npc/m/" + id + "_01.jpg", id);
    }
}

function displaySummons(elem)
{
    elem.removeAttribute("onclick");
    var node = document.getElementById('areasummons');  
    for(let id of summons)
    {
        addImage(node, "sp/assets/summon/m/" + id + ".jpg", id);
    }
}

function displayWeapons(elem)
{
    elem.removeAttribute("onclick");
    var node = document.getElementById('areaweapons');  
    for(let id of weapons)
    {
        addImage(node, "sp/assets/weapon/m/" + id + ".jpg", id);
    }
}

function displaySkins(elem)
{
    elem.removeAttribute("onclick");
    var node = document.getElementById('areaskins');  
    for(let id of skins)
    {
        addImage(node, "sp/assets/npc/m/" + id + "_01.jpg", id);
    }
}

function displayEnemies(elem)
{
    elem.removeAttribute("onclick");
    var node = document.getElementById('areaenemies');  
    for(let id of enemies)
    {
        addImage(node, "sp/assets/enemy/m/" + id + ".png", "e" + id);
    }
}