/*jshint esversion: 11 */
const CanvasState = Object.freeze({
	IDLE: 0,
	RUNNING: 1,
	DONE: 2,
	ERROR: 3
});
const CanvasSize = Object.freeze({
	W: 1920,
	H: 1080
});
const CanvasTextColor = Object.freeze({
	LIGHT: "#cccccc",
	DARK: "#333333"
});
const SparkMode = Object.freeze({
	UNDEF: -1,
	NPC: 0,
	MOON: 1,
	STONE: 2,
	COUNT: 3
});
const DragState = Object.freeze({
	IDLE: 0,
	CHECKING: 1,
	RUNNING: 2
});
var search = null;
var timestamp = Date.now();
var index = null;
var items = {};
var lists = [[], [], []];
var spark_container = null;
var spark_sections = null;
const DEFAULT_SIZE = [140, 80];
var resize_timer = null;
// image generation
const HEADERS = ["assets/jpg/spark/gem.jpg", "assets/jpg/spark/moon.jpg", "assets/jpg/spark/sunstone.jpg"];
const SPARK_ICON = "assets/webp/spark/spark.webp";
var canvas_area = null; // contains the area where the canvas is displayed
var canvas = null; // contains the canvas
var canvas_state = CanvasState.IDLE;
const CACHE_LIMIT = 50;
var canvas_cache = {}; // image cache
var canvas_color = "#252526";
var canvas_text_color = CanvasTextColor.LIGHT;
var canvas_opacity = 1;
var canvas_target_opacity = 0.4;
var canvas_target_h_position = 0.3;
var canvas_target_v_position = 0.5;
var canvas_displayed = false;
// drag and drop
var drag_state = DragState.IDLE; // 0 = not running, 1 = drag check, 2 = running
var drag_event = null; // contains the last event received to process
var drag_original_div = null; // the div that the user clicked on when dragging
var drag_placeholder_div = null; // placeholder div that is displayed to the user during drag-and-drop
var drag_id = null; // the ID of the character or summon that is being dragged
var drag_is_spark = null; // whether the dragged element is sparked or not
var drag_mode = SparkMode.UNDEF; // the mode (NPC/MOON/STONE) of the currently dragged item
var drag_position = null; // the position of the currently dragged item
var drag_coords = {x:0, y:0}; // pointer coordinates
var drag_is_complete = true; // whether the last drag event was completed successfully
var drag_ghost = null; // container of a "ghost" of the dragged image

var jukebox = null;

function init() // entry point, called by body onload
{
	spark_container = document.getElementById("spark-container");
	spark_sections = document.querySelectorAll(".spark-section");
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
		const node = document.getElementById("jukebox");
		jukebox = new AudioJukeboxPlayer(node, value);
	});
}

function start(changelog)
{
	search = new Search(
		document.getElementById("spark-filter"),
		{
			search_filters:{
				"wpn":["", GBFType.weapon],
				"sum":["", GBFType.summon],
				"cha":["", GBFType.character]
			},
			simple_search:true
		}
	);
	// add search event listeners
	document.addEventListener('search-update', () => {
		spark_apply_results(document.getElementById('spark-filter').value.trim().toLowerCase());
	});
	document.addEventListener('search-clear', () => {
		spark_reset_results();
	});
	// add Shift-Tab listener
	const btn_npc = document.getElementById("spark-tab-btn-npc");
	const btn_summon = document.getElementById("spark-tab-btn-summon");
	document.addEventListener(
		"keydown",
		(event) => {
			if(event.shiftKey && event.key == "Tab")
			{
				if(btn_summon.classList.contains("active"))
				{
					btn_npc.click();
				}
				else
				{
					btn_summon.click();
				}
				event.stopPropagation();
				event.preventDefault();
			}
		}
	);
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
		{
			btn.classList.remove("active");
		}
	}
	for(let sel of document.getElementsByClassName("spark-select"))
	{
		sel.style.display = "none";
	}
	document.getElementById("spark-select-" + tabName).style.display = "";
	document.getElementById("spark-tab-btn-"+tabName).classList.add("active");
}

function default_onerror() // overwrite definition
{
	this.parentNode.remove();
}

function is_valid_mode(cid, mode, gbtype)
{
	if(
		(gbtype == GBFType.summon && mode != SparkMode.STONE)
		|| (gbtype != GBFType.summon && mode == SparkMode.STONE)
	)
	{
		return false;
	}
	return true;
}

