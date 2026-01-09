/*jshint esversion: 11 */

var gbf = null;
var search = null;
var timestamp = Date.now();
var index = null;
var items = {};
var lists = [[], [], []];
var spark_container = null;
var spark_sections = null;
const NPC = 0;
const MOON = 1;
const STONE = 2;
const COUNT = 3;
const DEFAULT_SIZE = [140, 80];
var resize_timer = null;
// image generation
const HEADERS = ["assets/spark/gem.jpg", "assets/spark/moon.jpg", "assets/spark/sunstone.jpg"];
var canvas = null; // contains last canvas
var canvas_state = 0; // 0 = not running, 1 = running, 2 = error
var canvas_wait = 0; // used to track pending loadings
// drag and drop
var drag_state = 0; // 0 = not running, 1 = drag check, 2 = running
var drag_event = null; // contains the last event received to process
var drag_original_div = null; // the div that the user clicked on when dragging
var drag_placeholder_div = null; // placeholder div that is displayed to the user during drag-and-drop
var drag_id = null; // the ID of the character or summon that is being dragged
var drag_is_spark = null; // whether the dragged element is sparked or not
var drag_mode = null; // the mode (NPC/MOON/STONE) of the currently dragged item
var drag_position = null; // the position of the currently dragged item
var drag_coords = {x:0, y:0}; // pointer coordinates
var drag_is_complete = true; // whether the last drag event was completed successfully
var drag_ghost = null; // container of a "ghost" of the dragged image

var jukebox = null;

function init() // entry point, called by body onload
{
	spark_container = document.getElementById("spark-container");
	spark_sections = document.querySelectorAll(".spark-section");
	gbf = new GBF();
	fetchJSON("json/changelog.json?" + timestamp).then((value) => {
		load(value);
	});
	init_drag_and_drop();
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
	fetchJSON("../GBFML/json/jukebox.json").then((value) => {
		let node = document.getElementById("jukebox");
		jukebox = new AudioJukeboxPlayer(node, value);
	});
}

function start(changelog)
{
	search = new Search(
		document.getElementById("spark-filter"),
		null,
		null,
		{
			"wpn":["", GBFType.weapon],
			"sum":["", GBFType.summon],
			"cha":["", GBFType.character]
		},
		null,
		false,
		false
	);
	// add search event listeners
	document.addEventListener('search-update', function() {
		spark_apply_results(document.getElementById('spark-filter').value.trim().toLowerCase());
	});
	document.addEventListener('search-clear', function() {
		spark_reset_results();
	});
	// init the rest
	set_spark_list();
	spark_load_settings();
	load_settings();
	spark_container.scrollIntoView();
}

function open_spark_tab(tabName) // reset and then select a tab
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

function default_onerror() // overwrite definition
{
	this.remove();
}

function is_valid_mode(cid, mode, gbtype)
{
	if(gbtype == GBFType.summon && mode != STONE)
		return false;
	if(gbtype != GBFType.summon && mode == STONE)
		return false;
	return true;
}

