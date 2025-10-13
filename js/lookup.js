/*jshint esversion: 11 */

// global variables
var output = null; // set output
var gbf = null;
var search = null;
var timestamp = Date.now(); // last updated timestamp
var index = null;
var last_id = null;
var last_type = null;
const updated_key = "gbfal-updated";
const bookmark_key = "gbfal-bookmark";
var bookmark_onclick = null;
const history_key = "gbfal-history";
var history_onclick = null;
const search_save_key = "gbfal-search";
var dummy_scene = [];
var no_speech_bubble_filter = [];
var audio = null;
var jukebox = null;

function init() // entry point, called by body onload
{
	// init var
	gbf = new GBF();
	gbf.set_lookup_prefix({
		"e": GBFType.enemy,
		"q": GBFType.event,
		"sk": GBFType.skill,
		"fa": GBFType.fate,
		"b": GBFType.buff,
		"ms": GBFType.story,
		"sd": GBFType.shield,
		"ma": GBFType.manatura
	});
	bookmark_onclick = index_onclick;
	history_onclick = index_onclick;
	output = document.getElementById('output');
	
	// open tab
	open_tab('index'); // set to this tab by default
	
	// get json
	Promise.all([
		fetchJSON("json/config.json?" + timestamp),
		fetchJSON("json/changelog.json?" + timestamp)
	]).then((values) => {
		let config = values[0];
		let changelog = values[1];
		if(config == null) // GBFAL is broken
		{
			crash();
		}
		else
		{
			load(config, changelog);
		}
	});
}

function load(config, changelog)
{
	let stat_string = "";
	if(config.dummy_scene)
		dummy_scene = config.dummy_scene;
	if(config.no_speech_bubble_filter)
		no_speech_bubble_filter = config.no_speech_bubble_filter;
	if(config.hasOwnProperty("banned"))
	{
		gbf.banned_ids = config.banned;
	}
	if(changelog)
	{
		timestamp = changelog.timestamp; // start the clock
		clock(); // start the clock
		if(changelog.hasOwnProperty("stat")) // save stat string
			stat_string = changelog.stat;
		if(changelog.hasOwnProperty("issues")) // write issues if any
		{
			issues(changelog);
		}
		if(config.hasOwnProperty("help_form"))
		{
			help_form = config.help_form;
		}
		if(help_form && changelog.hasOwnProperty("help") && changelog.help)
		{
			help_wanted(config);
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
			start(config, changelog);
		}
	});
	fetchJSON("../GBFML/json/jukebox.json").then((value) => {
		let node = document.getElementById("jukebox");
		jukebox = new AudioJukeboxPlayer(node, value);
		document.getElementById("tab-jukebox").style.display = "";
	});
}

function start(config, changelog)
{
	search = new Search(
		document.getElementById("filter"),
		document.getElementById("search-area"),
		search_save_key,
		{
			"wpn":["Weapon", GBFType.weapon],
			"sum":["Summon", GBFType.summon],
			"cha":["Character", GBFType.character],
			"skn":["Skin", "skins"],
			"npc":["NPC", GBFType.npc],
			"job":["Protagonist", GBFType.job],
			"bss":["Enemy", GBFType.enemy]
		},
		(config.allow_id_input ?? false)
	);
	search.populate_search_area();
	init_lists(changelog, index_onclick);
	init_index(config, changelog, index_onclick);
	let id = get_url_params().get("id");
	if(id != null)
	{
		lookup(id);
	}
}

function index_onclick()
{
	if(window.event.ctrlKey) // open new window
	{
		window.open("?id="+this.onclickid, '_blank').focus();
	}
	else
	{
		window.scrollTo(0, 0);
		lookup(this.onclickid);
	}
}

// load the appropriate element when user does back or forward
window.addEventListener("popstate", (event) => {
	let id = get_url_params().get("id");
	if(id)
	{
		lookup(id);
	}
});

function lookup(id, allow_open=true) // check element validity and either load it or return search results
{
	try
	{
		let type = gbf.lookup_string_to_element(id);
		let target = null;
		// exception due to special events and fates
		if(type == GBFType.unknown)
		{
			if(id.length == 7 && id.substring(1) in index["events"])
				type = GBFType.event;
			else if(id.length == 6 && id.startsWith("fa") && id.substring(2) in index["fate"])
				type = GBFType.fate;
		}
		if(type != GBFType.unknown)
		{
			target = gbf.type_to_index(type);
			if(target == "characters" && gbf.is_character_skin(id))
			{
				target = "skins";
			}
			else if(target == null)
			{
				console.error("Unsupported type " + type);
			}
			if(gbf.is_banned(id))
				return false;
			id = gbf.remove_prefix(id, type);
		};
		// remove fav button before loading
		init_bookmark_button(false);
		// execute
		if(target != null)
		{
			if(id in index[target])
			{
				if(index[target][id] !== 0)
				{
					load_assets(id, index[target][id], type, target, true, allow_open);
					return true;
				}
				else
				{
					return load_dummy(id, type, target, allow_open);
				}
			}
			else if(!isNaN(id))
			{
				return load_dummy(id, type, target, allow_open);
			}
		}
	} catch(err) {
		console.error("Exception thrown", err.stack);
	}
	return false;
}

function load_dummy(id, type, target, allow_open)// minimal load of an element not indexed or not fully indexed, this is only intended as a cheap placeholder
{
	let data = null;
	switch(type)
	{
		case GBFType.weapon:
			data = [[id],["phit_" + id + ".png","phit_" + id + "_1.png","phit_" + id + "_2.png"],["sp_" + id + "_0_a.png","sp_" + id + "_0_b.png","sp_" + id + "_1_a.png","sp_" + id + "_1_b.png"]];
			break;
		case GBFType.summon:
			data = [[id,id + "_02"],["summon_" + id + "_01_attack_a.png","summon_" + id + "_01_attack_b.png","summon_" + id + "_01_attack_c.png","summon_" + id + "_01_attack_d.png","summon_" + id + "_02_attack_a.png","summon_" + id + "_02_attack_b.png","summon_" + id + "_02_attack_c.png"],["summon_" + id + "_01_damage.png","summon_" + id + "_02_damage.png"], []];
			break;
		case GBFType.character:
			data = [["npc_" + id + "_01.png","npc_" + id + "_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_02"],["" + id + "_01","" + id + "_02"],dummy_scene,[],[]];
			break;
		case GBFType.partner:
			data = [["npc_" + id + "_01.png","npc_" + id + "_0_01.png","npc_" + id + "_1_01.png","npc_" + id + "_02.png","npc_" + id + "_0_02.png","npc_" + id + "_1_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_01_0","" + id + "_01_1","" + id + "_02","" + id + "_02_0","" + id + "_02_1"]];
			break;
		case GBFType.npc:
			data = [true, dummy_scene, []];
			break;
		case GBFType.enemy:
			data = [[id],["enemy_" + id + "_a.png","enemy_" + id + "_b.png","enemy_" + id + "_c.png"],["raid_appear_" + id + ".png"],["ehit_" + id + ".png"],["esp_" + id + "_01.png","esp_" + id + "_02.png","esp_" + id + "_03.png"],["esp_" + id + "_01_all.png","esp_" + id + "_02_all.png","esp_" + id + "_03_all.png"]];
			break;
		case GBFType.skill:
			data = [[JSON.stringify(parseInt(id))]];
			break;
		case GBFType.buff:
			data = [[JSON.stringify(parseInt(id))],["","_1","_2","_10","_11","_101","_110","_111","_20", "_30","1","_1_1", "_2_1","_0_10","_1_10","_1_20","_2_10"]];
			break;
		default:
			return false;
	}
	if(data != null)
	{
		load_assets(id, data, type, target, false, allow_open);
		return true;
	}
	return false;
}

