/*jshint esversion: 11 */

/*
This file uses ranker.js as a base
*/

var slider_enabled = false;
var slider_index = 0;
var slider_images = null;
var slider_skip = false;
var stats = {};
var undo_stack = [];

const table_columns = ["male", "female", "other", "total"];
const table_rows = ["human", "erune", "draph", "harvin", "primal", "unknown", "total"];

function init_smash() // entry point, called by body onload
{
	init_start_ui = function(clear = true)
	{
		if(clear)
			output.innerHTML = "";
		add_to(output, "button", {cls:["tab-button"], onclick:init_ranking}).innerHTML = '<img class="tab-button-icon" src="assets/ui/smash.png">Smash or Pass';
		init_checkboxes();
	}
	init_ui = function()
	{
		ui_elements = {};
		output.innerHTML = "";
		// buttons
		ui_elements.buttons = add_to(output, "div", {cls:["smash-button-container"]});
		add_to(ui_elements.buttons, "button", {cls:["tab-button", "smash-button-smash"], onclick:smash}).innerHTML = '<img class="tab-button-icon" src="assets/ui/smash.png">Smash';
		add_to(ui_elements.buttons, "button", {cls:["tab-button", "smash-button-pass"], onclick:pass}).innerHTML = '<img class="tab-button-icon" src="assets/ui/pass.png">Pass';
		add_to(ui_elements.buttons, "br");
		ui_elements.undo = add_to(ui_elements.buttons, "button", {cls:["toggle-button"], onclick:pass, innertext:"Undo", onclick:undo});
		ui_elements.undo.disabled = true;
		// name
		ui_elements.name = add_to(output, "div");
		// main ui
		let ui = add_to(output, "div", {cls:["smash-ui"]});
		ui_elements.global = ui;
		// line 1
		add_to(ui, "div");
		ui_elements.progress = add_to(ui, "div", {cls:["small-text"]});
		
		// line 2
		// image slider
		let contain = add_to(ui, "div", {cls:["smash-slider-container"]});
		ui_elements.slider = add_to(contain, "div", {cls:["smash-slider"], id:"smash-slider"});
		
		// table
		ui_elements.table = add_to(ui, "table", {cls:["smash-table"]});
		let tr = add_to(ui_elements.table, "tr", {cls:["smash-table-tr"]});
		add_to(tr, "th", {cls:["smash-table-cell", "smash-table-header"], innertext:"SMASHED"});
		for(const column of table_columns)
		{
			add_to(tr, "th", {cls:["smash-table-cell", "smash-table-header"], innertext:capitalize(column)});
		}
		for(const row of table_rows)
		{
			tr = add_to(ui_elements.table, "tr", {cls:["smash-table-tr"]});
			add_to(tr, "td", {cls:["smash-table-cell", "smash-table-header"], innertext:capitalize(row)});
			for(const column of table_columns)
			{
				if(row == "total" && column == "total")
				{
					ui_elements[row + "-" + column] = add_to(tr, "td", {cls:["smash-table-cell"], innertext:"/ 0"});
				}
				else
				{
					ui_elements[row + "-" + column] = add_to(tr, "td", {cls:["smash-table-cell"], innertext:"0"});
				}
				stats[row + "-" + column] = 0;
			}
		}
		// smashed list
		ui_elements.smashed_list = add_to(output, "div", {cls:["ranking-line", "ranking-line-3"]});
		ui_elements.smashed_list.style.display = "none";
		add_to(ui_elements.smashed_list, "div", {innertext:"Smashed"});
	}
	game_step = function()
	{
		if(game_data.characters.length == 0)
		{
			game_result();
			return;
		}
		game_ask(game_data.characters[0]);
	}
	game_ask = function(id)
	{
		// update ui
		ui_elements.progress.textContent = Math.round(((game_data.count - game_data.characters.length) / game_data.count) * 10000) / 100 + "%";
		ui_elements.name.textContent = capitalize(pools.list[id]);
		
		// set images
		ui_elements.slider.innerHTML = "";
		for(const url of get_character_smash(id, index.characters[id]))
		{
			let img = add_to(ui_elements.slider, "img", {cls:["loading", "smash-asset"], onerror:function(){
					this.remove();
				}
			});
			img.src = url;
			img.onload = function()
			{
				this.classList.toggle("loading", false);
			}
		}
		slider_enabled = true;
		reset_slider();
	}
	game_result = function()
	{
		ui_elements.progress.textContent = "Game Over";
		ui_elements.global.classList.toggle("smash-ui", false);
		ui_elements.global.classList.toggle("smash-result-ui", true);
		ui_elements.global.childNodes[2].remove();
		ui_elements.global.childNodes[0].remove();
		ui_elements.name.remove();
		ui_elements.buttons.remove();
		init_start_ui(false);
	}
	
	setInterval(slide, 3000);
	init();
}