function set_spark_list()
{
	// for each characters
	let node = document.getElementById('spark-select-npc');
	let frag = document.createDocumentFragment();
	const ckeys = Object.keys(index["characters"]).sort().reverse();
	if(ckeys.length > 0) // add more non-indexed characters first, so that the user got recent stuff in all scenarios
	{
		const highest = parseInt(ckeys[0]);
		for(let i = 5; i > 0; --i)
		{
			const id = JSON.stringify(highest + i * 1000);
			const ret = get_character(id, null, [-1, -1, -1, -1, 0, 1000]);
			if(ret != null)
			{
				items[id] = add_image_spark(frag, ret[0], GBFType.character); // display and memorize in items
			}
		}
	}
	for(const id of ckeys)
	{
		if(id in index["lookup"] && !(id in index["premium"]) && ckeys.indexOf(id) > 5)
		{
			continue; // exclude non gacha characters (unless not in lookup = it's recent)
		}
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
	const skeys = Object.keys(index["summons"]).sort().reverse();
	if(skeys.length > 0) // add more non-indexed summons first, so that the user got recent stuff in all scenarios
	{
		const highest = parseInt(skeys[0]);
		for(let i = 5; i > 0; --i)
		{
			const id = JSON.stringify(highest + i * 1000);
			const ret = get_summon(id, null, "4", [0, 1000]);
			if(ret != null)
			{
				items[id] = add_image_spark(frag, ret[0], GBFType.summon); // display and memorize in items
			}
		}
	}
	for(const id of skeys)
	{
		if(id in index["lookup"] && !(id in index["premium"]) && skeys.indexOf(id) > 5)
		{
			continue; // exclude non gacha summons (unless not in lookup = it's recent)
		}
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
	const container = document.createElement("div");
	container.classList.add("spark-image-container");
	
	const img = document.createElement("img");
	img.dataset.id = data.id;
	img.draggable = false; // important for event interaction
	img.gbtype = gbtype;
	img.classList.add("loading");
	img.classList.add("spark-image");
	img.setAttribute('loading', 'lazy');
	if(data.onerr == null)
	{
		img.onerror = default_onerror;
	}
	else
	{
		img.onerror = data.onerr;
	}
	const cid = data.id;
	img.onload = (event) => {
		img.classList.remove("loading");
		container.classList.add("clickable");
		if(gbf && index.lookup && data.id in index.lookup && index.lookup[data.id].includes("/n"))
		{
			img_text.innerText = gbf.get_lookup_names(data.id)[0].replace(" (SSR)", "");
			img.title = img_text.innerText;
			let char_len = img.title.length;
			
			if(data.id in index["premium"])
			{
				const id = index["premium"][data.id];
				if(id in index.lookup && index.lookup[id].includes("/n"))
				{
					const wpn_name = gbf.get_lookup_names(id)[0];
					img_text.innerHTML = img_text.innerText + "<br>" + wpn_name;
					char_len = Math.max(char_len, wpn_name.length);
				}
			}
			if(char_len > 15)
			{
				img_text.classList.add("spark-image-cycling-text");
			}
			else
			{
				img_text.classList.add("spark-image-text");
			}
		}
		else
		{
			img.title = data.id;
			img_text.innerText = "???";
			img_text.classList.add("spark-image-text");
		}
		container.onclick = () => {
			if(canvas_state == CanvasState.RUNNING) // if canvas processing
			{
				push_popup("Wait for the image to be processed");
			}
			else
			{
				result_clean();
				beep();
				if(
					img.gbtype == GBFType.character
					&& (
						window.event.shiftKey
						|| document.getElementById("moon-check").classList.contains("active")
					)
				) // add to moon
				{
					add_image_result_spark(SparkMode.MOON, cid, img);
				}
				else
				{
					add_image_result_spark(
						img.gbtype == GBFType.summon
						? SparkMode.STONE
						: SparkMode.NPC,
						cid,
						img
					); // add to npc or stone
				}
				spark_container.scrollIntoView(); // recenter view
				spark_save_settings();
			}
		};
	};
	img.src = data.path.replace("GBF/", gbf.endpoint());
	container.appendChild(img);
	
	const img_text_wrap = document.createElement("div");
	img_text_wrap.classList.add("spark-image-text-wrapper");
	container.appendChild(img_text_wrap);
	
	const img_text = document.createElement("div");
	img_text_wrap.appendChild(img_text);
	
	node.appendChild(container);
	return img;
}

function remove_image_result_spark(div) // remove image from the spark result
{
	for(let mode = 0; mode < SparkMode.COUNT; ++mode)
	{
		for(let i = 0; i < lists[mode].length; ++i) // look for it and remove
		{
			if(div === lists[mode][i][1])
			{
				lists[mode].splice(i, 1);
				div.remove();
				update_spark_result_size(mode);
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
		case SparkMode.NPC: node = document.getElementById("spark-npc"); break;
		case SparkMode.MOON: node = document.getElementById("spark-moon"); break;
		case SparkMode.STONE: node = document.getElementById("spark-summon"); break;
		default: return;
	}
	const div = document.createElement("div");
	div.dataset.id = id;
	div.draggable = false;
	div.spark_draggable = true;
	div.classList.add("spark-result");
	div.onclick = () => {
		if(canvas_state == CanvasState.RUNNING) // if canvas processing
		{
			push_popup("Wait for the image to be processed");
		}
		else
		{
			result_clean();
			beep();
			if(window.event.shiftKey || document.getElementById("spark-check").classList.contains("active")) // toggle spark icon
			{
				toggle_spark_state(div);
				update_rate(false);
			}
			else
			{
				remove_image_result_spark(div);
			}
			spark_save_settings();
			
		}
	};
	const cmode = mode;
	const img = document.createElement("img");
	img.draggable = false; // important  for event interaction
	img.classList.add("spark-result-img");
	img.src = base_img.src;
	img.onerror = base_img.onerror;
	div.appendChild(img);

	if(position === undefined)
	{
		position = lists[mode].length;
	}
	node.insertBefore(div, node.children[position]);
	lists[mode].splice(position, 0, [id, div]);

	update_spark_result_size(mode);
	return div;
}

function toggle_spark_state(div) // toggle spark icon
{
	if(div.classList.contains("sparked"))
	{
		remove_spark(div);
	}
	else
	{
		add_spark(div);
	}
}

function add_spark(div) // add spark icon
{
	if(div.classList.contains("sparked"))
	{
		return;
	}
	const img = document.createElement("img");
	img.classList.add("spark-icon");
	img.draggable = false;
	img.src = "assets/webp/spark/spark.webp";
	div.appendChild(img);
	div.classList.add("sparked");
}

function remove_spark(div) // remove spark icon
{
	if(!div.classList.contains("sparked"))
	{
		return;
	}
	div.removeChild(div.childNodes[1]);
	div.classList.remove("sparked");
}

addEventListener("resize", (event) => { // capture window resize event and call update_all_spark_result_size() (after 300ms)
	if(resize_timer != null)
	{
		clearTimeout(resize_timer);
	}
	resize_timer = setTimeout(update_all_spark_result_size, 300);
});

function init_drag_and_drop()
{
	// general drag events
	document.addEventListener("pointerdown", handle_dragstart);
	document.addEventListener("pointercancel", handle_dragstop);
}

function find_target(base_target)
{
	// for pointer events,
	// event.target sometimes catch the underlying image
	return (
		(
			base_target.classList.contains("spark-result-img") ||
			base_target.classList.contains("spark-icon")
		) ?
		base_target.parentNode : // catch the parent div
		base_target
	);
}

function handle_dragstart(event)
{
	if(drag_state != DragState.IDLE) // don't start if already on going
	{
		return;
	}
	const target = find_target(event.target);
	if(target.spark_draggable !== true || target.classList.contains("loading"))
	{
		return;
	}
	if(canvas_state == CanvasState.RUNNING) // if canvas processing
	{
		push_popup("Wait for the image to be processed");
	}
	else
	{
		// get and check id
		drag_id = target.dataset.id;
		if(!(drag_id in items))
		{
			return;
		}
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
					case "spark-npc": mode = SparkMode.NPC; break;
					case "spark-moon": mode = SparkMode.MOON; break;
					case "spark-summon": mode = SparkMode.STONE; break;
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
		drag_state = DragState.CHECKING;
		drag_is_complete = false;
		drag_coords.x = event.clientX;
		drag_coords.y = event.clientY;
		drag_ghost = null;
		// enable listeners
		document.addEventListener("pointermove", handle_dragmove);
		document.addEventListener("pointerup", handle_dragend);
	}
}

// finish initialization of dragging system
// called by handle_dragmove
function handle_draginit(event)
{
	if(drag_state != DragState.CHECKING)
	{
		return;
	}
	// initialize dragging
	drag_state = DragState.RUNNING;
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
		// note: No need for update_spark_result_size()
	}
	// add the highlight
	const drag_highlight_range = (
		items[drag_id].gbtype == GBFType.summon ?
		[2, 3] : 	// stone
		[0, 2]		// npc, moon
	);
	for(let i = drag_highlight_range[0]; i < drag_highlight_range[1]; ++i)
	{
		spark_sections[i].classList.toggle("spark-section-highlight", true);
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
		{
			break;
		}
		else if(event.clientY < rect.bottom && event.clientX < rect.left)
		{
			break;
		}
		position = i;
	}
	return position;
}

// return the section we're hovering, or null
function find_section(event)
{
	if(drag_ghost)
	{
		drag_ghost.style.display = 'none';
	}
    const targetBelow = document.elementFromPoint(event.clientX, event.clientY);
	if(drag_ghost)
	{
		drag_ghost.style.display = null;
	}
    if(!targetBelow)
	{
		return null;
	}
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
	if(drag_state != DragState.RUNNING)
	{
		return;
	}
	if(!event.clientX && !event.clientY)
	{
		return;
	}
	// only update if moved
	if(event.clientX == drag_coords.x && event.clientY == drag_coords.y)
	{
		return;
	}
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
			case "spark-npc": mode = SparkMode.NPC; break;
			case "spark-moon": mode = SparkMode.MOON; break;
			case "spark-summon": mode = SparkMode.STONE; break;
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
			update_spark_result_size(drag_mode);
			drag_mode = SparkMode.UNDEF;
			drag_position = -1;
		}
		return;
	}
	// find position
	const position = find_position(section, event);
	// and check if it changed
	if(drag_mode === mode && drag_position === position)
	{
		return;
	}
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
		update_spark_result_size(drag_mode);
	}
	// update mode and position
	drag_mode = mode;
	drag_position = position;
	// set new placeholder
	drag_placeholder_div = add_image_result_spark(mode, drag_id, img, drag_position);
	drag_placeholder_div.classList.add("placeholder");
	if(drag_is_spark)
	{
		add_spark(drag_placeholder_div);
	}
	update_spark_result_size(drag_mode);
	update_rate(false);
}