function reset_asset_tabs() // reset the tab state
{
	let tabcontent = document.getElementsByClassName("tab-asset-content");
	for(let i = 0; i < tabcontent.length; i++)
		tabcontent[i].style.display = "none";
	let tabbuttons = document.getElementsByClassName("tab-asset-button");
	for (let i = 0; i < tabbuttons.length; i++)
		tabbuttons[i].classList.toggle("active", false);
}

function open_asset_tab(name) // reset and then select a tab
{
	reset_asset_tabs();
	document.getElementById(name).style.display = "";
	document.getElementById("tab-"+name).classList.toggle("active", true);
}

function load_assets(id, data, type, target, indexed, allow_open)
{
	beep();
	gbf.reset_endpoint();
	if(typeof audio != "undefined" && audio != null && audio.player != null)
	{
		audio.player.pause();
	}
	audio = null;
	// save last_id
	let tmp_last_id = last_id;
	// headers
	let include_link = false; // if true, will add wiki links and extra links
	let extra_links = [];
	// content
	let pages = [];
	let files = null;
	// flags
	let keeptab = false; // add tab to DOM if true even if there is a single one
	let melee = false; // melee weapon flag
	
	switch(type)
	{
		case GBFType.weapon:
		{
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]]; // format is title, icon, link
			last_id = id; // update last id
			// tabs to display
			pages = [
				{
					name:"Arts",
					icon:"../GBFML/assets/ui/icon/journal.png",
					assets:[
						{type:1, paths:[["sp/assets/weapon/b/", "png"]], index:0}, // default is type 0, see further below for types
						{name:"Other Arts", paths:[["sp/assets/weapon/weapon_evolution/main/", "png"], ["sp/assets/weapon/g/", "png"], ["sp/gacha/header/", "png"]], index:0, icon:"../GBFML/assets/ui/icon/other_category.png"}
					]
				},
				{
					name:"Portraits",
					icon:"../GBFML/assets/ui/icon/portrait.png",
					assets:[
						{type:1, paths:[["sp/assets/weapon/m/", "jpg"], ["sp/assets/weapon/s/", "jpg"], ["sp/assets/weapon/ls/", "jpg"]], index:0, lazy:false}
					]
				},
				{
					name:"Sprites",
					icon:"../GBFML/assets/ui/icon/sprite.png",
					assets:[
						{type:1, paths:[["sp/cjs/", "png"]], special_index:"sprite", filename:true, lazy:false},
						{name:"Attack Effects", paths:[["sp/cjs/", "png"]], index:1, icon:"../GBFML/assets/ui/icon/auto.png", filename:true},
						{name:"Charge Attack Effects", paths:[["sp/cjs/", "png"]], index:2, icon:"../GBFML/assets/ui/icon/ca.png", filename:true}
					]
				},
				{
					name:"Others",
					icon:"../GBFML/assets/ui/icon/siero.png",
					assets:[
						{type:1, paths:[["sp/gacha/cjs_cover/", "png"]], special_index:"recruit_header", hidden:true, lazy:false},
						{type:1, paths:[["sp/archaic/", ""]], special_index:"weapon_forge_header", hidden:true, lazy:false},
						{type:1, paths:[["sp/archaic/", ""]], special_index:"weapon_forge_portrait", hidden:true, lazy:false},
						{type:1, paths:[["sp/coaching/reward_npc/assets/", "png"]], special_index:"reward", hidden:true, lazy:false}
					]
				}
			];
			melee = (id[4] == "6");
			break;
		}
		case GBFType.shield:
		{
			last_id = "sd"+id; // last id must add prefix
			pages = [
				{
					name:"",
					icon:"",
					assets:[
						{type:1, paths:[["sp/cjs/shield_", "png"], ["sp/assets/shield/m/", "jpg"], ["sp/assets/shield/s/", "jpg"]], index:0}
					]
				}
			];
			break;
		}
		case GBFType.manatura:
		{
			last_id = "ma"+id;
			pages = [
				{
					name:"",
					icon:"",
					assets:[
						{type:1, paths:[["sp/cjs/familiar_", "png"], ["sp/assets/familiar/m/", "jpg"], ["sp/assets/familiar/s/", "jpg"]], index:0}
					]
				}
			];
			break;
		}
		case GBFType.summon:
		{
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]];
			last_id = id;
			pages = [
				{
					name:"Arts",
					icon:"../GBFML/assets/ui/icon/journal.png",
					assets:[
						{type:1, paths:[["sp/assets/summon/b/", "png"]], index:0},
						{name:"Other Arts", paths:[["sp/assets/summon/summon_evolution/main/", "png"], ["sp/assets/summon/g/", "png"], ["sp/gacha/header/", "png"]], index:0, icon:"../GBFML/assets/ui/icon/other_category.png"},
					]
				},
				{
					name:"Skycompass",
					icon:"../GBFML/assets/ui/icon/skycompass_alpha.png",
					assets:[
						{type:2, paths:[["https://media.skycompass.io/assets/archives/summons/", "/detail_l.png"], ["https://media.skycompass.io/assets/archives/summons/", "/detail_s.png"], ["https://media.skycompass.io/assets/archives/summons/", "/list.png"]], special_index:"skycompass_base"}
					]
				},
				{
					name:"Home",
					icon:"../GBFML/assets/ui/icon/home.png",
					assets:[
						{type:1, paths:[["sp/assets/summon/my/", "png"]], index:0, home:true}
					]
				},
				{
					name:"Portraits",
					icon:"../GBFML/assets/ui/icon/portrait.png",
					assets:[
						{type:1, paths:[["sp/assets/summon/m/", "jpg"], ["sp/assets/summon/s/", "jpg"], ["sp/assets/summon/party_main/", "jpg"], ["sp/assets/summon/party_sub/", "jpg"], ["sp/assets/summon/detail/", "png"]], index:0, lazy:false},
						{name:"Battle Portraits", paths:[["sp/assets/summon/raid_normal/", "jpg"], ["sp/assets/summon/btn/", "png"]], index:0, icon:"../GBFML/assets/ui/icon/battle.png"}
					]
				},
				{
					name:"Sprites",
					icon:"../GBFML/assets/ui/icon/sprite.png",
					assets:[
						{name:"Summon Call Sheets", paths:[["sp/cjs/", "png"]], index:1, icon:"../GBFML/assets/ui/icon/summon_call.png", filename:true},
						{name:"Summon Damage Sheets", paths:[["sp/cjs/", "png"]], index:2, icon:"../GBFML/assets/ui/icon/summon_call.png", filename:true},
						{name:"Home Page Sheets", paths:[["sp/cjs/", "png"]], index:3, icon:"../GBFML/assets/ui/icon/home.png", filename:true}
					]
				},
				{
					name:"Others",
					icon:"../GBFML/assets/ui/icon/siero.png",
					assets:[
						{type:1, paths:[["sp/assets/summon/qm/", "png"]], special_index:"quest_portrait", hidden:true, lazy:false}
					]
				}
			];
			break;
		}
		case GBFType.character:
		{
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]];
			last_id = id;
			pages = [
				{
					name:"Arts",
					icon:"../GBFML/assets/ui/icon/journal.png",
					assets:[
						{type:1, paths:[["sp/assets/npc/zoom/", "png"]], index:5, form:false, open:allow_open},
						{name:"Journal Arts", paths:[["sp/assets/npc/b/", "png"]], index:5, icon:"../GBFML/assets/ui/icon/journal.png", form:false},
						{name:"Miscellaneous Arts", paths:[["sp/assets/npc/npc_evolution/main/", "png"], ["sp/assets/npc/gacha/", "png"], ["sp/cjs/npc_get_master_", "png"], ["sp/assets/npc/add_pose/", "png"]], index:6, icon:"../GBFML/assets/ui/icon/other_category.png", form:false},
						{name:"Cut-in Arts", paths:[["sp/assets/npc/cutin_special/", "jpg"], ["sp/assets/npc/raid_chain/", "jpg"]], index:5, icon:"../GBFML/assets/ui/icon/cb.png", form:false}
					]
				},
				{
					name:"Skycompass",
					icon:"../GBFML/assets/ui/icon/skycompass_alpha.png",
					assets:[
						{type:2, paths:[["https://media.skycompass.io/assets/customizes/characters/1138x1138/", ".png"]], index:5}
					]
				},
				{
					name:"Home",
					icon:"../GBFML/assets/ui/icon/home.png",
					assets:[
						{type:1, paths:[["sp/assets/npc/my/", "png"]], index:5, form:false, home:true}
					]
				},
				{
					name:"Portraits",
					icon:"../GBFML/assets/ui/icon/portrait.png",
					assets:[
						{type:1, paths:[["sp/assets/npc/m/", "jpg"], ["sp/assets/npc/s/", "jpg"], ["sp/assets/npc/f/", "jpg"], ["sp/assets/npc/qm/", "png"], ["sp/assets/npc/quest/", "jpg"], ["sp/assets/npc/t/", "png"], ["sp/assets/npc/result_lvup/", "png"], ["sp/assets/npc/detail/", "png"], ["sp/assets/npc/sns/", "jpg"]], index:5, form:false},
						{name:"Battle Portraits", paths:[["sp/assets/npc/raid_normal/", "jpg"]], index:5, icon:"../GBFML/assets/ui/icon/battle.png"},
						{name:"Fire Outfit", paths:[["sp/assets/npc/s/skin/", "_s1.jpg"], ["sp/assets/npc/f/skin/", "_s1.jpg"], ["sp/assets/npc/t/skin/", "_s1.png"]], index:5, icon:"../GBFML/assets/ui/icon/fire.png", form:false},
						{name:"Water Outfit", paths:[["sp/assets/npc/s/skin/", "_s2.jpg"], ["sp/assets/npc/f/skin/", "_s2.jpg"], ["sp/assets/npc/t/skin/", "_s2.png"]], index:5, icon:"../GBFML/assets/ui/icon/water.png", form:false},
						{name:"Earth Outfit", paths:[["sp/assets/npc/s/skin/", "_s3.jpg"], ["sp/assets/npc/f/skin/", "_s3.jpg"], ["sp/assets/npc/t/skin/", "_s3.png"]], index:5, icon:"../GBFML/assets/ui/icon/earth.png", form:false},
						{name:"Wind Outfit", paths:[["sp/assets/npc/s/skin/", "_s4.jpg"], ["sp/assets/npc/f/skin/", "_s4.jpg"], ["sp/assets/npc/t/skin/", "_s4.png"]], index:5, icon:"../GBFML/assets/ui/icon/wind.png", form:false},
						{name:"Light Outfit", paths:[["sp/assets/npc/s/skin/", "_s5.jpg"], ["sp/assets/npc/f/skin/", "_s5.jpg"], ["sp/assets/npc/t/skin/", "_s5.png"]], index:5, icon:"../GBFML/assets/ui/icon/light.png", form:false},
						{name:"Dark Outfit", paths:[["sp/assets/npc/s/skin/", "_s6.jpg"], ["sp/assets/npc/f/skin/", "_s6.jpg"], ["sp/assets/npc/t/skin/", "_s6.png"]], index:5, icon:"../GBFML/assets/ui/icon/dark.png", form:false}
					]
				},
				{
					name:"Sprites",
					icon:"../GBFML/assets/ui/icon/sprite.png",
					assets:[
						{type:1, paths:[["sp/gacha/assets/balloon_s/", "png"], ["sp/assets/npc/sd/", "png"]], index:6, form:false, lazy:false},
						{name:"Sprite Sheets", paths:[["sp/cjs/", "png"]], icon:"../GBFML/assets/ui/icon/spritesheet.png", filename:true, index:0},
						{name:"Attack Effect Sheets", paths:[["sp/cjs/", "png"]], index:1, icon:"../GBFML/assets/ui/icon/auto.png", filename:true},
						{name:"Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:2, icon:"../GBFML/assets/ui/icon/ca.png", filename:true},
						{name:"AOE Skill Sheets", paths:[["sp/cjs/", "png"]], index:3, icon:"../GBFML/assets/ui/icon/skill.png", filename:true},
						{name:"Single Target Skill Sheets", paths:[["sp/cjs/", "png"]], index:4, icon:"../GBFML/assets/ui/icon/skill.png", filename:true},
						{name:"Home Page Sheets", paths:[["sp/cjs/", "png"]], index:9, icon:"../GBFML/assets/ui/icon/home.png", filename:true}
					]
				},
				{
					name:"Scenes",
					icon:"../GBFML/assets/ui/icon/scene.png",
					assets:[
						{type:3, index:7, bubble:0, filename:true},
						{type:3, index:7, bubble:1, filename:true}
					]
				},
				{
					name:"Audios",
					icon:"../GBFML/assets/ui/icon/audio.png",
					assets:[
						{type:5, index:8}
					]
				},
				{
					name:"Others",
					icon:"../GBFML/assets/ui/icon/siero.png",
					assets:[
						{name:"Fate Episode Reward", paths:[["sp/assets/npc/reward/", "png"]], special_index:"reward", icon:"../GBFML/assets/ui/icon/fate_episode.png", form:false, hidden:true, lazy:false},
						{name:"Recruit Arts", paths:[["sp/cjs/npc_get_master_", "png"]], special_index:"character_unlock", icon:"../GBFML/assets/ui/icon/recruit.png", form:false, hidden:true, lazy:false},
						{name:"News Art", paths:[["sp/banner/notice/update_char_", "png"]], index:6, icon:"../GBFML/assets/ui/icon/news.png", form:false, hidden:true, lazy:false},
						{name:"Result Popup", paths:[["sp/result/popup_char/", "png"]], special_index:"character_popup", icon:"../GBFML/assets/ui/icon/result.png", form:false, hidden:true, lazy:false},
						{name:"Custom Skill Previews", paths:[["sp/assets/npc/sd_ability/", "png"]], special_index:"custom_outfit_skill", icon:"../GBFML/assets/ui/icon/custom.png", form:false, hidden:true, lazy:false},
						{name:"Siero's Academy", paths:[["sp/coaching/chara/", "png"], ["sp/coaching/reward_npc/assets/", "jpg"], ["sp/coaching/reward_npc/assets/name_", "png"]], special_index:"reward", icon:"../GBFML/assets/ui/icon/siero.png", form:false, hidden:true, lazy:false},
						{name:"Other Arts", paths:[["sp/shop/prebuiltset/assets/chara/", ".png"]], special_index:"reward", icon:"../GBFML/assets/ui/icon/other_category.png", form:false, hidden:true, lazy:false},
					]
				}
			];
			// extra files for eternals
			if(gbf.eternals().includes(id))
			{
				pages[7].assets[pages[7].assets.length - 1].paths.push(["sp/coaching/assets/eternals/", "png"]);
				pages[7].assets.push(
					{name:"Eternals", paths:[["sp/event/common/terra/top/assets/story/btnbnr_", "_01.png"]], special_index:"reward", icon:"../GBFML/assets/ui/icon/fate_episode.png", form:false, lazy:false}
				);
			}
			break;
		}
		case GBFType.partner:
		{
			keeptab = true;
			include_link = true;
			last_id = id;
			pages = [
				{
					name:"Portraits",
					icon:"../GBFML/assets/ui/icon/portrait.png",
					assets:[
						{name:"Party Portraits", paths:[["sp/assets/npc/quest/", "jpg"]], index:5, icon:"../GBFML/assets/ui/icon/portrait.png", form:false, open:allow_open},
						{name:"Battle Portraits", paths:[["sp/assets/npc/raid_normal/", "jpg"]], index:5, icon:"../GBFML/assets/ui/icon/battle.png"},
						{name:"Cut-in Arts", paths:[["sp/assets/npc/cutin_special/", "jpg"], ["sp/assets/npc/raid_chain/", "jpg"]], index:5, icon:"../GBFML/assets/ui/icon/cb.png", form:false}
					]
				},
				{
					name:"Sprites",
					icon:"../GBFML/assets/ui/icon/sprite.png",
					assets:[
						{name:"Sprite Sheets", paths:[["sp/cjs/", "png"]], icon:"../GBFML/assets/ui/icon/spritesheet.png", index:0},
						{name:"Attack Effect Sheets", paths:[["sp/cjs/", "png"]], index:1, icon:"../GBFML/assets/ui/icon/auto.png"},
						{name:"Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:2, icon:"../GBFML/assets/ui/icon/ca.png"},
						{name:"AOE Skill Sheets", paths:[["sp/cjs/", "png"]], index:3, icon:"../GBFML/assets/ui/icon/skill.png"},
						{name:"Single Target Skill Sheets", paths:[["sp/cjs/", "png"]], index:4, icon:"../GBFML/assets/ui/icon/skill.png"}
					]
				}
			];
			break;
		}
		case GBFType.npc:
		{
			keeptab = true
			include_link = true;
			last_id = id;
			pages = [
				{
					name:"Arts",
					icon:"../GBFML/assets/ui/icon/journal.png",
					assets:[
						{type:1, paths:[["sp/assets/npc/m/", "jpg"],["sp/assets/npc/zoom/", "png"],["sp/assets/npc/b/", "png"]], special_index:"use_files", open:allow_open, hidden:true, lazy:false},
						{type:3, index:1, bubble:0, filename:true},
						{type:3, index:1, bubble:1, filename:true}
					]
				},
				{
					name:"Audios",
					icon:"../GBFML/assets/ui/icon/audio.png",
					assets:[
						{type:5, index:2, name:"Audios", icon:"../GBFML/assets/ui/icon/audio.png", open:allow_open}
					]
				}
			];
			if("lookup" in index && id in index.lookup && index.lookup[id].includes("voice-only"))
				pages.splice(0, 1);
			
			files = [id + "_01"];
			break;
		}
		case GBFType.enemy:
		{
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]];
			last_id = "e"+id;
			pages = [
				{
					name:"",
					icon:"",
					assets:[
						{name:"Icons", paths:[["sp/assets/enemy/m/", "png"], ["sp/assets/enemy/s/", "png"]], index:0, icon:"../GBFML/assets/ui/icon/eicon.png", open:allow_open},
						{name:"Raid Entry Sheets", paths:[["sp/cjs/", "png"]], index:2, icon:"../GBFML/assets/ui/icon/appear.png", open:allow_open, filename:true},
						{name:"Sprite Sheets", paths:[["sp/cjs/", "png"]], index:1, icon:"../GBFML/assets/ui/icon/spritesheet.png", filename:true},
						{name:"Attack Effect Sheets", paths:[["sp/cjs/", "png"]], index:3, icon:"../GBFML/assets/ui/icon/auto.png", filename:true},
						{name:"Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:4, icon:"../GBFML/assets/ui/icon/ca.png", filename:true},
						{name:"AOE Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:5, icon:"../GBFML/assets/ui/icon/ca.png", filename:true}
					]
				}
			];
			break;
		}
		case GBFType.job:
		{
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]];
			last_id = id;
			pages = [
				{
					name:"Home",
					icon:"../GBFML/assets/ui/icon/home.png",
					assets:[
						{type:1, paths:[["sp/assets/leader/my/", "png"]], index:3, home:true}
					]
				},
				{
					name:"Skycompass",
					icon:"../GBFML/assets/ui/icon/skycompass_alpha.png",
					assets:[
						{type:2, paths:[["https://media.skycompass.io/assets/customizes/jobs/1138x1138/", ".png"]], special_index:"skycompass_main_character"}
					]
				},
				{
					name:"Arts",
					icon:"../GBFML/assets/ui/icon/journal.png",
					assets:[
						{type:1, paths:[["sp/assets/leader/job_change/", "png"]], index:3},
						{type:1, paths:[["sp/assets/leader/jobtree/", "png"]], index:0},
						{type:1, paths:[["sp/ui/icon/job/", "png"]], index:0, small:true},
						{type:1, paths:[["sp/ui/icon/job_complete/", "png"]], index:0, small:true}
					]
				},
				{
					name:"Texts",
					icon:"../GBFML/assets/ui/icon/text.png",
					assets:[
						{type:1, paths:[["sp/ui/job_name_tree_l/", "png"], ["sp/ui/job_name/job_change/", "png"],["sp/ui/job_name/job_list/", "png"],["sp/assets/leader/job_name_ml/", "png"],["sp/assets/leader/job_name_pp/", "png"],["sp/event/common/teamraid/assets/skin_name/", "png"]], index:0, hidden:true, lazy:false}
					]
				},
				{
					name:"Profile",
					icon:"../GBFML/assets/ui/icon/profile.png",
					assets:[
						{type:1, paths:[["sp/assets/leader/pm/", "png"]], index:3, profile:true}
					]
				},
				{
					name:"Portraits",
					icon:"../GBFML/assets/ui/icon/portrait.png",
					assets:[
						{type:1, paths:[["sp/assets/leader/m/", "jpg"], ["sp/assets/leader/sd/m/", "jpg"], ["sp/assets/leader/skin/", "png"]], index:1},
						{name:"Battle Portraits", paths:[["sp/assets/leader/raid_normal/", "jpg"],["sp/assets/leader/btn/", "png"],["sp/assets/leader/result_ml/", "jpg"]], icon:"../GBFML/assets/ui/icon/battle.png", index:3},
						{name:"Other Portraits", paths:[["sp/assets/leader/jlon/", "png"], ["sp/assets/leader/jloff/", "png"], ["sp/assets/leader/zenith/", "png"], ["sp/assets/leader/master_level/", "png"]], index:2, icon:"../GBFML/assets/ui/icon/other_category.png", lazy:false},
						{name:"Various Big Portraits", paths:[["sp/assets/leader/zoom/", "png"], ["sp/assets/leader/p/", "png"], ["sp/assets/leader/jobon_z/", "png"], ["sp/assets/leader/coop/", "png"]], index:3, icon:"../GBFML/assets/ui/icon/big_portrait.png"},
						{name:"Various Small Portraits", paths:[["sp/assets/leader/s/", "jpg"], ["sp/assets/leader/talk/", "png"], ["sp/assets/leader/quest/", "jpg"], ["sp/assets/leader/t/", "png"], ["sp/assets/leader/raid_log/", "png"], ["sp/event/common/teamraid/assets/sd_skin/", "jpg"], ["sp/event/common/teamraid/assets/selected_skin_thumbnail/", "png"], ["sp/event/common/teamraid/assets/skin_info_thumbnail/", "png"]], icon:"../GBFML/assets/ui/icon/portrait.png", index:3}
					]
				},
				{
					name:"Sprites",
					icon:"../GBFML/assets/ui/icon/sprite.png",
					assets:[
						{name:"Sprites", paths:[["sp/assets/leader/sd/", "png"]], icon:"../GBFML/assets/ui/icon/sprite.png", index:4, filename:true},
						{name:"Sprite Sheets", paths:[["sp/cjs/", "png"]], icon:"../GBFML/assets/ui/icon/spritesheet.png", index:7, filename:true},
						{name:"Attack Effect Sheets", paths:[["sp/cjs/", "png"]], index:8, icon:"../GBFML/assets/ui/icon/auto.png", filename:true},
						{name:"Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:9, icon:"../GBFML/assets/ui/icon/ca.png", filename:true},
						{name:"AOE Skill Sheets", paths:[["sp/cjs/", "png"]], index:10, icon:"../GBFML/assets/ui/icon/skill.png", filename:true},
						{name:"Single Target Skill Sheets", paths:[["sp/cjs/", "png"]], index:11, icon:"../GBFML/assets/ui/icon/skill.png", filename:true},
						{name:"Home Page Sheets", paths:[["sp/cjs/", "png"]], index:13, icon:"../GBFML/assets/ui/icon/home.png", filename:true},
						{name:"Unlock Sheets", paths:[["sp/cjs/", "png"]], index:12, icon:"../GBFML/assets/ui/icon/lock.png", filename:true},
						{name:"Custom Skill Previews", paths:[["sp/assets/leader/sd_ability/", "png"]], special_index:"custom_class_skill", icon:"../GBFML/assets/ui/icon/custom.png", hidden:true, lazy:false, filename:true}
					]
				}
			];
			break;
		}
		case GBFType.story:
		{
			last_id = "ms"+id;
			pages = [
				{
					name:"",
					icon:"",
					assets:[
						{type:1, paths:[["sp/quest/scene/character/body/", "png"]], index:0, filename:true}
					]
				}
			];
			break;
		}
		case GBFType.fate:
		{
			keeptab = true;
			last_id = "fa"+id;
			pages = [
				{
					name:"Base",
					icon:"../GBFML/assets/ui/icon/art.png",
					assets:[
						{type:1, paths:[["sp/quest/scene/character/body/", "png"]], index:0, filename:true}
					]
				},
				{
					name:"Uncap",
					icon:"../GBFML/assets/ui/icon/uncap.png",
					assets:[
						{type:1, name:"Uncap Arts", paths:[["sp/quest/scene/character/body/", "png"]], index:1, filename:true}
					]
				},
				{
					name:"Transcendence",
					icon:"../GBFML/assets/ui/icon/transcendence.png",
					assets:[
						{type:1, paths:[["sp/quest/scene/character/body/", "png"]], index:2, filename:true}
					]
				},
				{
					name:"Others",
					icon:"../GBFML/assets/ui/icon/party.png",
					assets:[
						{type:1, paths:[["sp/quest/scene/character/body/", "png"]], index:3, filename:true}
					]
				}
			];
			break;
		}
		case GBFType.event:
		{
			keeptab = true;
			last_id = "q"+id;
			pages = [
				{
					name:"Opening",
					icon:"../GBFML/assets/ui/icon/scene_op.png",
					assets:[
						{type:1, paths:[["sp/quest/scene/character/body/", "png"]], index:2, lazy:false, filename:true}
					]
				}
			];
			for(let i = 0; i < 20; ++i)
			{
				pages.push({
					name:"Chapter " + (i+1),
					icon:"../GBFML/assets/ui/icon/scene_" + ("" + (i + 1)).padStart(2, "0") + ".png",
					assets:[
						{type:1, paths:[["sp/quest/scene/character/body/", "png"]], index:5+i, filename:true}
					]
				});
			}
			pages = pages.concat([
				{
					name:"Ending",
					icon:"../GBFML/assets/ui/icon/scene_end.png",
					assets:[
						{type:1, paths:[["sp/quest/scene/character/body/", "png"]], index:3, filename:true}
					]
				},
				{
					name:"Arts",
					icon:"../GBFML/assets/ui/icon/art.png",
					assets:[
						{type:1, paths:[["sp/quest/scene/character/body/", "png"]], index:4, lazy:false, filename:true}
					]
				},
				{
					name:"Skycompass",
					icon:"../GBFML/assets/ui/icon/skycompass_alpha.png",
					assets:[
						{type:2, paths:[["https://media.skycompass.io/assets/archives/events/"+data[1]+"/image/", "_free.png"]], index:25, filename:true}
					]
				},
			]);
			break;
		}
		case GBFType.skill:
		{
			last_id = "sk"+id;
			pages = [
				{
					name:"",
					icon:"",
					assets:[
						{type:1, paths:[["sp/ui/icon/ability/m/", "png"]], special_index:"use_files", small:true, hidden:true, lazy:false}
					]
				}
			];
			files = [""+parseInt(id), ""+parseInt(id)+"_1", ""+parseInt(id)+"_2", ""+parseInt(id)+"_3", ""+parseInt(id)+"_4", ""+parseInt(id)+"_5"];
			break;
		}
		case GBFType.buff:
		{
			last_id = "b"+id;
			pages = [
				{
					name:"",
					icon:"",
					assets:[
						{type:1, paths:[["sp/ui/icon/status/x64/status_"+data[0], "png"]], index:1, small:true}
					]
				}
			];
			break;
		}
		default:
		{
			console.error("Unknown type " + type);
			return;
		}
	}
	// quit if already loaded
	if(id == tmp_last_id && last_type == type)
	{
		open_tab("view");
		output.scrollIntoView();
		return;
	}
	// clean preview parts
	try
	{
		let preview = document.getElementById("preview");
		preview.innerHTML = "";
		add_to(preview, "button", {
			cls:["fullscreen-button"],
			onclick: function() {
				document.getElementById("preview").style.display = "none";
			},
			innertext: "Close"
		});
	} catch (err) {
		console.error("Exception", err);
	}
	// set last id and update query, etc...
	last_type = type;
	update_query(last_id);
	if(indexed)
	{
		update_history(id, type);
		init_bookmark_button(true, id, type);
	}
	// cleanup output and create fragment
	let fragment = document.createDocumentFragment();
	// open tab
	document.getElementById("tab-view").style.display = null;
	open_tab("view");
	// create header
	build_header(
		fragment,
		{
			id:id,
			target:target,
			navigation:indexed,
			navigation_special_targets:["story", "fate", "events"],
			lookup:indexed,
			related:indexed,
			link:include_link,
			extra_links:extra_links
		}
	);
	// tabs
	const tab_containers = [];
	for(const page of pages)
	{
		const tag_id = "asset-" + page.name.toLowerCase().replaceAll(" ", "-");
		let i = tab_containers.length;
		tab_containers.push([null, null]);
		// button
		tab_containers[i][0] = add_to(null, "button", {
			cls:["tab-button", "tab-asset-button"],
			id:"tab-" + tag_id,
			onclick:function() {
				open_asset_tab(tag_id)
			}
		});
		add_to(tab_containers[i][0], "img", {
			cls:["tab-button-icon"]
		}).src = page.icon;
		tab_containers[i][0].appendChild(document.createTextNode(page.name));
		// tab content
		tab_containers[i][1] = add_to(null, "div", {
			cls:["container", "tab-asset-content"],
			id:tag_id
		});
		tab_containers[i][1].style.display = "none";
		// add assets
		for(let j = 0; j < page.assets.length; ++j)
		{
			// tab type
			switch(page.assets[j].type ?? 0)
			{
				case 5: // audios
				{
					if(!indexed)
						continue;
					files = get_file_list(id, data, page.assets[j], files, melee);
					add_audio_assets(tab_containers[i][1], id, files);
					break;
				}
				case 4: // scenes with details
				{
					files = get_file_list(id, data, page.assets[j], files, melee);
					const [details, div] = add_result(null, page.assets[j]);
					if(add_scene_assets(div, id, page.assets[j], files))
						tab_containers[i][1].appendChild(details);
					break;
				}
				case 3: // scenes
				{
					files = get_file_list(id, data, page.assets[j], files, melee);
					add_scene_assets(tab_containers[i][1], id, page.assets[j], files);
					break;
				}
				case 2: // skycompass
				{
					files = get_file_list(id, data, page.assets[j], files, melee);
					add_skycompass_assets(tab_containers[i][1], id, page.assets[j], files);
					break;
				}
				case 1: // no detail element
				{
					files = get_file_list(id, data, page.assets[j], files, melee);
					add_assets(tab_containers[i][1], id, page.assets[j], files);
					break;
				}
				default:
				{
					files = get_file_list(id, data, page.assets[j], files, melee);
					const [details, div] = add_result(null, page.assets[j]);
					if(add_assets(div, id, page.assets[j], files))
						tab_containers[i][1].appendChild(details);
					break;
				}
			}
		}
	}
	// clean empty tabs
	for(let i = 0; i < tab_containers.length;)
	{
		if(tab_containers[i][1].childNodes.length == 0)
			tab_containers.splice(i, 1);
		else
			++i;
	}
	// add tabs
	switch(tab_containers.length)
	{
		case 0:
		{
			output.innerHTML = '<img src="../GBFML/assets/ui/sorry.png"><br>No assets available';
			return;
		}
		case 1:
		{
			if(keeptab) // still add the tab
			{
				fragment.appendChild(tab_containers[0][0]);
				tab_containers[0][0].classList.toggle("active", true);
			}
			fragment.appendChild(tab_containers[0][1]);
			tab_containers[0][1].style.display = "";
			break;
		}
		default:
		{
			for(const tab of tab_containers)
			{
				fragment.appendChild(tab[0]);
			}
			for(const tab of tab_containers)
			{
				fragment.appendChild(tab[1]);
			}
			// make first tab active and visible
			tab_containers[0][0].classList.toggle("active", true);
			tab_containers[0][1].style.display = "";
			break;
		}
	}
	// add close button to bottom of preview
	try
	{
		let preview = document.getElementById("preview");
		add_to(preview, "button", {
			cls:["fullscreen-button"],
			onclick: function() {
				document.getElementById("preview").style.display = "none";
			},
			innertext: "Close"
		});
	} catch (err) {
		console.error("Exception", err);
	}
	interrupt_image_downloads(output);
	// append fragment to output
	update_next_frame(function() {
		output.innerHTML = "";
		output.appendChild(fragment);
		output.scrollIntoView();
	});
}

