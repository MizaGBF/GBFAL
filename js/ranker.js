/*jshint esversion: 11 */

var gbf = null;
var search = null; // unused
var timestamp = Date.now();
var index = null;
var output = null;

var pools = {};
var checkboxes = {};
var game_data = null;
var ui_elements = {};

const options = {
	Rarity:{
		r:"R",
		sr:"SR",
		ssr:"SSR"
	},
	Element:{
		fire:"Fire",
		water:"Water",
		earth:"Earth",
		wind:"Wind",
		light:"Light",
		dark:"Dark",
		any:"Null"
	},
	Gender:{
		male:"Male",
		female:"Female",
		other:"Other"
	},
	Race:{
		human:"Human",
		erune:"Erune",
		draph:"Draph",
		harvin:"Harvin",
		primal:"Primal",
		unknown:"Unknown"
	},
	Series:{
		none:"None",
		grand:"Grand",
		summer:"Summer",
		yukata:"Yukata",
		valentine:"Valentine",
		halloween:"Halloween",
		holiday:"Holiday",
		formal:"Formal",
		"12generals":"12 Generals",
		fantasy:"Fantasy",
		collab:"Collab",
		eternals:"Eternals",
		evokers:"Evokers",
		"4saints":"4 Saints"
	},
	"Release Order":{
		original:"First Version",
		dupe:"Alternate Versions"
	},
	Others:{
		single:"Single Units",
		multi:"Multi Units"
	},
	Options:{
		strict:"Exclude characters not matching all filters"
	}
};

function init() // entry point, called by body onload
{
	output = document.getElementById("output");
	output_loading();
	gbf = new GBF();
	fetchJSON("json/changelog.json?" + timestamp).then((value) => {
		load(value);
	});
}

function load(changelog)
{
	if(changelog)
	{
		timestamp = changelog.timestamp; // start the clock
		clock(); // start the clock
		if(changelog.hasOwnProperty("issues")) // write issues if any
		{
			issues(changelog);
		}
	}
	fetchJSON("json/data.json?" + timestamp).then((value) => {
		index = value;
		if(index == null)
		{
			crash();
		}
		else
		{
			start(changelog)
		}
	});
}

function start(changelog)
{
	if(typeof index.lookup == 'undefined' || typeof index.characters == 'undefined' || output == null)
	{
		crash();
		return;
	}
	allocate_pools();
	init_start_ui();
}

function init_start_ui(clear = true)
{
	if(clear)
		output.innerHTML = "";
	add_to(output, "button", {cls:["tab-button"], onclick:init_ranking}).innerHTML = '<img class="tab-button-icon" src="../GBFML/assets/ui/icon/view.png">Start';
	
	for(const [title, line] of Object.entries(options))
	{
		div = add_to(output, "div", {cls:["search-control"]});
		div.appendChild(document.createTextNode(title));
		div.appendChild(document.createElement("br"));
		
		let check_list = [];
		for(const [key, name] of Object.entries(line))
		{
			let container = add_to(div, "span", {
				cls:["search-checkbox-container"]
			});
			
			let input = add_to(container, "input", {cls:["checkbox"]});
			input.type = "checkbox";
			input.name = name;
			input.checked = key in checkboxes ? checkboxes[key].checked : true;
			checkboxes[key] = input; // store it
			check_list.push(input);
			
			let label = add_to(container, "label", {
				cls:["checkbox-label"],
				innertext:name
			});
			label.for = name;
		}
		if(check_list.length > 1)
		{
			const t = check_list.slice();
			add_to(div, "button", {
				cls:["toggle-button"],
				innertext:"Toggle",
				onclick:function()
				{
					let bool = !(t[0].checked);
					for(let check of t)
					{
						check.checked = bool;
					}
				}
			});
		}
	}
}