// triggered when moving the mouse
function handle_dragmove(event)
{
	if(drag_state == DragState.IDLE)
	{
		return;
	}
	if(!(event.target instanceof HTMLElement))
	{
		return;
	}
	if(canvas_state != CanvasState.IDLE) // if canvas processing
	{
		return;
	}
	event.preventDefault();
	if(drag_state === DragState.CHECKING)
	{
		const delta = {
				x: Math.abs(event.clientX - drag_coords.x),
				y: Math.abs(event.clientY - drag_coords.y)
		};
		// check for accidental drags
		// by looking for a movement of more than 5px
		if(delta.x + delta.y > 5)
		{
			handle_draginit(event);
		}
		else return;
	}
	queue_drag_state(event);
}

// triggered when releasing the mouse
function handle_dragend(event, allow_beep = true)
{
	if(drag_state == DragState.IDLE)
	{
		return;
	}
	if(drag_ghost)
	{
		drag_ghost.remove();
	}
	drag_ghost = null;
	// flag to check if we dragging went through
	const process_drag = canvas_state == CanvasState.IDLE && drag_state == DragState.RUNNING;
	// remove listeners
	document.removeEventListener("pointermove", handle_dragmove);
	document.removeEventListener("pointerup", handle_dragend);
	if(process_drag && drag_mode != SparkMode.UNDEF)
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
				if(drag_is_spark)
				{
					add_spark(div);
				}
				drag_is_complete = true;
			}
		}
	}
	// remove or restore original div
	if(drag_original_div)
	{
		if(drag_is_complete || drag_mode == SparkMode.UNDEF)
		{
			remove_image_result_spark(drag_original_div);
			drag_is_complete = true; // for the beep below
		}
		else
		{
			drag_original_div.style.display = null;
		}
	}
	if(drag_is_complete && allow_beep)
	{
		beep();
	}
	handle_dragstop();
	// update and save
	update_rate(false);
	spark_save_settings();
}