function set_spark_list()
{
	// for each characters
	let node = document.getElementById('spark-select-npc');
	let frag = document.createDocumentFragment();
	const ckeys = Object.keys(index["characters"]).reverse();
	if(ckeys.length > 0) // add more non-indexed characters first, so that the user got recent stuff in all scenarios
	{
		let highest = parseInt(ckeys[0]);
		for(let i = 5; i > 0; --i)
		{
			let id = JSON.stringify(highest+i*1000);
			const ret = get_character(id, null, [-1, -1, -1, -1, 0, 1000]);
			if(ret != null)
			{
				items[id] = add_image_spark(frag, ret[0], GBFType.character); // display and memorize in items
			}
		}
	}
	for(const id of ckeys)
	{
		if(id in index["lookup"] && !(id in index["premium"]) && ckeys.indexOf(id) > 5) continue; // exclude non gacha characters (unless not in lookup = it's recent)
		const ret = get_character(id, (index["characters"][id] !== 0 ? index["characters"][id] : null), [-1, -1, -1, -1, 0, 1000]);
		if(ret != null)
		{
			items[id] = add_image_spark(frag, ret[0], GBFType.character); // display and memorize in items
		}
	}
	node.appendChild(frag);
	
	// for each summons
	node = document.getElementById('spark-select-summon');
	frag = document.createDocumentFragment();
	const skeys = Object.keys(index["summons"]).reverse();
	if(skeys.length > 0) // add more non-indexed summons first, so that the user got recent stuff in all scenarios
	{
		let highest = parseInt(skeys[0]);
		for(let i = 5; i > 0; --i)
		{
			let id = JSON.stringify(highest+i*1000);
			const ret = get_summon(id, null, "4", [0, 1000]);
			if(ret != null)
			{
				items[id] = add_image_spark(frag, ret[0], GBFType.summon); // display and memorize in items
			}
		}
	}
	for(const id of skeys)
	{
		if(id in index["lookup"] && !(id in index["premium"]) && skeys.indexOf(id) > 5) continue; // exclude non gacha summons (unless not in lookup = it's recent)
		const ret = get_summon(id, (index["summons"][id] !== 0 ? index["summons"][id] : null), "4", [0, 1000]);
		if(ret != null)
		{
			items[id] = add_image_spark(frag, ret[0], GBFType.summon); // display and memorize in items
		}
	}
	node.appendChild(frag);
}

function add_image_spark(node, data, gbtype) // add an image to the selector
{
	let img = document.createElement("img");
	img.title = data.id;
	img.dataset.id = data.id;
	img.spark_draggable = true;
	img.draggable = false; // important for event interaction
	img.gbtype = gbtype;
	img.classList.add("loading");
	img.classList.add("spark-image");
	img.setAttribute('loading', 'lazy');
	if(data.onerr == null)
	{
		img.onerror = function() {
			this.remove();
		};
	}
	else img.onerror = data.onerr;
	const cid = data.id;
	img.onload = function(event) {
		this.classList.remove("loading");
		this.classList.add("clickable");
		this.onclick = function()
		{
			if(canvas_state > 0) // if canvas processing
			{
				push_popup("Wait for the image to be processed");
			}
			else
			{
				canvas = null;
				beep();
				if(this.gbtype == GBFType.character && (window.event.shiftKey || document.getElementById("moon-check").classList.contains("active"))) // add to moon
				{
					add_image_result_spark(MOON, cid, this);
				}
				else
				{
					add_image_result_spark(this.gbtype == GBFType.summon ? STONE : NPC, cid, this); // add to npc or stone
				}
				spark_container.scrollIntoView(); // recenter view
				spark_save_settings();
			}
		};
	};
	img.src = data.path.replace("GBF/", gbf.id_to_endpoint(data.id));
	node.appendChild(img);
	return img;
}

function remove_image_result_spark(div) // remove image from the spark result
{
	for(let mode = 0; mode < COUNT; ++mode)
	{
		for(let i = 0; i < lists[mode].length; ++i) // look for it and remove
		{
			if(div === lists[mode][i][1])
			{
				lists[mode].splice(i, 1);
				div.remove();
				update_node(mode);
				return;
			}
		}
	}
}

function add_image_result_spark(mode, id, base_img, position) // add image to the spark result
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
	div.dataset.id = id;
	div.draggable = false;
	div.spark_draggable = true;
	div.classList.add("spark-result");
	div.onclick = function()
	{
		if(canvas_state > 0) // if canvas processing
		{
			push_popup("Wait for the image to be processed");
		}
		else
		{
			canvas = null;
			beep();
			if(window.event.shiftKey || document.getElementById("spark-check").classList.contains("active")) // toggle spark icon
			{
				toggle_spark_state(div);
				update_rate(false);
			}
			else
			{
				remove_image_result_spark(this);
			}
			spark_save_settings();
			
		}
	};
	const cmode = mode;
	let img = document.createElement("img");
	img.draggable = false; // important  for event interaction
	img.classList.add("spark-result-img");
	img.src = base_img.src;
	img.onerror = base_img.onerror;
	div.appendChild(img);

	if(position === undefined)
		position = lists[mode].length;
	node.insertBefore(div, node.children[position]);
	lists[mode].splice(position, 0, [id, div]);

	update_node(mode);
	return div;
}