function get_file_list(id, data, asset, files, melee)
{
	// special exceptions
	switch(asset.special_index ?? "")
	{
		case "use_files": // for npc / skills
		{
			files = files;
			break;
		}
		case "character_popup": // for chara popup portraits
		{
			files = [id, id+"_001"];
			break;
		}
		case "weapon_forge_header": // for weapon forge headers
		{
			files = ["job/header/"+id+".png", "number/header/"+id+".png", "seraphic/header/"+id+".png", "xeno/header/"+id+".png", "bahamut/header/"+id+".png", "omega/header/"+id+".png", "draconic/header/"+id+".png", "revans/header/"+id+".png"];
			break;
		}
		case "weapon_forge_portrait": // for weapon forge portraits
		{
			files = ["job/result/"+id+".png", "number/result/"+id+".png", "seraphic/result/"+id+".png", "xeno/result/"+id+".png", "bahamut/result/"+id+".png", "omega/result/"+id+".png", "draconic/result/"+id+".png", "revans/result/"+id+".png"];
			break;
		}
		case "custom_class_skill": // custom MC skin skills
		{
			files = [id+"_0_ability", id+"_1_ability", id+"_0_attack", id+"_1_attack"];
			for(let i = 1; i < 5; ++i)
				for(let j = 0; j < 2; ++j)
					files.push(id+"_"+j+"_vs_motion_"+i);
			break;
		}
		case "custom_outfit_skill": // custom character skin skills
		{
			files = [id+"_01_attack"];
			for(let i = 1; i < 5; ++i)
				files.push(id+"_01_vs_motion_"+i);
			break;
		}
		case "quest_portrait": // custom summon quest portraits
		{
			files = [id, id+"_hard", id+"_hard_plus", id+"_ex", id+"_ex_plus", id+"_high", id+"_high_plus"]; 
			break;
		}
		case "reward": // character fate episode rewards & chara weapon siero training reward
		{
			files = [id]; 
			break;
		}
		case "character_unlock": // character unlock
		{
			files = [id + "_char", id + "_char_w"]; 
			break;
		}
		case "recruit_header": // gacha cover
		{
			files = [id+"_1", id+"_3"];
			break;
		}
		case "news_art": // character news art
		{
			files = [id];
			break;
		}
		case "sprite": // weapon sprites
		{
			if(melee) // exception for melee weapon sprites
				files = [id+"_1", id+"_2"];
			else
				files = [id];
			break;
		}
		case "skycompass_base": // skycompass art for base id
		{
			files = [id];
			break;
		}
		case "skycompass_main_character": // skycompass art for main character
		{
			files = [id+"_0", id+"_1"];
			break;
		}
		default:
		{
			files = data[asset.index];
		}
	}
	return files;
}