// the drag system stop and reset function
function handle_dragstop()
{
	if(drag_state == DragState.IDLE)
	{
		return;
	}
	if(drag_ghost)
	{
		drag_ghost.remove();
	}
	drag_ghost = null;
	// remove placeholder
	if(drag_placeholder_div)
	{
		remove_image_result_spark(drag_placeholder_div);
		drag_placeholder_div = null;
	}
	// reset everything else
	drag_state = DragState.IDLE;
	drag_coords = {x:0, y:0};
	drag_original_div = null;
	drag_placeholder_div = null;
	drag_id = null;
	drag_is_spark = null;
	drag_mode = SparkMode.UNDEF;
	drag_position = null;
	for(let i = 0; i < spark_sections.length; ++i)
	{
		spark_sections[i].classList.toggle("spark-section-highlight", false);
		spark_sections[i].classList.toggle("spark-section-highlight-enabled", false);
	}
	update_all_spark_result_size();
}

function update_all_spark_result_size() // update all three columns
{
	clearTimeout(resize_timer);
	resize_timer = null;
	update_spark_result_size(SparkMode.NPC);
	update_spark_result_size(SparkMode.MOON);
	update_spark_result_size(SparkMode.STONE);
}

function count_visible_nodes(list)
{
	let count = 0;
	for(let i = 0; i < list.length; ++i)
	{
		if(list[i].style.display != "none")
		{
			++count;
		}
	}
	return count;
}