function allocate_pools()
{
	pools = {
		r:[],
		sr:[],
		ssr:[],
		
		fire:[],
		water:[],
		earth:[],
		wind:[],
		light:[],
		dark:[],
		any:[],
		
		male:[],
		female:[],
		other:[],
		
		human:[],
		erune:[],
		draph:[],
		harvin:[],
		primal:[],
		unknown:[],
		
		none:[],
		grand:[],
		summer:[],
		yukata:[],
		valentine:[],
		halloween:[],
		holiday:[],
		formal:[],
		"12generals":[],
		fantasy:[],
		collab:[],
		eternals:[],
		evokers:[],
		"4saints":[],
		
		single:[],
		multi:[],
		original:[],
		dupe:[],
		
		list:{}
	}
	let releases = {};
	for(const id of Object.keys(index.characters))
	{
		if(!(id in index.lookup))
			continue;
		if(index.lookup[id].includes("cut-content") || index.lookup[id].includes("missing-help-wanted") || index.lookup[id].includes("voice-only"))
			continue;
		let words = index.lookup[id].split(" ");
		let offset = words[0].startsWith("@@") ? 1 : 0; // skip wiki
		// element (always the first)
		if(!(["fire", "water", "earth", "wind", "light", "dark", "any"].includes(words[offset])))
			continue;
		pools[words[offset++]].push(id);
		// rarity
		if(!(["r", "sr", "ssr"].includes(words[offset])))
			continue;
		pools[words[offset++]].push(id);
		// name and race
		let start = offset;
		while(gbf.lookup_word_is_part_of_name(words[offset]))
		{
			++offset;
		}
		let name = words.slice(start, offset).join(" ");
		pools.list[id] = name;
		// dual units
		if(pools.list[id].includes(" and "))
			pools.multi.push(id);
		else
			pools.single.push(id);
		if(["human", "erune", "draph", "harvin", "primal", "unknown"].includes(words[offset])) // no series
		{
			pools.none.push(id);
		}
		while(!(["human", "erune", "draph", "harvin", "primal", "unknown"].includes(words[offset]))) // series
		{
			if(words[offset] in pools)
				pools[words[offset]].push(id);
			++offset;
			if(offset >= words.length)
			{
				--offset;
				break;
			}
		}
		while(["human", "erune", "draph", "harvin", "primal", "unknown"].includes(words[offset]))
			pools[words[offset++]].push(id); // race
		// gender
		while(["male", "female", "other"].includes(words[offset]))
		{
			pools[words[offset++]].push(id);
		}
		// Date
		offset = words.length - 1;
		if(words[offset][4] == '-' && words[offset][7] == '-')
		{
			if(!(words[offset] in releases))
				releases[words[offset]] = [];
			releases[words[offset]].push([id, name]);
		}
	}
	// sort releases dates to find alternate versions
	let dates = Object.keys(releases);
	dates.sort();
	let name_set = new Set();
	for(const release_date of dates)
	{
		for(const [id, name] of releases[release_date])
		{
			// alt versions
			if(name_set.has(name))
			{
				pools.dupe.push(id);
			}
			else
			{
				pools.original.push(id);
				name_set.add(name);
			}
		}
	}
}

function shuffle(arr)
{
    var j, x, index;
    for (index = arr.length - 1; index > 0; index--) {
        j = Math.floor(Math.random() * (index + 1));
        x = arr[index];
        arr[index] = arr[j];
        arr[j] = x;
    }
    return arr;
}

function init_ranking()
{
	beep();
	game_data = {
		characters:[],
		result:[[]],
		count:0,
		index:0
	};
	// add checked ones
	let set = new Set(Object.keys(pools.list));
	// remove id not matching filters
	if(checkboxes.strict.checked) // strict mode
	{
		for(const [key, input] of Object.entries(checkboxes))
		{
			if(!input.checked)
			{
				for(let id of pools[key])
				{
					if(set.has(id))
					{
						set.delete(id);
					}
				}
			}
		}
	}
	else
	{
		for(const id of Object.keys(pools.list))
		{
			if(!set.has(id))
				continue;
			for(const [title, line] of Object.entries(options))
			{
				if(title == "Options")
					continue;
				let state = false;
				for(const [key, name] of Object.entries(line))
				{
					if(pools[key].includes(id))
					{
						state = checkboxes[key].checked;
						if(state)
						{
							break;
						}
					}
				}
				if(!state)
				{
					set.delete(id);
					break;
				}
			}
		}
	}
	// init characters
	for(const id of set)
	{
		game_data.characters.push(id);
	}
	shuffle(game_data.characters);
	game_data.count = Object.keys(game_data.characters).length;
	if(game_data.count < 2)
	{
		push_popup("The game needs at least 2 characters in the pool to start");
	}
	else
	{
		document.getElementById("confirm-prompt").style.display = "";
		document.getElementById("prompt-text").textContent = game_data.count + " Characters in the pool. Start the game?";
	}
}

function init_confirm()
{
	beep();
	document.getElementById("confirm-prompt").style.display = "none";
	output_loading();
	init_ui();
	game_step();
}

function init_cancel()
{
	beep();
	document.getElementById("confirm-prompt").style.display = "none";
}

function output_loading()
{
	output.innerHTML = '<svg style="display:block;margin:auto;" width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><style>.spinner_0XTQ{transform-origin:center;animation:spinner_y6GP .75s linear infinite}@keyframes spinner_y6GP{100%{transform:rotate(360deg)}}</style><path class="spinner_0XTQ" d="M12,23a9.63,9.63,0,0,1-8-9.5,9.51,9.51,0,0,1,6.79-9.1A1.66,1.66,0,0,0,12,2.81h0a1.67,1.67,0,0,0-1.94-1.64A11,11,0,0,0,12,23Z" fill="#62c1e5"/></svg>';
}