function add_assets(node, id, asset, files)
{
	if(files.length == 0)
		return false;
	// for each path and file
	for(const path of asset.paths)
	{
		for(let i = 0; i < files.length; ++i)
		{
			add_image(node, id, files[i], asset, path);
		}
	}
	
	// add preview
	if((asset.home ?? false) || (asset.profile ?? false))
	{
		add_to(node, "br");
		add_to(node, "button", {
			cls:["fullscreen-button"],
			onclick: function() {
				document.getElementById("preview").style.display = "";
			},
			innertext:"Preview"
		})
	}
	return true;
}

// called if an asset doesn't download
function clean_asset(img)
{
	let parent = img.parentNode.parentNode;
	img.parentNode.remove();
	// if parent is empty (or only preview button is left)
	if(
		parent.childNodes.length == 0 ||
		(
			parent.childNodes.length == 2 &&
			(parent.childNodes[0].tagName == "BR" && parent.childNodes[1].tagName == "BUTTON")
		)
	)
	{
		// if parent is the tab container
		if(parent.id != null && parent.id != "")
		{
			parent.innerHTML = '<img src="../GBFML/assets/ui/sorry.png"><br>Nothing is available in this tab';
		}
		// if parent is container under a details
		else
		{
			let granparent = parent.parentNode;
			parent.remove();
			// check if the detail is empty
			if(granparent.tagName == "DETAILS")
			{
				let grangranparent = granparent.parentNode;
				granparent.remove();
				// if the whole tab is empty
				if(grangranparent.childNodes.length == 0) // note: missing check for button preview
				{
					grangranparent.innerHTML = '<img src="../GBFML/assets/ui/sorry.png"><br>Nothing is available in this tab';
				}
			}
		}
	}
}