function toggle_spark_state(div) // toggle spark icon
{
	if(div.classList.contains("sparked")) remove_spark(div);
	else add_spark(div);
}

function add_spark(div) // add spark icon
{
	if(div.classList.contains("sparked"))
		return;
	let img = document.createElement("img");
	img.classList.add("spark-icon");
	img.draggable = false;
	img.src = "assets/spark/spark.png";
	div.appendChild(img);
	div.classList.add("sparked");
}

function remove_spark(div) // remove spark icon
{
	if(!div.classList.contains("sparked"))
		return;
	div.removeChild(div.childNodes[1]);
	div.classList.remove("sparked");
}

addEventListener("resize", (event) => { // capture window resize event and call update_all() (after 300ms)
	if(resize_timer != null)
		clearTimeout(resize_timer);
	resize_timer = setTimeout(update_all, 300);
});

function init_drag_and_drop()
{
	// general drag events
	document.addEventListener("pointerdown", handle_dragstart);
}

function find_target(base_target)
{
	// for pointer events,
	// event.target sometimes catch the underlying image
	return (
		base_target.classList.contains("spark-image") ?
		base_target :
		(
			(
				base_target.classList.contains("spark-result-img") ||
				base_target.classList.contains("spark-icon")
			) ?
			base_target.parentNode : // catch the parent div
			base_target
		)
	);
}

function handle_dragstart(event)
{
	if(drag_state) // don't start if already on going
		return;
	const target = find_target(event.target);
	if(target.spark_draggable !== true || target.classList.contains("loading"))
		return;
	if(canvas_state > 0) // if canvas processing
	{
		push_popup("Wait for the image to be processed");
	}
	else
	{
		// get and check id
		drag_id = target.dataset.id;
		if(!(drag_id in items))
			return;
		// check if the user is dragging from one of the three spark result sections
		const section = target.closest(".spark-section");
		if(section)
		{
			// if ctrlKey is pressed, we make a new element instead
			if(!event.ctrlKey)
			{
				// store the neccesary info
				drag_original_div = target;
				drag_is_spark = target.classList.contains("sparked");
				let mode;
				switch(section.id)
				{
					case "spark-npc": mode = NPC; break;
					case "spark-moon": mode = MOON; break;
					case "spark-summon": mode = STONE; break;
					default: return;
				}
				drag_mode = mode;
				drag_position = Array.from(section.children).indexOf(drag_original_div);
			}
			// the rest of the initializaion is done in update_drag_state()
		}
		else // the user is dragging from the select filter
		{
			// do nothing
		}
		// set state
		drag_state = 1;
		drag_is_complete = false;
		drag_coords.x = event.clientX;
		drag_coords.y = event.clientY;
		drag_ghost = null;
		// enable listeners
		document.addEventListener("pointermove", handle_dragmove);
		document.addEventListener("pointerup", handle_dragend);
	}
}

// find position in index from pointer coordinate
function find_position(section, event)
{
	const children = section.children;
	let position = 0;
	for(let i = 0; i < children.length; ++i)
	{
		const rect = children[i].getBoundingClientRect();
		if(event.clientY < rect.top)
			break;
		else if(event.clientY < rect.bottom && event.clientX < rect.left)
			break;
		position = i;
	}
	return position;
}

// return the section we're hovering, or null
function find_section(event)
{
	if(drag_ghost)
		drag_ghost.style.display = 'none';
    const targetBelow = document.elementFromPoint(event.clientX, event.clientY);
	if(drag_ghost)
		drag_ghost.style.display = null;
    if(!targetBelow)
		return null;
    return targetBelow.closest(".spark-section");
}

// queue an event for processing
function queue_drag_state(event)
{
	const event_pending = drag_event != null;
	drag_event = event;
	if(!event_pending)
	{
		// only process the last received event at the next frame
		requestAnimationFrame(() => {
			const ev = drag_event;
			drag_event = null;
			if(ev != null && drag_id)
			{
				update_drag_state(ev);
			}
		});
	}
}

