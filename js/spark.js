/*jshint esversion: 11 */

var gbf = null;
var timestamp = Date.now();
var index = null;
var items = {};
var lists = [[], [], []];
var sizes = [null, null, null];
const NPC = 0;
const MOON = 1;
const STONE = 2;
const COUNT = 3;
const HEIGHT = 50;
const DEFAULT_SIZE = [140, 80];
var resize_timer = null;
// image generation stuff
const HEADERS = ["assets/spark/gem.jpg", "assets/spark/moon.jpg", "assets/spark/sunstone.jpg"];
var canvas = null; // contains last canvas
var canvas_state = 0; // 0 = not running, 1 = running, 2 = error
var canvas_wait = 0; // used to track pending loadings

function init() // entry point, called by body onload
{
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
		setInterval(clock, 1000); // start the clock
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
	init_search_lookup();
	set_spark_list();
	load_spark();
	load_setting();
	document.getElementById("spark-container").scrollIntoView();
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
				items[id] = add_image_spark(frag, ret[0]); // display and memorize in items
			}
		}
	}
	for(const id of ckeys)
	{
		if(id in index["lookup"] && !(id in index["premium"]) && ckeys.indexOf(id) > 5) continue; // exclude non gacha characters (unless not in lookup = it's recent)
		const ret = get_character(id, (index["characters"][id] !== 0 ? index["characters"][id] : null), [-1, -1, -1, -1, 0, 1000]);
		if(ret != null)
		{
			items[id] = add_image_spark(frag, ret[0]); // display and memorize in items
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
				items[id] = add_image_spark(frag, ret[0]); // display and memorize in items
			}
		}
	}
	for(const id of skeys)
	{
		if(id in index["lookup"] && !(id in index["premium"]) && skeys.indexOf(id) > 5) continue; // exclude non gacha summons (unless not in lookup = it's recent)
		const ret = get_summon(id, (index["summons"][id] !== 0 ? index["summons"][id] : null), "4", [0, 1000]);
		if(ret != null)
		{
			items[id] = add_image_spark(frag, ret[0]); // display and memorize in items
		}
	}
	node.appendChild(frag);
}

function add_image_spark(node, data) // add an image to the selector
{
	let img = document.createElement("img");
	img.title = data.id;
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
	const isSummon = data.id.startsWith("20");
	const cid = data.id;
	img.onload = function() {
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
				if(!isSummon && (window.event.shiftKey || document.getElementById("moon-check").classList.contains("active"))) // add to moon
				{
					add_image_result_spark(MOON, cid, this);
				}
				else
				{
					add_image_result_spark(isSummon ? STONE : NPC, cid, this); // add to npc or stone
				}
				document.getElementById("spark-container").scrollIntoView(); // recenter view
				saveSpark();
			}
		};
	};
	img.src = data.path.replace("GBF/", gbf.id_to_endpoint(data.id));
	node.appendChild(img);
	return img;
}

function add_image_result_spark(mode, id, base_img) // add image to the spark result
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
				for(let i = 0; i < lists[cmode].length; ++i) // look for it and remove
				{
					if(this === lists[cmode][i][1])
					{
						lists[cmode].splice(i, 1);
					}
				}
				this.remove();
				update_node(cmode, false);
			}
			saveSpark();
		}
	};
	let img = document.createElement("img");
	img.classList.add("spark-result-img");
	img.src = base_img.src;
	img.onerror = base_img.onerror;
	div.appendChild(img);
	node.appendChild(div);
	lists[mode].push([id, div]);
	update_node(mode, true);
	return div;
}

function toggle_spark_state(div) // toggle spark icon
{
	if(div.childNodes.length == 2) remove_spark(div);
	else if(div.childNodes.length == 1) add_spark(div);
}

function add_spark(div) // add spark icon
{
	if(div.childNodes.length == 2) return;
	let img = document.createElement("img");
	img.classList.add("spark-icon");
	img.src = "assets/spark/spark.png";
	div.appendChild(img);
	div.classList.add("sparked");
}

function remove_spark(div) // remove spark icon
{
	if(div.childNodes.length != 2) return;
	div.removeChild(div.childNodes[1]);
	div.classList.remove("sparked");
}

addEventListener("resize", (event) => { // capture window resize event and call update_all() (after 300ms)
	if(resize_timer != null) clearTimeout(resize_timer);
	resize_timer = setTimeout(update_all, 300);
});