function add_skycompass_assets(node, id, asset, files)
{
	if(files.length == 0)
		return false;
	// go over paths and add the images
	for(const path of asset.paths)
	{
		for(let i = 0; i < files.length; ++i)
		{
			const file = files[i];
			if(file instanceof String && file.includes("_f"))
				continue;
			let ref = add_to(node, "a");
			ref.target = "_blank";
			ref.rel = "noopener noreferrer";
			let img = add_to(ref, "img", {
				cls:["loading", "skycompass"],
				onerror:function() {
					clean_asset(this);
				},
				onload:function() {
					this.classList.toggle("loading", false);
				}
			});
			img.src = path[0] + file + path[1];
			if(asset.lazy ?? true)
				img.setAttribute('loading', 'lazy');
			ref.setAttribute('href', img.src);
		}
	}
	return true;
}

function add_scene_assets(node, id, asset, suffixes)
{
	if("npc_replace" in index && id in index.npc_replace) // imported manual_npc_replace.json
		id = index.npc_replace[id]; // replace npc id
	let path = asset.bubble ? ["sp/raid/navi_face/", "png"] : ["sp/quest/scene/character/body/", "png"];
	let files = [];
	// prepare file list with id
	for(let i = 0; i < suffixes.length; ++i)
	{
		if(asset.bubble)
		{
			let add = true;
			for(const bf of no_speech_bubble_filter)
			{
				if(suffixes[i].includes(bf))
				{
					add = false;
					break;
				}
			}
			if(add)
				files.push(id + suffixes[i]);
		}
		else files.push(id + suffixes[i]);
	}
	let clone = {...asset};
	clone.paths = [path];
	return add_assets(node, id, clone, files);
}