// processing the event
function update_drag_state(event)
{
	switch(drag_state)
	{
		case 1: // drag initialization
		{
			// check how much we moved since click down
			const delta = {
				x: event.clientX - drag_coords.x,
				y: event.clientY - drag_coords.y
			};
			// check for accidental drags
			// by looking for a movement of more than 5px
			if(delta.x * delta.x + delta.y * delta.y > 25)
			{
				// initialize dragging
				drag_state = 2;
				// create ghost
				// don't clone, in case the img isn't loaded
				drag_ghost = document.createElement("img");
				drag_ghost.src = items[drag_id].src;
				drag_ghost.classList.add("spark-drag-ghost");
				drag_ghost.style.transform = `translate(${event.clientX - 52}px, ${event.clientY - 30}px)`;
				document.body.appendChild(drag_ghost);
				// hide initial div and create placeholder
				if(drag_original_div)
				{
					const img = items[drag_id];
					drag_original_div.style.display = "none";
					drag_placeholder_div = add_image_result_spark(drag_mode, drag_id, img, drag_position);
					drag_placeholder_div.classList.add("placeholder");
					if(drag_is_spark)
						add_spark(drag_placeholder_div);
					update_rate(false);
					// note: No need for update_node()
				}
				// add the highlight
				let drag_highlight_range = (
					items[drag_id].gbtype == GBFType.summon ?
					[2, 3] :
					[0, 2]
				);
				for(let i = drag_highlight_range[0]; i < drag_highlight_range[1]; ++i)
				{
					spark_sections[i].classList.toggle("spark-section-highlight", true);
				}
			}
			else return;
		}
		case 0: // not dragging
		{
			return;
		}
	}
	if(!event.clientX && !event.clientY)
		return;
	// only update if moved
	if(event.clientX == drag_coords.x && event.clientY == drag_coords.y)
		return;
	// update coordinates
	drag_coords.x = event.clientX;
	drag_coords.y = event.clientY;
	if(drag_ghost) // use gpu via translate to avoid layout recalcul
		drag_ghost.style.transform = `translate(${drag_coords.x - 52}px, ${drag_coords.y - 30}px)`;
	const target = find_target(event.target);
	let section = find_section(event);
	const img = items[drag_id];
	let mode;
	if(section)
	{
		switch(section.id)
		{
			case "spark-npc": mode = NPC; break;
			case "spark-moon": mode = MOON; break;
			case "spark-summon": mode = STONE; break;
			default: return;
		}
	}
	// check if the targeted section is valid
	if(!img || !is_valid_mode(drag_id, mode, img.gbtype))
		section = null;
	if(section == null)
	{
		// if not, remove highlight and placeholder
		for(const s of spark_sections)
		{
			s.classList.toggle("spark-section-highlight-enabled", false);
		}
		if(drag_placeholder_div)
		{
			lists[drag_mode].splice(drag_position, 1);
			drag_placeholder_div.remove();
			drag_placeholder_div = null;
			update_node(drag_mode);
			drag_mode = -1;
			drag_position = -1;
		}
		return;
	}
	// find position
	const position = find_position(section, event);
	// and check if it changed
	if(drag_mode === mode && drag_position === position)
		return;
	// add the highlight
	for(const s of spark_sections)
	{
		s.classList.toggle("spark-section-highlight-enabled", s == section);
	}
	// remove previous placeholder
	if(drag_placeholder_div)
	{
		lists[drag_mode].splice(drag_position, 1);
		drag_placeholder_div.remove();
		drag_placeholder_div = null;
		update_node(drag_mode);
	}
	// update mode and position
	drag_mode = mode;
	drag_position = position;
	// set new placeholder
	drag_placeholder_div = add_image_result_spark(mode, drag_id, img, drag_position);
	drag_placeholder_div.classList.add("placeholder");
	if(drag_is_spark)
		add_spark(drag_placeholder_div);
	update_node(drag_mode);
	update_rate(false);
}

// triggered when moving the mouse
function handle_dragmove(event)
{
	if(!drag_state)
		return;
	if(!(event.target instanceof HTMLElement))
		return;
	if(canvas_state > 0) // if canvas processing
	{
		return;
	}
	event.preventDefault();
	queue_drag_state(event);
}

