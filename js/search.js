/*jshint esversion: 11 */

var search_id = null;
var search_onclick = null;
var search_results = []; // search results
var previous_displayed_result = [];
const SEARCH_LIMIT = 100;

function filter() // called by the search filter (onkeyup event)
{
	clearTimeout(typing_timer);
	typing_timer = setTimeout(function(){ // set a timeout of 1s before executing lookup
		lookup(document.getElementById('filter').value);
	}, typing_update);
}

function init_search_lookup()
{
	if(index.lookup && !index.lookup_reverse)
	{
		index.lookup_reverse = {};
		for(const [key, value] of Object.entries(index.lookup))
		{
			if(!(value in index.lookup_reverse))
				index.lookup_reverse[value] = [];
			index.lookup_reverse[value].push(key);
		}
	}
}

function clean_search_if_not(id)
{
	let found = false;
	for(const el of search_results)
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
		search_results = [];
		previous_displayed_result = [];
		search_id = null;
	}
}

function search(id, internal_behavior = 0) // generate search results
/*
	* internal_behavior is only used by spark.html so far
	0 = default bevahior
	1 = spark mode: remove search limit, doesn't call update_search_results at the end, limit the search to premium elements
	2 = blind mode: remove search limit, doesn't call update_search_results at the end, limit the search to chara/npc elements
*/
{
	if(id == "" || id == search_id)
		return;
	// search
	let words = id.toLowerCase().replace("@@", "").split(' ');
	let positives = [];
	let counters = [];
	const _LIMIT_ = (internal_behavior >= 1) ? 1000000 : SEARCH_LIMIT;
	while(counters.length < 10)
		counters.push(0);
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
			for(const v of value)
			{
				if(
				   (internal_behavior == 1 && !(v in index["premium"]))
				|| (internal_behavior == 2 && !["302", "303", "304", "305", "399"].includes(v.slice(0, 3)))
				) continue;
				let et = 0;
				switch(v.length)
				{
					case 6: et = 0; break; // mc
					case 7: et = 4; break; // boss
					default: et = (["305", "399"].includes(v.slice(0, 3)) ? 5 : parseInt(v[0])); break;
				}
				if(counters[et] >= _LIMIT_) break;
				counters[et]++;
				positives.push([v, et]);
			}
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
	search_results = positives;
	search_id = id;
	if(!internal_behavior)
	{
		if(search_results.length > 0)
		{
			let filter = document.getElementById('filter');
			if(filter.value != id && filter.value.trim().toLowerCase() != id)
				filter.value = id;
		}
		update_search_results();
	}
}

function get_search_filter_states()
{
	let search_filters = localStorage.getItem("gbfal-search");
	if(search_filters != null)
	{
		try
		{
			search_filters = JSON.parse(search_filters);
			while(search_filters.length < 7) search_filters.push(true); // retrocompability
		}
		catch(err)
		{
			console.error("Exception thrown", err.stack);
			search_filters = [true, true, true, true, true, true, true];
		}
	}
	else search_filters = [true, true, true, true, true, true, true];
	return search_filters;
}

function update_search_results(scroll_to_search = true)
{
	if(search_results.length == 0) return;
	const search_filters = get_search_filter_states();
	// filter results
	let results = [];
	for(let e of search_results)
	{
		switch(e[1])
		{
			case 0:
				if(search_filters[5]) // classes
					results.push(e);
				break;
			case 1:
			case 2: // skins or characters or summons or weapons
			case 3:
				if(search_filters[e[0].slice(0, 2) == "37" ? 3 : e[1]-1])
					results.push(e);
				break;
			case 5:
				if(search_filters[4]) // npcs
					results.push(e);
				break;
			case 4:
				if(search_filters[6]) // enemies
					results.push(e);
				break;
			default:
				continue;
		}
		if(results.length >= SEARCH_LIMIT)
			break;
	}
	var node = document.getElementById('results');
	let frag = document.createDocumentFragment();
	if(results.length == 0)
	{
		frag.appendChild(document.createTextNode("No Results"));
	}
	else
	{
		if(nested_array_are_equal(results, previous_displayed_result)
			&& node.style.display != null)
		{
			if(scroll_to_search)
				scroll_to_search_results();
			return;
		}
		previous_displayed_result = results;
		list_elements(frag, results, search_onclick);
		frag.insertBefore(document.createElement("br"), frag.firstChild);
		frag.insertBefore(document.createTextNode((results.length >= SEARCH_LIMIT) ? "First " + SEARCH_LIMIT + " Results for \"" + search_id + "\"" : "Results for \"" + search_id + "\""), frag.firstChild);
	}
	// add checkboxes
	frag.appendChild(document.createElement("br"));
	frag.appendChild(document.createElement("br"));
	let div = document.createElement("div");
	div.classList.add("std-button-container");
	frag.appendChild(div);
	for(const e of [[0, "Weapons"], [1, "Summons"], [2, "Characters"], [3, "Skins"], [4, "NPCs"], [5, "MCs"], [6, "Enemies"]])
	{
		let input = document.createElement("input");
		input.type = "checkbox";
		input.classList.add("checkbox");
		input.name = e[1];
		input.onclick = function() {toggle_search_filter(e[0]);};
		input.checked = search_filters[e[0]];
		div.appendChild(input);
		let label = document.createElement("label");
		label.classList.add("checkbox-label");
		label.for = e[1];
		label.innerHTML = e[1];
		div.appendChild(label);
	}
	// wait next frame to give time to calculate
	update_next_frame(function() {
		node.style.display = null;
		node.innerHTML = "";
		node.appendChild(frag);
		if(scroll_to_search)
			scroll_to_search_results();
	});
}

function scroll_to_search_results()
{
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

function toggle_search_filter(indice)
{
	let search_filters = get_search_filter_states();
	// toggle
	search_filters[indice] = !search_filters[indice];
	// write
	try
	{
		localStorage.setItem("gbfal-search", JSON.stringify(search_filters));
	}
	catch(err)
	{
		console.error("Exception thrown", err.stack);
	}
	// update
	update_search_results(false);
}