function update_all() // update all three columns
{
	clearTimeout(resize_timer);
	resize_timer = null;
	update_node(NPC, false);
	update_node(MOON, false);
	update_node(STONE, false);
}

function update_node(mode, addition) // update spark column
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
	if(node.childNodes.length == 0) return; // quit if empty
	// get node size
	const nw = node.offsetWidth - 5;
	const nh = node.offsetHeight - 5;
	let current_size;
	if(addition) // get last size if we just added a new element
	{
		current_size = sizes[mode];
	}
	
	{
		current_size = DEFAULT_SIZE; // get default size otherwise
		sizes[mode] = null;
	}
	let changed = false;
	while(true)
	{
		const cw = Math.floor(nw/current_size[0]); // number of element in a row inside the node
		const ch = Math.floor(nh/current_size[1]) - 1; // number of element in a column inside the node (-1 to assure some space)
		if(node.childNodes.length <= cw*ch) // if the total number of element is greater to our number of ssr
		{
			break;
		}
		sizes[mode] = [current_size[0]*0.9, current_size[1]*0.9]; // else, reduce size by 10% and try again
		current_size = sizes[mode];
		changed = true;
	}
	if(changed) // if size changed
	{
		for(let i = 0; i < node.childNodes.length; ++i) // resize all elements
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
				node.childNodes[i].style.minWidth = "" + Math.max(1, sizes[mode][0]) + "px"; // min needed for mobile
				node.childNodes[i].style.minHeight = "" + Math.max(1, sizes[mode][1]) + "px";
				node.childNodes[i].style.maxWidth = "" + Math.max(1, sizes[mode][0]) + "px";
				node.childNodes[i].style.maxHeight = "" + Math.max(1, sizes[mode][1]) + "px";
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
					if(lists[i][j][1].childNodes.length == 2) ++s;
					else ++c;
			if(v < c) v = c;
			document.getElementById("spark-rate").innerHTML = "" + c + " / " + v + (s > 0 ? " +" + s + " sparked": "") + "<br>" + (Math.round(c / v * 1000) / 10) + "% SSR";
		}
		catch(err)
		{
			console.error("Exception thrown", err.stack);
			return;
		}
		if(to_update) saveSpark();
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
		div.classList.add("spark-fullscreen-bg");
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

function saveSpark() // save spark in localstorage
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

function load_spark() // load spark from localstorage
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

function saveSetting() // save settings in localstorage
{
	let tmp = [document.getElementById("moon-check").classList.contains("active"), document.getElementById("spark-check").classList.contains("active")];
	localStorage.setItem("gbfal-spark-settings", JSON.stringify(tmp));
}

function load_setting() // load settings from localstorage
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

function spark_filter() // filter trigger
{
	clearTimeout(typing_timer);
	typing_timer = setTimeout(function(){
		spark_apply_filter(document.getElementById('spark-filter').value.trim().toLowerCase());
	}, 1000);
}

function spark_apply_filter(content) // apply the filter
{
	if(content == "") // empty, we reset
	{
		for(let k in items)
		{
			items[k].style.display = null;
		}
	}
	else
	{
		for(let k in items) // hide everything
		{
			items[k].style.display = "none";
		}
		search(content, 1); // call GBFAL search (behavior 1)
		for(let i = 0; i < search_results.length; ++i) // unhide all results
		{
			if(search_results[i][1] == 2 || search_results[i][1] == 3) // only chara and summon
			{
				if(search_results[i][0] in items)
					items[search_results[i][0]].style.display = null;
			}
			else if(search_results[i][1] == 1 && search_results[i][0] in index["premium"]) // matching chara = weapon
			{
				const id = index["premium"][search_results[i][0]];
				if(id in items)
					items[id].style.display = null;
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
	saveSetting();
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
	saveSetting();
}

function close_fullscreen() // close fullscreen popups
{
	beep();
	let bgs = document.getElementsByClassName("spark-fullscreen-bg");
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
	if(canvas_state == 2) return;
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
	if(canvas_state == 2) return;
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
	if(imgcount == 0) return []; // if no image, stop now
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
		canvas.onclick = function() {
			close_fullscreen();
		}
		// add background
		let div = document.createElement("div");
		div.onclick = function() {
			close_fullscreen();
		}
		div.classList.add("spark-fullscreen-bg");
		document.body.appendChild(div);
		div.appendChild(canvas);
		if(isOnMobile()) push_popup("Hold Touch, Save as...");
		else push_popup("Right Click, Save as...");
		canvas_state = 0;
	}
}