// add a detail element to put assets under
function add_result(node, asset)
{
	let details = add_to(node, "details");
	details.open = asset.open ?? false;
	
	let summary = add_to(details, "summary", {
		cls:["detail"]
	});
	let icon = asset.icon ?? null;
	if(icon != null && icon != "")
	{
		add_to(summary, "img", {
			cls:["result-icon"]
		}).src = icon;
	}
	summary.appendChild(document.createTextNode(asset.name));
	
	let div = add_to(details, "div", {
		cls:["container"]
	});
	return [details, div];
}

// add an image asset
function add_image(node, id, file, asset, path)
{
	// form check
	if(!(asset.form ?? true) && (file.endsWith('_f') || file.endsWith('_f1')))
		return;
	// add link
	let ref = add_to(node, "a", {
		cls:["asset-link"]
	});
	ref.target = "_blank";
	ref.rel = "noopener noreferrer";
	// add image
	let img = add_to(ref, "img", {
		cls:["loading", ((asset.small ?? false) ? "asset-small" : "asset")]
	});
	// set path
	// note: old code, might be worth cleaning up later
	if(file.endsWith(".png") || file.endsWith(".jpg")) // if extension is already set
	{
		img.src = gbf.get_endpoint() + "assets_en/img_low/" + path[0] + file;
	}
	else if(path[1].endsWith(".png") || path[1].endsWith(".jpg"))
	{
		img.src = gbf.get_endpoint() + "assets_en/img_low/" + path[0] + file + path[1];
	}
	else
	{
		img.src = gbf.get_endpoint() + "assets_en/img_low/" + path[0] + file + "." + path[1];
	}
	// set link to img src but with lower quality
	ref.setAttribute('href', img.src.replace("img_low", "img").replace("img_mid", "img"));
	// set lazy loading
	if(asset.lazy ?? true)
	{
		img.setAttribute('loading', 'lazy');
	}
	// set hidden
	if((asset.hidden ?? false) && !(asset.lazy ?? true)) // make it uncompatible with lazy loading
	{
		ref.style.display = "none";
	}
	// set events
	img.onerror = function() {
		clean_asset(this);
	};
	img.onload = function() {
		this.classList.toggle("loading", false);
		this.onload = null;
		this.parentNode.style.display = "";
		// make text visible
		if(this.text_node)
			this.text_node.style.display = "";
	};
	// add filename if set
	if(asset.filename ?? false)
	{
		// text class
		let txt = add_to(ref, "div", {
			cls:[((asset.small ?? false) ? "asset-text-small" : "asset-text")],
			innertext: img.src.split("/").pop().split(".")[0].replaceAll(id, "").replaceAll("_", " ").trim()
		});
		txt.style.display = "none";
		img.text_node = txt; // add it to img text_node
	}
	// for mypage and profile previews
	try
	{
		// add the fulle preview in the dedicated part
		if(asset.home ?? false)
		{
			let previewref = add_to(document.getElementById("preview"), "div", {
				cls:["preview-mypage-top"]
			});
			add_to(previewref, "img", {
				cls:["preview-mypage-bg"],
				onerror: function() {
					this.parentNode.remove();
				}
			}).src = ref.href;
		}
		if(asset.profile ?? false)
		{
			let previewref = add_to(document.getElementById("preview"), "div", {
				cls:["preview-profile-top"]
			});
			add_to(previewref, "img", {
				cls:["preview-profile-bg"],
				onerror: function() {
					this.parentNode.remove();
				}
			}).src = ref.href;
		}
	} catch(err) {
		console.error("Exception in add_image", err);
	}
}