function update_spark_result_size(mode) // update spark column
{
	let node;
	switch(mode)
	{
		case SparkMode.NPC: node = document.getElementById("spark-npc"); break;
		case SparkMode.MOON: node = document.getElementById("spark-moon"); break;
		case SparkMode.STONE: node = document.getElementById("spark-summon"); break;
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
	if(canvas_state == CanvasState.RUNNING) // if canvas processing
	{
		push_popup("Wait for the image to be processed");
	}
	else
	{
		result_clean();
		let v;
		try
		{
			v = parseInt(document.getElementById("spark-roll-input").value);
			if(isNaN(v) || v <= 0) v = 300;
			let c = 0; // total ssr count
			let s = 0; // sparked
			for(let i = 0; i < SparkMode.COUNT; ++i)
			{
				for(let j = 0; j < lists[i].length; ++j)
				{
					if(lists[i][j][1].style.display != "none")
					{
						if(lists[i][j][1].childNodes.length == 2) ++s;
						else ++c;
					}
				}
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
	if(canvas_state == CanvasState.RUNNING) // if canvas processing
	{
		push_popup("Wait for the image to be processed");
	}
	else
	{
		const div = document.createElement("div");
		div.classList.add("fullscreen-preview");
		const cont = add_to(div, "div", {cls:["spark-delete-confirm"]});
		add_to(
			cont,
			"div",
			{
				cls:["fullscreen-prompt"],
				innertext:"Are you certain that you want to reset the spark screen?"
			}
		);
		add_to(
			cont,
			"button",
			{
				cls:["std-button"],
				innertext:"Yes",
				onclick:() => {
					div.remove();
					spark_clear();
				}
			}
		);
		add_to(
			cont,
			"button",
			{
				cls:["std-button"],
				innertext:"No",
				onclick:() => {
					div.remove();
				}
			}
		);
		document.body.appendChild(div);
	}
}

function spark_clear() // clear everything
{
	result_clean();
	localStorage.removeItem('gbfal-spark');
	lists = [[], [], []];
	for(let i = 0; i < SparkMode.COUNT; ++i)
	{
		let node;
		switch(i)
		{
			case SparkMode.NPC: node = document.getElementById("spark-npc"); break;
			case SparkMode.MOON: node = document.getElementById("spark-moon"); break;
			case SparkMode.STONE: node = document.getElementById("spark-summon"); break;
			default: continue;
		}
		node.innerHTML = "";
	}
	document.getElementById("spark-roll-input").value = 300;
	update_all_spark_result_size();
	update_rate(false);
}

function spark_save_settings() // save spark in localstorage
{
	let tmp = [[], [], [], document.getElementById("spark-roll-input").value];
	for(let i = 0; i < SparkMode.COUNT; ++i)
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
		if(tmp[SparkMode.COUNT] != undefined)
		{
			document.getElementById("spark-roll-input").value = tmp[SparkMode.COUNT];
		}
		lists = [[], [], []];
		for(let i = 0; i < SparkMode.COUNT; ++i)
		{
			let node;
			switch(i)
			{
				case SparkMode.NPC: node = document.getElementById("spark-npc"); break;
				case SparkMode.MOON: node = document.getElementById("spark-moon"); break;
				case SparkMode.STONE: node = document.getElementById("spark-summon"); break;
				default: continue;
			}
			for(let j = 0; j < tmp[i].length; ++j)
			{
				if(tmp[i][j][0] in items)
				{
					const div = add_image_result_spark(i, tmp[i][j][0], items[tmp[i][j][0]]);
					if(tmp[i][j][1])
					{
						add_spark(div);
					}
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
	const tmp = [
		document.getElementById("moon-check").classList.contains("active"),
		document.getElementById("spark-check").classList.contains("active")
	];
	localStorage.setItem("gbfal-spark-settings", JSON.stringify(tmp));
}

function load_settings() // load settings from localstorage
{
	try
	{
		let tmp = localStorage.getItem("gbfal-spark-settings");
		if(tmp == null)
		{
			return;
		}
		tmp = JSON.parse(tmp);
		if(tmp[0])
		{
			document.getElementById("moon-check").classList.add("active");
		}
		if(tmp[1])
		{
			document.getElementById("spark-check").classList.add("active");
		}
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
		items[k].parentNode.style.display = null;
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
			items[k].parentNode.style.display = "none";
		}
		for(let i = 0; i < search_results.length; ++i) // unhide all results
		{
			switch(search_results[i][1])
			{
				case GBFType.character:
				case GBFType.summon:
				{
					if(search_results[i][0] in items)
					{
						items[search_results[i][0]].parentNode.style.display = null;
					}
					break;
				}
				case GBFType.weapon:
				{
					if(search_results[i][0] in index["premium"])
					{
						const id = index["premium"][search_results[i][0]];
						if(id in items)
						{
							items[id].parentNode.style.display = null;
						}
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

function result_init()
{
	// create the canvas
	canvas = document.createElement("canvas");
	canvas.width = CanvasSize.W;
	canvas.height = CanvasSize.H;
	// prepare canvas to be displayed
	canvas.classList.add("spark-fullscreen");
	// add background
	canvas_area = document.createElement("div");
	canvas_area.classList.add("fullscreen-preview");
	add_to(canvas_area, "button", {cls:["fullscreen-button"], innertext:"Close", onclick:result_close});
	canvas_area.appendChild(canvas);
	// spark result editing
	const controls = add_to(canvas_area, "div", {cls:["spark-result-controls"]});
	// bg color
	let row = add_to(controls, "div", {cls:["spark-result-control-row"]});
	add_to(row, "label", {cls:["spark-result-label"], innertext:"Background Color"}).htmlFor = "spark-bg-color";
	const bg_color = add_to(row, "input", {cls:["std-button"], id:"spark-bg-color"});
	bg_color.style.verticalAlign = "middle";
	bg_color.type = "color";
	bg_color.value = canvas_color;
	bg_color.onchange = () => {
		canvas_color = bg_color.value;
		// compute text color
		const hex = canvas_color.replace('#', '');
		const r = parseInt(hex.substring(0, 2), 16);
		const g = parseInt(hex.substring(2, 4), 16);
		const b = parseInt(hex.substring(4, 6), 16);
		// YIQ equation
		const yiq = (r * 299 + g * 587 + b * 114) / 1000;
		canvas_text_color = yiq >= 128 ? CanvasTextColor.DARK : CanvasTextColor.LIGHT;
		// update
		result_compute();
	};
	// bg opacity
	row = add_to(controls, "div", {cls:["spark-result-control-row"]});
	add_to(row, "label", {cls:["spark-result-label"], innertext:"Background Opacity"}).htmlFor = "spark-bg-opacity";
	const bg_opacity = add_to(row, "input", {
		cls:["spark-result-slider"],
		id:"spark-bg-opacity"
	});
	bg_opacity.type = "range";
	bg_opacity.min = "0";
	bg_opacity.max = "100";
	bg_opacity.value = "" + canvas_opacity * 100;
	bg_opacity.onchange = () => {
		canvas_opacity = parseInt(bg_opacity.value) / 100.0;
		result_compute();
	};
	// target opacity
	row = add_to(controls, "div", {cls:["spark-result-control-row"]});
	add_to(row, "label", {cls:["spark-result-label"], innertext:"Spark Target Opacity"}).htmlFor = "spark-target-opacity";
	const spk_opacity = add_to(row, "input", {
		cls:["spark-result-slider"],
		id:"spark-target-opacity"
	});
	spk_opacity.type = "range";
	spk_opacity.min = "0";
	spk_opacity.max = "100";
	spk_opacity.value = "" + canvas_target_opacity * 100;
	spk_opacity.onchange = () => {
		canvas_target_opacity = parseInt(spk_opacity.value) / 100.0;
		result_compute();
	};
	// target horizontal position
	row = add_to(controls, "div", {cls:["spark-result-control-row"]});
	add_to(row, "label", {cls:["spark-result-label"], innertext:"Spark Target H. Position"}).htmlFor = "spark-target-h-position";
	const spk_h_position = add_to(row, "input", {
		cls:["spark-result-slider"],
		id:"spark-target-h-position"
	});
	spk_h_position.type = "range";
	spk_h_position.min = "0";
	spk_h_position.max = "100";
	spk_h_position.value = "" + canvas_target_h_position * 100;
	spk_h_position.onchange = () => {
		canvas_target_h_position = parseInt(spk_h_position.value) / 100.0;
		result_compute();
	};
	// target vertical position
	row = add_to(controls, "div", {cls:["spark-result-control-row"]});
	add_to(row, "label", {cls:["spark-result-label"], innertext:"Spark Target V. Position"}).htmlFor = "spark-target-v-position";
	const spk_v_position = add_to(row, "input", {
		cls:["spark-result-slider"],
		id:"spark-target-v-position"
	});
	spk_v_position.type = "range";
	spk_v_position.min = "0";
	spk_v_position.max = "100";
	spk_v_position.value = "" + canvas_target_v_position * 100;
	spk_v_position.onchange = () => {
		canvas_target_v_position = parseInt(spk_v_position.value) / 100.0;
		result_compute();
	};
	// end of controls
	add_to(canvas_area, "button", {cls:["fullscreen-button"], innertext:"Close", onclick:result_close});
}

function result_close() // close result area
{
	beep();
	canvas_area.remove();
	canvas_displayed = false;
}

function generate_image() // generate spark canvas
{
	if(canvas_state != CanvasState.RUNNING)
	{
		beep();
		canvas_state = CanvasState.RUNNING;
		if(canvas_state == CanvasState.DONE)
		{
			result_display();
		}
		else
		{
			if(canvas_area == null)
			{
				result_init();
			}
			if(canvas.getContext) // check if possible
			{
				push_popup("Generating...");
				result_start_draw();
			}
			else // stop
			{
				push_popup("Unsupported for your browser/system");
				canvas_state = CanvasState.IDLE;
			}
		}
	}
	else push_popup("Wait before generating another image");
}

function result_clean()
{
	if(canvas_displayed)
	{
		return;
	}
	canvas_state = CanvasState.IDLE;
	// cache cleanups
	const keys = Object.keys(canvas_cache);
	if(keys.length > CACHE_LIMIT)
	{
		for(const k of keys)
		{
			if(!HEADERS.includes(k) && k != SPARK_ICON)
			{
				delete canvas_cache[k];
			}
		}
	}
	else if("sparked" in canvas_cache)
	{
		delete canvas_cache["sparked"];
	}
}

function load_images(sources)
{
    // Map each url to a promise
    const promises = sources.map(src => {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
				resolve(img);
				canvas_cache[src] = img;
			};
            img.onerror = () => reject(new Error(`Failed to load image: ${src}`));
            img.src = src;
        });
    });
    // wait all
    return Promise.all(promises);
}

function result_start_draw()
{
	// loading images
	let sparked = null;
	let sources = new Set();
	for(let i = 0; i < SparkMode.COUNT; ++i)
	{
		for(let j = 0; j < lists[i].length; ++j)
		{
			const src = lists[i][j][1].childNodes[0].src.replace("img_low", "img");
			// regular image
			if(!(src in canvas_cache))
			{
				sources.add(src);
			}
			if(sparked == null && lists[i][j][1].childNodes.length == 2)
			{
				// childNodes.length == 2 because the spark indicator adds a second element
				const s = src.split("/");
				switch(i)
				{
					case SparkMode.NPC:
					case SparkMode.MOON:
					{
						sparked = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/zoom/" + s[s.length-1].replace(".jpg", ".png");
						break;
					}
					case SparkMode.STONE:
					{
						sparked = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/b/" + s[s.length-1].replace(".jpg", ".png");
						break;
					}
					default:
					{
						continue;
					}
				}
				if(!(sparked in canvas_cache))
				{
					sources.add(sparked);
				}
			}
		}
	}
	// convert to array
	sources = Array.from(sources);
	// load used icons
	if(sources.length > 0)
	{
		for(const header_img of HEADERS)
		{
			if(!(header_img in canvas_cache))
			{
				sources.push(header_img);
			}
		}
		if(!(SPARK_ICON in canvas_cache))
		{
			sources.push(SPARK_ICON);
		}
	}
	else
	{
		push_popup("Please add some elements first");
		canvas_state = CanvasState.IDLE;
		return;
	}
	load_images(sources).then(() => {
		// set sparked
		if(sparked != null)
		{
			canvas_cache["sparked"] = canvas_cache[sparked];
		}
		else if("sparked" in canvas_cache)
		{
			delete canvas_cache["sparked"];
		}
		result_compute();
		result_display();
	}).catch((err) => {
		console.error("An error occurred while loading images:", err);
		push_popup("A critical error occured");
		result_clean();
		canvas_state = CanvasState.ERROR;
	});
}

function result_compute()
{
	const ctx = canvas.getContext("2d");
	ctx.imageSmoothingEnabled = true;
	// clean
	ctx.clearRect(0, 0, CanvasSize.W, CanvasSize.H);
	// background
	ctx.globalAlpha = canvas_opacity;
	ctx.rect(0, 0, CanvasSize.W, CanvasSize.H);
	ctx.fillStyle = canvas_color;
	ctx.fill();
	ctx.globalAlpha = 1;
	// add sparked target
	if("sparked" in canvas_cache)
	{
		ctx.globalAlpha = canvas_target_opacity; // change opacity
		const img = canvas_cache["sparked"];
		const w = img.naturalWidth * CanvasSize.H / img.naturalHeight;
		const x = canvas_target_h_position * CanvasSize.W - w / 2;
		const y = canvas_target_v_position * CanvasSize.H - CanvasSize.H / 2
		draw_image(ctx, img, x, y, w, CanvasSize.H);
		ctx.globalAlpha = 1; // back to normal
	}
	// texts
	ctx.font = "40px sans-serif";
	ctx.fillStyle = canvas_text_color;
	ctx.fillText(document.getElementById("spark-rate").innerHTML.replace("<br>", " - "), 50, 1070);
	// draw elements
	for(let i = 0; i < SparkMode.COUNT; ++i)
	{
		const offset = 640 * i; // horizontal offset (CanvasSize.W / 3 = 640)
		draw_image(ctx, canvas_cache[HEADERS[i]], ((640-100)/2) + offset, 50, 100, 100); // draw column header
		const sparks = draw_column(ctx, offset, lists[i]);
		// spark indicators
		for(const spk of sparks)
		{
			ctx.beginPath();
			ctx.lineWidth = 3;
			ctx.strokeStyle = "#3bddf6";
			ctx.rect(spk[0], spk[1], spk[2], spk[3]);
			ctx.stroke();
			ctx.closePath();
			draw_image(ctx, canvas_cache[SPARK_ICON], spk[0], spk[1], spk[3] * 0.4, spk[3] * 0.4);
		}
	}
}

function result_display()
{
	if(canvas_state == CanvasState.ERROR) // if in error mode
	{
		push_popup("A critical error occured");
		result_clean();
		return;
	}
	canvas_state = CanvasState.DONE;
	document.body.appendChild(canvas_area);
	push_popup("Right Click / Hold Touch, then Save as...");
	canvas.scrollIntoView();
	canvas_displayed = true;
}

function draw_image(ctx, img, x, y, w, h) // draw an image on the canvas
{
	if(img instanceof HTMLImageElement)
	{
		ctx.drawImage(img, x, y, w, h);
	}
	else
	{
		console.error("Unknown element", img);
	}
}

function draw_column(ctx, offset, content)
{
	const imgcount = content.length;
	if(imgcount == 0)
	{
		return []; // if nothing to draw, stop now
	}
	const RECT_CONTENT = [offset+50, 100+50+50, 640-100, CanvasSize.H-200-50];
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
		{
			break; // we stop
		}
		// else, we reduce the size by 10% and try again
		size[0] *= 0.9;
		size[1] *= 0.9;
	}
	// draw
	let pos = [0, 0];
	let hoff = 0;
	if(imgcount < grid[0]) // horizontal offset calculation
	{
		hoff = (RECT_CONTENT[2] - size[0] * imgcount) / 2;
	}
	else
	{
		hoff = (RECT_CONTENT[2] - size[0] * grid[0]) / 2;
	}
	// stop if canvas_state enters its error state
	for(let i = 0; i < imgcount && canvas_state != CanvasState.ERROR; ++i)
	{
		// draw image
		const src = content[i][1].childNodes[0].src.replace('img_low', 'img');
		draw_image(ctx, canvas_cache[src], RECT_CONTENT[0]+pos[0]+hoff, RECT_CONTENT[1]+pos[1], size[0], size[1]); // change to /img/ quality
		if(content[i][1].childNodes.length == 2) // add spark icon
		{
			sparkIcon_list.push([RECT_CONTENT[0]+pos[0]+hoff, RECT_CONTENT[1]+pos[1], size[0], size[1]]);
		}
		// update position
		if(pos[0] + size[0] >= RECT_CONTENT[2] - size[0])
		{
			pos[0] = 0;
			pos[1] += size[1];
			if(imgcount - i - 1 < grid[0]) // update offset for last line if needed
			{
				hoff = (RECT_CONTENT[2] - size[0] * (imgcount-i-1)) / 2;
			}
		}
		else
		{
			pos[0] += size[0];
		}
	}
	return sparkIcon_list;
}