// triggered when releasing the mouse
function handle_dragend(event)
{
	if(drag_state == 0)
		return;
	if(drag_ghost)
		drag_ghost.remove();
	drag_ghost = null;
	// flag to check if we dragging went through
	const process_drag = canvas_state == 0 && drag_state == 2;
	// remove listeners
	document.removeEventListener("pointermove", handle_dragmove);
	document.removeEventListener("pointerup", handle_dragend);
	if(process_drag && drag_mode != -1)
	{
		// force process the queued last event
		drag_event = null;
		update_drag_state(event);
		const img = items[drag_id];
		if(img)
		{
			// check validity and add to list
			if(is_valid_mode(drag_id, drag_mode, img.gbtype))
			{
				const div = add_image_result_spark(drag_mode, drag_id, img, drag_position);
				drag_position++; // for the deletion of the placeholder
				if(drag_is_spark)
				{
					add_spark(div);
				}
				drag_is_complete = true;
			}
		}
	}
	// remove placeholder
	if(drag_placeholder_div)
	{
		lists[drag_mode].splice(drag_position, 1);
		drag_placeholder_div.remove();
		drag_placeholder_div = null;
	}
	// remove or restore original div
	if(drag_original_div)
	{
		if(drag_is_complete || drag_mode == -1)
		{
			remove_image_result_spark(drag_original_div);
			drag_is_complete = true; // for the beep below
		}
		else
		{
			drag_original_div.style.display = null;
		}
	}
	if(drag_is_complete)
		beep();
	// reset everything else
	drag_state = 0;
	drag_coords = {x:0, y:0};
	drag_original_div = null;
	drag_placeholder_div = null;
	drag_id = null;
	drag_is_spark = null;
	drag_mode = null;
	drag_position = null;
	for(let i = 0; i < spark_sections.length; ++i)
	{
		spark_sections[i].classList.toggle("spark-section-highlight", false);
		spark_sections[i].classList.toggle("spark-section-highlight-enabled", false);
	}
	// update and save
	update_all();
	update_rate(false);
	spark_save_settings();
}

function update_all() // update all three columns
{
	clearTimeout(resize_timer);
	resize_timer = null;
	update_node(NPC);
	update_node(MOON);
	update_node(STONE);
}

function count_visible_nodes(list)
{
	let count = 0;
	for(let i = 0; i < list.length; ++i)
	{
		if(list[i].style.display != "none") ++count;
	}
	return count;
}

function update_node(mode) // update spark column
{
	let node;
	switch(mode)
	{
		case NPC: node = document.getElementById("spark-npc"); break;
		case MOON: node = document.getElementById("spark-moon"); break;
		case STONE: node = document.getElementById("spark-summon"); break;
		default: return;
	}
	update_rate(false); // update rate text
	if(node.childNodes.length == 0)
		return; // quit if empty
	// get node size
	const nw = node.offsetWidth - 5;
	const nh = node.offsetHeight - 5;
	let current_size = DEFAULT_SIZE; // get default size otherwise
	let changed = false;
	const visibleNodesCount = count_visible_nodes(node.childNodes);
	while(true)
	{
		const cw = Math.floor(nw/current_size[0]); // number of element in a row inside the node
		const ch = Math.floor(nh/current_size[1]) - 1; // number of element in a column inside the node (-1 to assure some space)
		if(visibleNodesCount <= cw*ch) // if the total number of element is greater to our number of ssr
		{
			break;
		}
		// else, reduce size by 10% and try again
		current_size = [
			current_size[0] * 0.9,
			current_size[1] * 0.9
		];
		changed = true;
	}
	if(changed) // if size changed
	{
		for(let i = 0; i < node.childNodes.length; ++i) // resize all elements
		{
			if(current_size == null)
			{
				node.childNodes[i].style.minWidth = null;
				node.childNodes[i].style.minHeight = null;
				node.childNodes[i].style.maxWidth = null;
				node.childNodes[i].style.maxHeight = null;
			}
			else
			{
				node.childNodes[i].style.minWidth = "" + Math.max(1, current_size[0]) + "px"; // min needed for mobile
				node.childNodes[i].style.minHeight = "" + Math.max(1, current_size[1]) + "px";
				node.childNodes[i].style.maxWidth = "" + Math.max(1, current_size[0]) + "px";
				node.childNodes[i].style.maxHeight = "" + Math.max(1, current_size[1]) + "px";
			}
		}
	}
}