function add_audio_assets(node, id, sounds)
{
	let sorted_sound = {"Generic":[]};
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
		"zenith_": "Extended Mastery",
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
		"hp_down": "HP Down",
		"power_down": "Debuffed",
		"dying": "Dying",
		"lose": "K.O.",
		"win": "Win",
		"player": "To Player",
		"pair": "Banter"
	};
	// sort sounds
	for(let sound of sounds)
	{
		let found = false;
		for(const [k, v] of Object.entries(checks))
		{
			if(k == "")
				continue;
			if(sound.includes(k))
			{
				found = true;
				if(!(v in sorted_sound))
					sorted_sound[v] = [];
				sorted_sound[v].push(sound);
				break;
			}
		}
		if(!found)
			sorted_sound["Generic"].push(sound);
	}
	// remove generic category if empty
	if(sorted_sound["Generic"].length == 0)
		delete sorted_sound["Generic"];
	// sort content
	for(const [k, v] of Object.entries(checks))
	{
		if(v in sorted_sound && sorted_sound[v].length > 0)
		{
			sorted_sound[v].sort(sound_sort);
		}
		else if(v in sorted_sound)
		{
			delete sorted_sound[v];
		}
	}
	// sort categories
	sorted_sound = Object.keys(sorted_sound).sort().reduce(
		(obj, key) => {
			obj[key] = sorted_sound[key]; 
			return obj;
		}, 
		{}
	);
	// check if there is at least one sound
	if(Object.keys(sorted_sound).length == 0)
	{
		return false;
	}
	else
	{
		// add audio player
		audio = new AudioVoicePlayer(node, id, sorted_sound);
		return true;
	}
	return false;
}