function smash()
{
	beep();
	let modified_stats = [];
	let id = game_data.characters[0];
	for(const c of table_columns)
	{
		if(c != "total" && pools[c].includes(id))
		{
			for(const r of table_rows)
			{
				if(r != "total" && pools[r].includes(id))
				{
					++stats[r + "-" + c];
					modified_stats.push(r + "-" + c);
					++stats[r + "-total"];
					modified_stats.push(r + "-total");
					++stats["total-" + c];
					modified_stats.push("total-" + c);
					++stats["total-total"];
					modified_stats.push("total-total");
				}
			}
		}
	}
	if(ui_elements.smashed_list.style.display != "")
	{
		ui_elements.smashed_list.style.display = "";
	}
	list_elements(ui_elements.smashed_list, [[id, GBFType.character]]);
	undo_stack.push(
		{
			id:id,
			stats:modified_stats,
			smashed:true
		}
	);
	ui_elements.undo.disabled = false;
	update_table();
	game_data.characters.shift();
	game_step();
}

function pass()
{
	beep();
	let id = game_data.characters[0];
	++stats["total-total"];
	undo_stack.push(
		{
			id:id,
			stats:["total-total"],
			smashed:false
		}
	);
	ui_elements.undo.disabled = false;
	update_table();
	game_data.characters.shift();
	game_step();
}

function undo()
{
	beep();
	let item = undo_stack.pop();
	game_data.characters.splice(game_data.characters, 0, item.id);
	for(const stat_key of item.stats)
	{
		--stats[stat_key];
	}
	if(item.smashed)
	{
		ui_elements.smashed_list.removeChild(ui_elements.smashed_list.lastChild);
		if(ui_elements.smashed_list.childNodes.length <= 1)
		{
			ui_elements.smashed_list.style.display = "none";
		}
	}
	if(undo_stack.length == 0)
	{
		ui_elements.undo.disabled = true;
	}
	update_table();
	game_step();
}

function update_table()
{
	for(const [key, val] of Object.entries(stats))
	{
		if(val > 0)
		{
			ui_elements[key].classList.toggle("smash-table-header", true);
		}
		if(key == "total-total")
		{
			ui_elements[key].textContent = "/ " + val;
		}
		else
		{
			ui_elements[key].textContent = val;
		}
	}
}

function get_character_smash(id, data)
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
			if(s[2].length == 2 && suffixes.length > 0 && suffixes[suffixes.length - 1].length == 2)
			{
				suffixes.pop();
			}
			if(suffixes.length == 0 || !suffixes[suffixes.length - 1].startsWith(u))
			{
				suffixes.push(u + "_" + s[2]);
			}
		}
		else
		{
			suffixes.push(u);
		}
	}
	for(let i = 0; i < suffixes.length; ++i)
	{
		suffixes[i] = gbf.id_to_endpoint(id) + "assets_en/img_low/sp/assets/npc/result_lvup/"+id+"_"+suffixes[i]+".png";
	}
	return suffixes; // actually list of urls
}

function reset_slider()
{
	slider_index = -1;
	slider_images = document.querySelectorAll('.smash-asset');
	slide();
	slider_skip = true;
}

function slide()
{
	if(slider_enabled)
	{
		if(slider_skip)
		{
			slider_skip = false;
		}
		else
		{
			slider_index = (slider_index + 1) % slider_images.length;
			const translateValue = - slider_index * slider_images[0].clientWidth;
			ui_elements.slider.style.transform = `translateX(${translateValue}px)`;
		}
	}
}