function init_ui()
{
	ui_elements = {};
	output.innerHTML = "";
	let ui = add_to(output, "div", {cls:["game-ui"]});
	// line 1
	add_to(ui, "div");
	ui_elements.progress = add_to(ui, "div", {cls:["small-text"]});
	add_to(ui, "div");
	// line 2
	ui_elements.chara1_parent = add_to(ui, "div");
	ui_elements.chara1 = add_to(ui_elements.chara1_parent, "img", {
		cls:["loading", "vs-asset"]
	});
	add_to(ui, "div", {cls:["vs-spacer"]});
	ui_elements.chara2_parent = add_to(ui, "div");
	ui_elements.chara2 = add_to(ui_elements.chara2_parent, "img", {
		cls:["loading", "vs-asset"]
	});
	// line 3
	ui_elements.btn1 = add_to(ui, "button", {cls:["vs-button", "vs-button-animate"]});
	add_to(ui, "div", {cls:["vs-grid-text"], innertext:"Your choice?"});
	ui_elements.btn2 = add_to(ui, "button", {cls:["vs-button", "vs-button-animate"]});
	// line 4
	add_to(ui, "div");
	ui_elements.random = add_to(ui, "button", {
		cls:["vs-button"],
		innertext:"Pick for me"
	});
	add_to(ui, "div");
}

function capitalize(s) {
	return s.charAt(0).toUpperCase() + s.slice(1);
}

function game_step()
{
	if(game_data.characters.length == 1)
	{
		game_data.result.push(game_data.characters);
		game_result();
		return;
	}
  
	if(game_data.index == game_data.characters.length - 1) // for odd lists
		game_data.index = 0;
	game_ask(game_data.characters[game_data.index], game_data.characters[game_data.index+1]);
}

function game_ask(id1, id2)
{
	// update ui
	ui_elements.progress.textContent = Math.round(((game_data.count - game_data.characters.length) / game_data.count) * 10000) / 100 + "%";
	ui_elements.btn1.textContent = capitalize(pools.list[id1]);
	ui_elements.btn1.onclick = () => {
		game_win(id1, id2);
	};
	ui_elements.btn2.textContent = capitalize(pools.list[id2]);
	ui_elements.btn2.onclick = () => {
		game_win(id2, id1);
	};
	ui_elements.random.onclick = () => {
		if(Math.random() < 0.5)
		{
			ui_elements.btn1.click();
			push_popup("I picked " + capitalize(pools.list[id1]));
		}
		else
		{
			ui_elements.btn2.click();
			push_popup("I picked " + capitalize(pools.list[id2]));
		}
	}
	// set images
	// get urls
	let data1 = get_character_vs(id1, index.characters[id1]);
	let data2 = get_character_vs(id2, index.characters[id2]);
	// clean up
	ui_elements.chara1_parent.firstChild.remove();
	ui_elements.chara1 = add_to(ui_elements.chara1_parent, "img", {
		cls:["loading", "vs-asset"]
	});
	ui_elements.chara2_parent.firstChild.remove();
	ui_elements.chara2 = add_to(ui_elements.chara2_parent, "img", {
		cls:["loading", "vs-asset"]
	});
	// set
	ui_elements.chara1.src = data1.path.replace("GBF/", gbf.id_to_endpoint(data1.id)).replace("npc/m/", "npc/f/");
	ui_elements.chara1.onerror = data1.onerr;
	ui_elements.chara2.src = data2.path.replace("GBF/", gbf.id_to_endpoint(data2.id)).replace("npc/m/", "npc/f/");
	ui_elements.chara2.onerror = data2.onerr;
}

function game_win(winner, loser)
{
	beep();
	game_data.result[game_data.result.length - 1].push(loser);
	game_data.characters[game_data.index++] = winner;
	game_data.characters.splice(game_data.index, 1);
	if(game_data.index >= game_data.characters.length - 1)
	{
		game_data.index = 0;
		game_data.result.push([]);
	}
	game_step();
}

function game_result()
{
	output.innerHTML = "";
	add_to(output, "div", {cls:[], innertext:"Your top selection"});
	let count = 0;
	for(let i = game_data.result.length - 1; i >= 0; --i)
	{
		if(game_data.result[i].length == 0)
			continue;
		let formatted = [];
		for(const id of game_data.result[i])
		{
			formatted.push([id, GBFType.character]);
		}
		list_elements(
			add_to(output, "div", {cls:["ranking-line", "ranking-line-"+count]}),
			formatted
		);
		count++;
		if(count >= 7)
			break;
	}
	init_start_ui(false);
}

get_character_vs = function(id, data, _unused_a_ = null, _unused_b_ = null)
{
	if(data == null)
		return null;
	let suffixes = [];
	for(const el of data[5])
	{
		if(el.includes("_f"))
			continue;
		let s = el.split("_");
		let u = s[1];
		if(s.length > 2)
		{
			if(suffixes.length == 0 || suffixes[suffixes.length - 1] == u)
			{
				suffixes.push(u + "_" + s[2]);
			}
		}
		else if(u.startsWith("0"))
		{
			suffixes = [];
			suffixes.push(u);
		}
	}
	let onerr = default_onerror;
	if(suffixes.length > 1)
	{
		onerr = function() {
			this.src=gbf.id_to_endpoint(id) + "assets_en/img_low/sp/assets/npc/f/"+id+"_"+suffixes[1]+".jpg";
			this.onerror=default_onerror;
		};
	}
	let path = "GBF/assets_en/img_low/sp/assets/npc/m/" + id + "_" + suffixes[0] + ".jpg";
	return {id:id, path:path, onerr:onerr, class:"", link:false};
}