function update_rate(to_update) // update ssr rate text
{
	if(canvas_state > 0) // if canvas processing
	{
		push_popup("Wait for the image to be processed");
	}
	else
	{
		canvas = null;
		let v;
		try
		{
			v = parseInt(document.getElementById("spark-roll-input").value);
			if(isNaN(v) || v <= 0) v = 300;
			let c = 0; // total ssr count
			let s = 0; // sparked
			for(let i = 0; i < COUNT; ++i)
				for(let j = 0; j < lists[i].length; ++j)
					if(lists[i][j][1].style.display != "none")
					{
						if(lists[i][j][1].childNodes.length == 2) ++s;
						else ++c;
					}
			if(v < c) v = c;
			document.getElementById("spark-rate").innerHTML = "" + c + " / " + v + (s > 0 ? " +" + s + " sparked": "") + "<br>" + (Math.round(c / v * 1000) / 10) + "% SSR";
		}
		catch(err)
		{
			console.error("Exception thrown", err.stack);
			return;
		}
		if(to_update) spark_save_settings();
	}
}

function confirm_spark_clear() // open popup when pressing reset button
{
	if(canvas_state > 0) // if canvas processing
	{
		push_popup("Wait for the image to be processed");
	}
	else
	{
		let div = document.createElement("div");
		div.classList.add("fullscreen-preview");
		div.innerHTML = '<div class="spark-delete-confirm">Are you certain that you want to reset the spark screen?<br><button class="std-button" onclick="close_fullscreen(); spark_clear();">Yes</button><button class="std-button" onclick="close_fullscreen();">No</button></div>';
		document.body.appendChild(div);
	}
}

function spark_clear() // clear everything
{
	canvas = null;
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
	document.getElementById("spark-roll-input").value = 300;
	update_all();
	update_rate(false);
}

function spark_save_settings() // save spark in localstorage
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

function spark_load_settings() // load spark from localstorage
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
					let div = add_image_result_spark(i, tmp[i][j][0], items[tmp[i][j][0]]);
					if(tmp[i][j][1])
						add_spark(div);
				}
			}
		}
		update_rate(false);
	}
	catch(err)
	{
		console.error("Exception thrown", err.stack);
	}
}

function save_settings() // save settings in localstorage
{
	let tmp = [document.getElementById("moon-check").classList.contains("active"), document.getElementById("spark-check").classList.contains("active")];
	localStorage.setItem("gbfal-spark-settings", JSON.stringify(tmp));
}

function load_settings() // load settings from localstorage
{
	try
	{
		let tmp = localStorage.getItem("gbfal-spark-settings");
		if(tmp == null)
			return;
		tmp = JSON.parse(tmp);
		if(tmp[0])
			document.getElementById("moon-check").classList.add("active");
		if(tmp[1])
			document.getElementById("spark-check").classList.add("active");
	}
	catch(err)
	{
		console.error("Exception thrown", err.stack);
	}
}

function spark_reset_results()
{
	for(let k in items)
	{
		items[k].style.display = null;
	}
}

function spark_apply_results(content) // apply the filter
{
	if(content == "") // empty, we reset
	{
		spark_reset_results();
	}
	else
	{
		let search_results = search.get_filtered_results();
		for(let k in items) // hide everything
		{
			items[k].style.display = "none";
		}
		for(let i = 0; i < search_results.length; ++i) // unhide all results
		{
			switch(search_results[i][1])
			{
				case GBFType.character:
				case GBFType.summon:
				{
					if(search_results[i][0] in items)
						items[search_results[i][0]].style.display = null;
					break;
				}
				case GBFType.weapon:
				{
					if(search_results[i][0] in index["premium"])
					{
						const id = index["premium"][search_results[i][0]];
						if(id in items)
							items[id].style.display = null;
					}
					break;
				}
			}
		}
	}
}

function toggle_moon(btn) // toggle moon mode button
{
	beep();
	if(btn.classList.contains("active"))
	{
		btn.classList.remove("active");
	}
	else
	{
		btn.classList.add("active");
		push_popup("Click on a Character to add it to the Moons");
	}
	save_settings();
}