// random button
function random_lookup()
{
	const targets = ["characters", "summons", "weapons", "enemies", "skins", "job", "npcs"]; // limited to these caregories
	let total = 0;
	let keys = {}
	// count how many elements
	for(let e of targets)
	{
		keys[e] = Object.keys(index[e]);
		total += keys[e].length;
	}
	if(!isNaN(total) && total > 0)
	{
		let roll = Math.floor(Math.random()*total); // roll dice between 0 and total (excluded)
		for(let e of targets) // loop over targets again
		{
			if(roll >= keys[e].length) // if we're outside bounds of current category
			{
				roll -= keys[e].length; // remove excess
			}
			else
			{
				switch(e) // lookup at selected position
				{
					case "enemies":
						lookup("e"+keys[e][roll], false);
						return;
					default:
						lookup(keys[e][roll], false);
						return;
				}
			}
		}
	}
}

// build header callback
function get_special_navigation_indexes(id, target, key_index, keys)
{
	let si = target == "events" ? 2 : 0;
	let next = key_index;
	let previous = key_index;
	
	let valid = false;
	next = key_index;
	while(!valid)
	{
		next = (next + 1) % keys.length;
		if(index[target][keys[next]] !== 0)
		{
			for(let i = si; i < index[target][keys[next]].length; ++i)
			{
				if(index[target][keys[next]][i].constructor === Array && index[target][keys[next]][i].length > 0)
				{
					valid = true;
					break;
				}
			}
		}
	}
	valid = false;
	previous = key_index;
	while(!valid)
	{
		previous = (previous + keys.length - 1) % keys.length;
		if(index[target][keys[previous]] !== 0)
		{
			for(let i = si; i < index[target][keys[previous]].length; ++i)
			{
				if(index[target][keys[next]][i].constructor === Array && index[target][keys[previous]][i].length > 0)
				{
					valid = true;
					break;
				}
			}
		}
	}
	return [previous, next];
}