function toggle_spark(btn) // toggle spark mode button
{
	beep();
	if(btn.classList.contains("active"))
	{
	   btn.classList.remove("active");
	}
	else
	{
		btn.classList.add("active");
		push_popup("Click on an Element to add a Sparked icon");
	}
	save_settings();
}

function close_fullscreen() // close fullscreen popups
{
	beep();
	let bgs = document.getElementsByClassName("fullscreen-preview");
	for(let bg of bgs)
		bg.remove();
}

function generate_image() // generate spark canvas
{
	if(canvas_state == 0) // if idle
	{
		beep();
		canvas_state = 1;
		canvas_wait = 0;
		if(canvas != null) // if existing canvas
		{
			display_canvas(canvas);
		}
		else
		{
			canvas = document.createElement("canvas"); // create
			canvas.width = 1920;
			canvas.height = 1080;
			if(canvas.getContext) // check if possible
			{
				push_popup("Generating...");
				draw_spark(canvas);
				display_canvas(canvas);
			}
			else // stop
			{
				push_popup("Unsupported for your browser/system");
				canvas_state = 0;
			}
		}
	}
	else push_popup("Wait before generating another image");
}

/* NOTE
draw_spark is broken into three functions to ensure the draw order is respected (as image loading shuffle everything up), by syncing using the canvas_wait variable
I'm sure there are better wait to do it in javascript but it works so...
*/

function draw_spark(canvas) // draw the spark on the canvas
{
	var ctx = canvas.getContext("2d");
	ctx.imageSmoothingEnabled = true;
	++canvas_wait;
	// background
	ctx.rect(0, 0, 1920, 1080);
	ctx.fillStyle = "#252526";
	ctx.fill();
	// texts
	ctx.font = "40px sans-serif";
	ctx.fillStyle = "#cccccc";
	ctx.fillText(document.getElementById("spark-rate").innerHTML.replace("<br>", " - "), 50, 1070);
	ctx.fillStyle = "#1d1d1d";
	// add source/credit
	ctx.fillText("GBFAL", 1750, 1070);
	// spark target
	let sparked = null;
	for(let i = 0; i < COUNT && sparked == null; ++i)
		for(let j = 0; j < lists[i].length && sparked == null; ++j)
			if(lists[i][j][1].childNodes.length == 2)
					sparked = lists[i][j];
	if(sparked != null)
	{
		ctx.globalAlpha = 0.4; // change opacity
		const s = sparked[1].childNodes[0].src.split('/');
		switch(sparked[0][0])
		{
			case '2':
			{
				draw_image(ctx, "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/b/" + s[s.length-1].replace('.jpg', '.png'), 1920-1100, 0, 1100, 1080);
				break;
			}
			case '3':
			{
				draw_image(ctx, "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/zoom/" + s[s.length-1].replace('.jpg', '.png').replace('_01', '_02'), 30, 0, 1296, 1080);
				break;
			}
		}
	}
	setTimeout(draw_spark_middle, 50, ctx);
}

function draw_spark_middle(ctx) // draw the spark content
{
	if(canvas_state == 2)
		return;
	if(canvas_wait > 1)
	{
		setTimeout(draw_spark_middle, 50, ctx);
		return;
	}
	ctx.globalAlpha = 1; // reset opacity if changed previously
	// content
	let sparkIcon_list = []
	for(let i = 0; i < COUNT; ++i)
	{
		const offset = 640 * i; // horizontal offset (1920 / 3 = 640)
		draw_image(ctx, HEADERS[i], ((640-100)/2) + offset, 50, 100, 100); // draw column header
		sparkIcon_list = sparkIcon_list.concat(draw_column(ctx, offset, lists[i])); // draw column content
	}
	setTimeout(draw_spark_end, 50, ctx, sparkIcon_list);
}

function draw_spark_end(ctx, sparkIcon_list) // draw the spark icons
{
	if(canvas_state == 2)
		return;
	if(canvas_wait > 1)
	{
		setTimeout(draw_spark_end, 50, ctx, sparkIcon_list);
		return;
	}
	// draw spark outlines and icons
	for(let ico of sparkIcon_list)
	{
		ctx.beginPath();
		ctx.lineWidth = 3;
		ctx.strokeStyle = "#3bddf6";
		ctx.rect(ico[0], ico[1], ico[2], ico[3]);
		ctx.stroke();
		ctx.closePath();
		draw_image(ctx, "assets/spark/spark.png", ico[0], ico[1], ico[3]*0.4, ico[3]*0.4);
	}
	// over
	--canvas_wait;
}

function draw_image(ctx, src, x, y, w, h) // draw an image at the specified src url on the canvas
{
	++canvas_wait; // canvas_wait is used like a mutex
	const img = new Image(w, h);
	img.onload = function() {
		ctx.drawImage(this,x,y,w,h);
		--canvas_wait;
	};
	img.onerror = function() {
		canvas_state = 2; // put the process in error state
	};
	img.src = src;
}


function draw_column(ctx, offset, content)
{
	const imgcount = content.length;
	if(imgcount == 0)
		return []; // if no image, stop now
	const RECT_CONTENT = [offset+50, 100+50+50, 640-100, 1080-200-50];
	let size = [RECT_CONTENT[2], RECT_CONTENT[2]*DEFAULT_SIZE[1]/DEFAULT_SIZE[0]]; // default image size (make it fit the area horizontally, keeping the aspect ratio)
	let grid = [0, 0]; // will contain the number of horizontal and vertical elements
	let sparkIcon_list = [];
	// search ideal size
	while(true)
	{
		// calculate how many we can fit horizontally and vertically at the current size
		grid[0] = Math.floor(RECT_CONTENT[2] / size[0]);
		grid[1] = Math.floor(RECT_CONTENT[3] / size[1]);
		if(grid[0]*grid[1] >= imgcount) // if the number we can fix is greater than our current element count...
			break; // we stop
		// else, we reduce the size by 10% and try again
		size[0] *= 0.9;
		size[1] *= 0.9;
	}
	// draw
	let pos = [0, 0];
	let hoff = 0;
	if(imgcount < grid[0]) // horizontal offset calculation
		hoff = (RECT_CONTENT[2] - size[0] * imgcount) / 2;
	else
		hoff = (RECT_CONTENT[2] - size[0] * grid[0]) / 2;
	for(let i = 0; i < imgcount && canvas_state != 2; ++i) // stop if canvas_state enters its error state
	{
		// draw image
		draw_image(ctx, content[i][1].childNodes[0].src.replace('img_low', 'img'), RECT_CONTENT[0]+pos[0]+hoff, RECT_CONTENT[1]+pos[1], size[0], size[1]); // change to /img/ quality
		if(content[i][1].childNodes.length == 2) // add spark icon
			sparkIcon_list.push([RECT_CONTENT[0]+pos[0]+hoff, RECT_CONTENT[1]+pos[1], size[0], size[1]]);
		// update position
		if(pos[0] + size[0] >= RECT_CONTENT[2] - size[0])
		{
			pos[0] = 0;
			pos[1] += size[1];
			if(imgcount - i - 1 < grid[0]) // update offset for last line if needed
				hoff = (RECT_CONTENT[2] - size[0] * (imgcount-i-1)) / 2;
		}
		else
			pos[0] += size[0];
	}
	return sparkIcon_list;
}

function display_canvas(canvas)
{
	if(canvas_state == 2) // if in error mode
	{
		push_popup("A critical error occured");
		canvas_state = 0;
		canvas = null;
		return;
	}
	else if(canvas_wait > 0) // image loading still on going
	{
		setTimeout(display_canvas, 100, canvas); // try again in one second
	}
	else
	{
		push_popup("Complete");
		// prepare canvas to be displayed
		canvas.classList.add("spark-fullscreen");
		// add background
		let div = document.createElement("div");
		div.classList.add("fullscreen-preview");
		add_to(div, "button", {cls:["fullscreen-button"], innertext:"Close", onclick:close_fullscreen
		});
		div.appendChild(canvas);
		add_to(div, "button", {cls:["fullscreen-button"], innertext:"Close", onclick:close_fullscreen
		});
		document.body.appendChild(div);
		push_popup("Right Click / Hold Touch, then Save as...");
		canvas_state = 0;
	}
}