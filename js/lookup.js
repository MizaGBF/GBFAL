/*jshint esversion: 11 */

// global variables
var output = null; // set output
var settings = {};
var gbf = null;
var timestamp = Date.now(); // last updated timestamp
var index = null;
var last_id = null;
var last_type = null;
const bookmark_key = "gbfal-bookmark";
var bookmark_onclick = null;
const history_key = "gbfal-history";
var history_onclick = null;
const search_save_key = "gbfal-search";
var dummy_scene = [];
var no_speech_bubble_filter = [];
var audio = null;

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
	search_onclick = index_onclick;
	output = document.getElementById('output');
	
	// load settings
	let tmp = localStorage.getItem("gbfal-previewhome");
	if(tmp != null)
		settings.home = !!JSON.parse(tmp);
	else
		settings.home = false;
	tmp = localStorage.getItem("gbfal-previewprofile");
	if(tmp != null)
		settings.profile = !!JSON.parse(tmp);
	else
		settings.profile = false;
	
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
		setInterval(clock, 1000); // start the clock
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
}

function start(config, changelog)
{
	init_search_lookup();
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

function toggle_preview_home() // toggle mypage preview
{
	const homepageElements = document.querySelectorAll(".homepage, .homepage-bg");

	homepageElements.forEach(e => {
		if (!settings.home) {
			e.classList.toggle("asset", false);
			e.classList.toggle("homepage", false);
			e.classList.toggle("homepage-bg", true);
			e.src = e.src.replace('/img_low/', '/img/');
			e.parentNode.classList.toggle("homepage-ui", true);
		} else {
			e.classList.toggle("homepage-bg", false);
			e.parentNode.classList.toggle("homepage-ui", false);
			e.src = e.src.replace('/img/', '/img_low/');
			e.classList.toggle("asset", true);
			e.classList.toggle("homepage", true);
		}
	});

	settings.home = !settings.home;
	localStorage.setItem("gbfal-previewhome", JSON.stringify(settings.home));
}

function toggle_preview_profile() // toggle profile preview
{
	const homepageElements = document.querySelectorAll(".profilepage");
	homepageElements.forEach(e => {
		if (!settings.home) {
			e.classList.toggle("asset", false);
			e.src = e.src.replace('/img_low/', '/img/');
			e.parentNode.classList.toggle("profilepage-ui", true);
		} else {
			e.parentNode.classList.toggle("profilepage-ui", false);
			e.src = e.src.replace('/img/', '/img_low/');
			e.classList.toggle("asset", true);
		}
	});

	settings.home = !settings.home;
	localStorage.setItem("gbfal-previewprofile", JSON.stringify(settings.home));
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
		let filter = document.getElementById('filter');
		if(filter.value == "" || filter.value != id)
		{
			filter.value = id;
		}
		id = id.trim().toLowerCase();
		if(id == "")
			return;
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
			id = gbf.remove_prefix(id, type);
		};
		if(target != null && gbf.is_banned(id))
			return;
		// cleanup search results if not relevant to current id
		clean_search_if_not(id);
		// remove fav button before loading
		init_bookmark_button(false);
		// execute
		if(target != null)
		{
			if(id in index[target])
			{
				if(index[target][id] !== 0)
				{
					load_assets(id, index[target][id], target, true, allow_open);
				}
				else
				{
					load_dummy(id, target, allow_open);
				}
			}
			else if(isNaN(id))
			{
				search(id);
			}
			else
			{
				load_dummy(id, target, allow_open);
			}
		}
		else search(id);
	} catch(err) {
		console.error("Exception thrown", err.stack);
	}
}

function load_dummy(id, target, allow_open)// minimal load of an element not indexed or not fully indexed, this is only intended as a cheap placeholder
{
	let data = null;
	switch(target)
	{
		case "weapons":
			data = [[id],["phit_" + id + ".png","phit_" + id + "_1.png","phit_" + id + "_2.png"],["sp_" + id + "_0_a.png","sp_" + id + "_0_b.png","sp_" + id + "_1_a.png","sp_" + id + "_1_b.png"]];
			break;
		case "summons":
			data = [[id,id + "_02"],["summon_" + id + "_01_attack_a.png","summon_" + id + "_01_attack_b.png","summon_" + id + "_01_attack_c.png","summon_" + id + "_01_attack_d.png","summon_" + id + "_02_attack_a.png","summon_" + id + "_02_attack_b.png","summon_" + id + "_02_attack_c.png"],["summon_" + id + "_01_damage.png","summon_" + id + "_02_damage.png"], []];
			break;
		case "characters":
			data = [["npc_" + id + "_01.png","npc_" + id + "_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_02"],["" + id + "_01","" + id + "_02"],dummy_scene,[],[]];
			break;
		case "skins":
			data = [["npc_" + id + "_01.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_01.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_02"],["" + id + "_01","" + id + "_02"],[],[],[]];
			break;
		case "partners":
			data = [["npc_" + id + "_01.png","npc_" + id + "_0_01.png","npc_" + id + "_1_01.png","npc_" + id + "_02.png","npc_" + id + "_0_02.png","npc_" + id + "_1_02.png"],["phit_" + id + ".png"],["nsp_" + id + "_01_s2.png","nsp_" + id + "_02_s2.png", "nsp_" + id + "_01.png","nsp_" + id + "_02.png"],["ab_all_" + id + "_01.png", "ab_all_" + id + "_02.png"],["ab_" + id + "_01.png","ab_" + id + "_02.png"],["" + id + "_01","" + id + "_01_0","" + id + "_01_1","" + id + "_02","" + id + "_02_0","" + id + "_02_1"]];
			break;
		case "npcs":
			data = [true, dummy_scene, []];
			break;
		case "enemies":
			data = [[id],["enemy_" + id + "_a.png","enemy_" + id + "_b.png","enemy_" + id + "_c.png"],["raid_appear_" + id + ".png"],["ehit_" + id + ".png"],["esp_" + id + "_01.png","esp_" + id + "_02.png","esp_" + id + "_03.png"],["esp_" + id + "_01_all.png","esp_" + id + "_02_all.png","esp_" + id + "_03_all.png"]];
			break;
		case "job":
			data = [[id],[id + "_01"],[],[],[],[id],[],[],[],[],[],[],[]];
			break;
		case "skills":
			data = [[JSON.stringify(parseInt(id))]];
			break;
		case "buffs":
			data = [[JSON.stringify(parseInt(id))],["","_1","_2","_10","_11","_101","_110","_111","_20", "_30","1","_1_1", "_2_1","_0_10","_1_10","_1_20","_2_10"]];
			break;
		default:
			break;
	}
	if(data != null)
	{
		load_assets(id, data, target, false, allow_open);
	}
}

function load_assets(id, data, target, indexed, allow_open)
{
	beep();
	gbf.reset_endpoint();
	let tmp_last_id = last_id;
	let include_link = false;
	let extra_links = [];
	let type = gbf.index_to_type(target);
	let assets = null;
	let skycompass = null;
	let mc_skycompass = false;
	let npcdata = null;
	let files = null;
	let sounds = null;
	let melee = false;
	let openscene = false;
	switch(target)
	{
		case "weapons":
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]];
			last_id = id;
			assets = [
				{name:"Journal Arts", paths:[["sp/assets/weapon/b/", "png"]], index:0, skycompass:true, icon:"assets/ui/result_icon/journal.png", open:allow_open},
				{name:"Miscellaneous Arts", paths:[["sp/assets/weapon/weapon_evolution/main/", "png"], ["sp/assets/weapon/g/", "png"], ["sp/gacha/header/", "png"]], index:0, icon:"assets/ui/result_icon/other.png"},
				{name:"Various Portraits", paths:[["sp/assets/weapon/m/", "jpg"], ["sp/assets/weapon/s/", "jpg"], ["sp/assets/weapon/ls/", "jpg"]], icon:"assets/ui/result_icon/portrait.png", index:0},
				{name:"Sprites", paths:[["sp/cjs/", "png"]], icon:"assets/ui/result_icon/sprite.png", index:0},
				{name:"Attack Effects", paths:[["sp/cjs/", "png"]], index:1, icon:"assets/ui/result_icon/auto.png"},
				{name:"Charge Attack Effects", paths:[["sp/cjs/", "png"]], index:2, icon:"assets/ui/result_icon/ca.png"},
				{name:"Recruit Header", paths:[["sp/gacha/cjs_cover/", "png"]], index:0, icon:"assets/ui/result_icon/recruit.png", break:true, lazy:false},
				{name:"Reforge Arts", paths:[["sp/archaic/", ""]], index:-3, icon:"assets/ui/result_icon/forge.png", lazy:false},
				{name:"Reforge Portraits", paths:[["sp/archaic/", ""]], index:-4, icon:"assets/ui/result_icon/forge.png", lazy:false},
				{name:"Siero's Academy", paths:[["sp/coaching/reward_npc/assets/", "png"]], index:-8, icon:"assets/ui/result_icon/siero.png", lazy:false}
			];
			melee = (id[4] == "6");
			break;
		case "shields":
			last_id = "sd"+id;
			assets = [
				{name:"Various Portraits", paths:[["sp/assets/shield/m/", "jpg"], ["sp/assets/shield/s/", "jpg"]], icon:"assets/ui/result_icon/portrait.png", index:0, open:allow_open},
				{name:"Sprites", paths:[["sp/cjs/shield_", "png"]], icon:"assets/ui/result_icon/sprite.png", index:0, open:allow_open},
			];
			break;
		case "manaturas":
			last_id = "ma"+id;
			assets = [
				{name:"Various Portraits", paths:[["sp/assets/familiar/m/", "jpg"], ["sp/assets/familiar/s/", "jpg"]], icon:"assets/ui/result_icon/portrait.png", index:0, open:allow_open},
				{name:"Sprites", paths:[["sp/cjs/familiar_", "png"]], icon:"assets/ui/result_icon/sprite.png", index:0, open:allow_open},
			];
			break;
		case "summons":
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]];
			last_id = id;
			assets = [
				{name:"Journal Arts", paths:[["sp/assets/summon/b/", "png"]], index:0, skycompass:true, icon:"assets/ui/result_icon/journal.png", open:allow_open},
				{name:"Home Page", paths:[["sp/assets/summon/my/", "png"]], index:0, icon:"assets/ui/result_icon/home.png", home:true},
				{name:"Miscellaneous Arts", paths:[["sp/assets/summon/summon_evolution/main/", "png"], ["sp/assets/summon/g/", "png"], ["sp/gacha/header/", "png"]], index:0, icon:"assets/ui/result_icon/other.png"},
				{name:"Various Portraits", paths:[["sp/assets/summon/m/", "jpg"], ["sp/assets/summon/s/", "jpg"], ["sp/assets/summon/party_main/", "jpg"], ["sp/assets/summon/party_sub/", "jpg"], ["sp/assets/summon/detail/", "png"]], index:0, icon:"assets/ui/result_icon/portrait.png"},
				{name:"Battle Portraits", paths:[["sp/assets/summon/raid_normal/", "jpg"], ["sp/assets/summon/btn/", "png"]], index:0, icon:"assets/ui/result_icon/battle.png"},
				{name:"Summon Call Sheets", paths:[["sp/cjs/", "png"]], index:1, icon:"assets/ui/result_icon/summon_call.png"},
				{name:"Summon Damage Sheets", paths:[["sp/cjs/", "png"]], index:2, icon:"assets/ui/result_icon/summon_call.png"},
				{name:"Home Page Sheets", paths:[["sp/cjs/", "png"]], index:3, icon:"assets/ui/result_icon/home.png"},
				{name:"Quest Portraits", paths:[["sp/assets/summon/qm/", "png"]], index:-7, icon:"assets/ui/result_icon/quest.png", break:true, lazy:false}
			];
			skycompass = ["https://media.skycompass.io/assets/archives/summons/", "/detail_l.png", false];
			break;
		case "skins":
		case "characters":
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]];
			last_id = id;
			assets = [
				{name:"Main Arts", paths:[["sp/assets/npc/zoom/", "png"]], index:5, icon:"assets/ui/result_icon/art.png", skycompass:true, form:false, open:allow_open},
				{name:"Home Page", paths:[["sp/assets/npc/my/", "png"]], index:5, icon:"assets/ui/result_icon/home.png", form:false, home:true},
				{name:"Journal Arts", paths:[["sp/assets/npc/b/", "png"]], index:5, icon:"assets/ui/result_icon/journal.png", form:false},
				{name:"Miscellaneous Arts", paths:[["sp/assets/npc/npc_evolution/main/", "png"], ["sp/assets/npc/gacha/", "png"], ["sp/cjs/npc_get_master_", "png"], ["sp/assets/npc/add_pose/", "png"]], index:6, icon:"assets/ui/result_icon/other.png", form:false},
				{name:"Various Portraits", paths:[["sp/assets/npc/m/", "jpg"], ["sp/assets/npc/s/", "jpg"], ["sp/assets/npc/f/", "jpg"], ["sp/assets/npc/qm/", "png"], ["sp/assets/npc/quest/", "jpg"], ["sp/assets/npc/t/", "png"], ["sp/assets/npc/result_lvup/", "png"], ["sp/assets/npc/detail/", "png"], ["sp/assets/npc/sns/", "jpg"]], index:5, icon:"assets/ui/result_icon/portrait.png", form:false},
				{name:"Skin Portraits", paths:[["sp/assets/npc/s/skin/", "_s1.jpg"], ["sp/assets/npc/f/skin/", "_s1.jpg"], ["sp/assets/npc/t/skin/", "_s1.png"], ["sp/assets/npc/s/skin/", "_s2.jpg"], ["sp/assets/npc/f/skin/", "_s2.jpg"], ["sp/assets/npc/t/skin/", "_s2.png"], ["sp/assets/npc/s/skin/", "_s3.jpg"], ["sp/assets/npc/f/skin/", "_s3.jpg"], ["sp/assets/npc/t/skin/", "_s3.png"], ["sp/assets/npc/s/skin/", "_s4.jpg"], ["sp/assets/npc/f/skin/", "_s4.jpg"], ["sp/assets/npc/t/skin/", "_s4.png"], ["sp/assets/npc/s/skin/", "_s5.jpg"], ["sp/assets/npc/f/skin/", "_s5.jpg"], ["sp/assets/npc/t/skin/", "_s5.png"], ["sp/assets/npc/s/skin/", "_s6.jpg"], ["sp/assets/npc/f/skin/", "_s6.jpg"], ["sp/assets/npc/t/skin/", "_s6.png"]], index:5, icon:"assets/ui/result_icon/skin.png", form:false},
				{name:"Battle Portraits", paths:[["sp/assets/npc/raid_normal/", "jpg"]], index:5, icon:"assets/ui/result_icon/battle.png"},
				{name:"Cut-in Arts", paths:[["sp/assets/npc/cutin_special/", "jpg"], ["sp/assets/npc/raid_chain/", "jpg"]], index:5, icon:"assets/ui/result_icon/cb.png", form:false},
				{name:"Sprites", paths:[["sp/gacha/assets/balloon_s/", "png"], ["sp/assets/npc/sd/", "png"]], index:6, icon:"assets/ui/result_icon/sprite.png", form:false},
				{name:"Sprite Sheets", paths:[["sp/cjs/", "png"]], icon:"assets/ui/result_icon/spritesheet.png", index:0},
				{name:"Attack Effect Sheets", paths:[["sp/cjs/", "png"]], index:1, icon:"assets/ui/result_icon/auto.png"},
				{name:"Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:2, icon:"assets/ui/result_icon/ca.png"},
				{name:"AOE Skill Sheets", paths:[["sp/cjs/", "png"]], index:3, icon:"assets/ui/result_icon/skill.png"},
				{name:"Single Target Skill Sheets", paths:[["sp/cjs/", "png"]], index:4, icon:"assets/ui/result_icon/skill.png"},
				{name:"Home Page Sheets", paths:[["sp/cjs/", "png"]], index:9, icon:"assets/ui/result_icon/home.png"},
				{name:"Fate Episode Reward", paths:[["sp/assets/npc/reward/", "png"]], index:-8, icon:"assets/ui/result_icon/fate_reward.png", break:true, form:false, lazy:false},
				{name:"Recruit Arts", paths:[["sp/cjs/npc_get_master_", "png"]], index:-9, icon:"assets/ui/result_icon/recruit.png", form:false, lazy:false},
				{name:"News Art", paths:[["sp/banner/notice/update_char_", "png"]], index:6, icon:"assets/ui/result_icon/news.png", form:false, lazy:false},
				{name:"Result Popup", paths:[["sp/result/popup_char/", "png"]], index:-2, icon:"assets/ui/result_icon/result.png", form:false, lazy:false},
				{name:"Custom Skill Previews", paths:[["sp/assets/npc/sd_ability/", "png"]], index:-6, icon:"assets/ui/result_icon/custom.png", form:false, lazy:false},
				{name:"Siero's Academy", paths:[["sp/coaching/chara/", "png"], ["sp/coaching/reward_npc/assets/", "jpg"], ["sp/coaching/reward_npc/assets/name_", "png"]], index:-8, icon:"assets/ui/result_icon/siero.png", form:false, lazy:false}
			];
			if(gbf.eternals().includes(id)) // include specific icons
			{
				assets[3].paths.push(["sp/event/common/terra/top/assets/story/btnbnr_", "png"]);
				assets[20].paths.push(["sp/coaching/assets/eternals/", "png"]);
			}
			skycompass = ["https://media.skycompass.io/assets/customizes/characters/1138x1138/", ".png", true];
			npcdata = data[7];
			sounds = data[8];
			break;
		case "partners":
			include_link = true;
			last_id = id;
			assets = [
				{name:"Party Portraits", paths:[["sp/assets/npc/quest/", "jpg"]], index:5, icon:"assets/ui/result_icon/portrait.png", form:false, open:allow_open},
				{name:"Battle Portraits", paths:[["sp/assets/npc/raid_normal/", "jpg"]], index:5, icon:"assets/ui/result_icon/battle.png"},
				{name:"Cut-in Arts", paths:[["sp/assets/npc/cutin_special/", "jpg"], ["sp/assets/npc/raid_chain/", "jpg"]], index:5, icon:"assets/ui/result_icon/cb.png", form:false},
				{name:"Sprite Sheets", paths:[["sp/cjs/", "png"]], icon:"assets/ui/result_icon/spritesheet.png", index:0},
				{name:"Attack Effect Sheets", paths:[["sp/cjs/", "png"]], index:1, icon:"assets/ui/result_icon/auto.png"},
				{name:"Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:2, icon:"assets/ui/result_icon/ca.png"},
				{name:"AOE Skill Sheets", paths:[["sp/cjs/", "png"]], index:3, icon:"assets/ui/result_icon/skill.png"},
				{name:"Single Target Skill Sheets", paths:[["sp/cjs/", "png"]], index:4, icon:"assets/ui/result_icon/skill.png"}
			];
			break;
		case "npcs":
			include_link = data[0];
			last_id = id;
			assets = [
				{name:"Portrait", paths:[["sp/assets/npc/m/", "jpg"]], index:-1, icon:"assets/ui/result_icon/portrait.png", open:allow_open},
				{name:"Arts", paths:[["sp/assets/npc/zoom/", "png"],["sp/assets/npc/b/", "png"]], icon:"assets/ui/result_icon/art.png", index:-1, open:allow_open}
			];
			openscene = allow_open;
			npcdata = data[1];
			sounds = data[2];
			files = [id, id + "_01"];
			break;
		case "enemies":
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]];
			last_id = "e"+id;
			assets = [
				{name:"Icons", paths:[["sp/assets/enemy/m/", "png"], ["sp/assets/enemy/s/", "png"]], index:0, icon:"assets/ui/result_icon/eicon.png", open:allow_open},
				{name:"Raid Entry Sheets", paths:[["sp/cjs/", "png"]], index:2, icon:"assets/ui/result_icon/appear.png", open:allow_open},
				{name:"Sprite Sheets", paths:[["sp/cjs/", "png"]], index:1, icon:"assets/ui/result_icon/spritesheet.png"},
				{name:"Attack Effect Sheets", paths:[["sp/cjs/", "png"]], index:3, icon:"assets/ui/result_icon/auto.png"},
				{name:"Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:4, icon:"assets/ui/result_icon/ca.png"},
				{name:"AOE Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:5, icon:"assets/ui/result_icon/ca.png"}
			];
			break;
		case "job":
			include_link = true;
			extra_links = [["Animations for " + id, "../GBFAP/assets/icon.png", "../GBFAP/?id="+id]];
			indexed = (data[7].length != 0) && indexed;
			last_id = id;
			assets = [
				{name:"Icon", paths:[["sp/ui/icon/job/", "png"]], index:0, icon:"assets/ui/result_icon/jicon.png", open:allow_open},
				{name:"Portraits", paths:[["sp/assets/leader/m/", "jpg"], ["sp/assets/leader/sd/m/", "jpg"], ["sp/assets/leader/skin/", "png"]], index:1, icon:"assets/ui/result_icon/portrait.png", open:allow_open},
				{name:"Full Arts", paths:[["sp/assets/leader/job_change/", "png"]], index:3, icon:"assets/ui/result_icon/art.png", skycompass:true, open:allow_open},
				{name:"Home Page", paths:[["sp/assets/leader/my/", "png"]], index:3, icon:"assets/ui/result_icon/home.png", home:true},
				{name:"Profile Page", paths:[["sp/assets/leader/pm/", "png"]], index:3, icon:"assets/ui/result_icon/profile.png", profile:true},
				{name:"Class Unlock", paths:[["sp/assets/leader/jobtree/", "png"], ["sp/ui/job_name_tree_l/", "png"]], index:0, icon:"assets/ui/result_icon/unlock.png", lazy:false},
				{name:"Other Class Texts", paths:[["sp/ui/job_name/job_change/", "png"],["sp/ui/job_name/job_list/", "png"],["sp/assets/leader/job_name_ml/", "png"],["sp/assets/leader/job_name_pp/", "png"]], icon:"assets/ui/result_icon/text.png", index:0, lazy:false},
				{name:"Various Big Portraits", paths:[["sp/assets/leader/zoom/", "png"], ["sp/assets/leader/p/", "png"], ["sp/assets/leader/jobon_z/", "png"]], index:3, icon:"assets/ui/result_icon/big_portrait.png"},
				{name:"Various Small Portraits", paths:[["sp/assets/leader/s/", "jpg"], ["sp/assets/leader/talk/", "png"], ["sp/assets/leader/quest/", "jpg"], ["sp/assets/leader/t/", "png"], ["sp/assets/leader/raid_log/", "png"], ["sp/event/common/teamraid/assets/selected_skin_thumbnail/", "png"]], icon:"assets/ui/result_icon/portrait.png", index:3},
				{name:"Battle Portraits", paths:[["sp/assets/leader/raid_normal/", "jpg"],["sp/assets/leader/btn/", "png"],["sp/assets/leader/result_ml/", "jpg"]], icon:"assets/ui/result_icon/battle.png", index:3},
				{name:"Other Portraits", paths:[["sp/assets/leader/jlon/", "png"], ["sp/assets/leader/jloff/", "png"], ["sp/assets/leader/zenith/", "png"], ["sp/assets/leader/master_level/", "png"]], index:2, icon:"assets/ui/result_icon/other.png", lazy:false},
				{name:"Sprites", paths:[["sp/assets/leader/sd/", "png"]], icon:"assets/ui/result_icon/sprite.png", index:4},
				{name:"Sprite Sheets", paths:[["sp/cjs/", "png"]], icon:"assets/ui/result_icon/spritesheet.png", index:7},
				{name:"Attack Effect Sheets", paths:[["sp/cjs/", "png"]], index:8, icon:"assets/ui/result_icon/auto.png"},
				{name:"Charge Attack Sheets", paths:[["sp/cjs/", "png"]], index:9, icon:"assets/ui/result_icon/ca.png"},
				{name:"AOE Skill Sheets", paths:[["sp/cjs/", "png"]], index:10, icon:"assets/ui/result_icon/skill.png"},
				{name:"Single Target Skill Sheets", paths:[["sp/cjs/", "png"]], index:11, icon:"assets/ui/result_icon/skill.png"},
				{name:"Unlock Sheets", paths:[["sp/cjs/", "png"]], index:12, icon:"assets/ui/result_icon/lock.png"},
				{name:"Custom Skill Previews", paths:[["sp/assets/leader/sd_ability/", "png"]], index:-5, icon:"assets/ui/result_icon/custom.png", break:true, lazy:false}
			];
			skycompass = ["https://media.skycompass.io/assets/customizes/jobs/1138x1138/", ".png", true];
			mc_skycompass = true;
			break;
		case "story":
			last_id = "ms"+id;
			assets = [
				{name:"Arts", paths:[["sp/quest/scene/character/body/", "png"]], index:0, icon:"assets/ui/result_icon/art.png", open:allow_open}
			];
			break;
		case "fate":
			last_id = "fa"+id;
			assets = [
				{name:"Base Arts", paths:[["sp/quest/scene/character/body/", "png"]], index:0, icon:"assets/ui/result_icon/art.png", open:allow_open},
				{name:"Uncap Arts", paths:[["sp/quest/scene/character/body/", "png"]], index:1, icon:"assets/ui/result_icon/v_uncap.png", open:allow_open},
				{name:"Transcendence Arts", paths:[["sp/quest/scene/character/body/", "png"]], index:2, icon:"assets/ui/result_icon/v_uncap.png", open:allow_open},
				{name:"Other Arts", paths:[["sp/quest/scene/character/body/", "png"]], index:3, icon:"assets/ui/result_icon/v_recruit.png", open:allow_open}
			];
			break;
		case "events":
			last_id = "q"+id;
			type = GBFType.event;
			assets = [
				{name:"Sky Compass", paths:[["", ""]], index:25, icon:"assets/ui/result_icon/skycompass.png", skycompass:true},
				{name:"Opening", paths:[["sp/quest/scene/character/body/", "png"]], index:2, icon:"assets/ui/result_icon/scene.png", open:allow_open},
				{name:"Chapter 1", paths:[["sp/quest/scene/character/body/", "png"]], index:5, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 2", paths:[["sp/quest/scene/character/body/", "png"]], index:6, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 3", paths:[["sp/quest/scene/character/body/", "png"]], index:7, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 4", paths:[["sp/quest/scene/character/body/", "png"]], index:8, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 5", paths:[["sp/quest/scene/character/body/", "png"]], index:9, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 6", paths:[["sp/quest/scene/character/body/", "png"]], index:10, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 7", paths:[["sp/quest/scene/character/body/", "png"]], index:11, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 8", paths:[["sp/quest/scene/character/body/", "png"]], index:12, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 9", paths:[["sp/quest/scene/character/body/", "png"]], index:13, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 10", paths:[["sp/quest/scene/character/body/", "png"]], index:14, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 11", paths:[["sp/quest/scene/character/body/", "png"]], index:15, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 12", paths:[["sp/quest/scene/character/body/", "png"]], index:16, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 13", paths:[["sp/quest/scene/character/body/", "png"]], index:17, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 14", paths:[["sp/quest/scene/character/body/", "png"]], index:18, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 15", paths:[["sp/quest/scene/character/body/", "png"]], index:19, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 16", paths:[["sp/quest/scene/character/body/", "png"]], index:20, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 17", paths:[["sp/quest/scene/character/body/", "png"]], index:21, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 18", paths:[["sp/quest/scene/character/body/", "png"]], index:22, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 19", paths:[["sp/quest/scene/character/body/", "png"]], index:23, icon:"assets/ui/result_icon/scene.png"},
				{name:"Chapter 20", paths:[["sp/quest/scene/character/body/", "png"]], index:24, icon:"assets/ui/result_icon/scene.png"},
				{name:"Ending", paths:[["sp/quest/scene/character/body/", "png"]], index:3, icon:"assets/ui/result_icon/scene.png"},
				{name:"Arts", paths:[["sp/quest/scene/character/body/", "png"]], index:4, icon:"assets/ui/result_icon/art.png", open:allow_open}
			];
			skycompass = ["https://media.skycompass.io/assets/archives/events/"+data[1]+"/image/", "_free.png", true];
			break;
		case "skills":
			last_id = "sk"+id;
			assets = [
				{name:"Skill Icons", paths:[["sp/ui/icon/ability/m/", "png"]], index:-1, icon:"assets/ui/result_icon/ability.png", open:allow_open},
			];
			files = [""+parseInt(id), ""+parseInt(id)+"_1", ""+parseInt(id)+"_2", ""+parseInt(id)+"_3", ""+parseInt(id)+"_4", ""+parseInt(id)+"_5"];
			break;
		case "buffs":
			last_id = "b"+id;
			assets = [
				{name:"Icons", paths:[["sp/ui/icon/status/x64/status_", "png"]], index:1, icon:"assets/ui/result_icon/buff.png", open:allow_open, file:data[0]}
			];
			break;
		default:
			return;
	}
	update_query(last_id);
	if(id == tmp_last_id && last_type == type)
		return; // quit if already loaded
	last_type = type;
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
	// add assets
	for(let i = 0; i < assets.length; ++i)
	{
		if(assets[i].break ?? false) fragment.appendChild(document.createElement('br'));
		load_assets_main(fragment, id, data, target, indexed, assets[i], load_assets_get_files(id, data, assets[i], files, melee), mc_skycompass, skycompass, (assets[i].lazy ?? true));
	}
	// add npc assets
	if(npcdata && npcdata.length > 0)
	{
		fragment.appendChild(document.createElement('br'));
		load_assets_scene(fragment, id, npcdata, indexed, openscene);
	}
	// add sound assets
	if(sounds && sounds.length > 0)
	{
		fragment.appendChild(document.createElement('br'));
		load_assets_sound(fragment, id, sounds, indexed);
	}
	// append fragment to output
	update_next_frame(function() {
		for(let img of output.getElementsByTagName("img")) // interrupt on-going downloads
		{
			img.src = "";
			img.removeAttribute("src");
		}
		output.innerHTML = "";
		output.appendChild(fragment);
		output.scrollIntoView();
	});
}

function load_assets_get_files(id, data, asset, files, melee)
{
	// special exceptions
	switch(asset.index)
	{
		case -1: // for npc / skills
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
			files = [id+"_0_ability", id+"_1_ability", id+"_0_attack", id+"_1_attack"];
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
		case -8: // character fate episode rewards & chara weapon siero training reward
			files = [id]; 
			break;
		case -9: // character unlock
			files = [id + "_char", id + "_char_w"]; 
			break;
		default:
			files = data[asset.index];
			// special exceptions
			switch(asset.name)
			{
				case "Recruit Header": // gacha cover
					files = [files[0]+"_1", files[0]+"_3"];
					break;
				case "News Art": // character news art
					files = [id];
					break;
				case "Sprites":
					if(melee) // melee weapon sprites
						files = [files[0]+"_1", files[0]+"_2"];
					break;
			}
			break;
	}
	return files;
}

function load_assets_main(fragment, id, data, target, indexed, asset, files, mc_skycompass, skycompass, lazy_loading)
{
	if(files.length == 0) return null;
	// add section
	let div = add_result(fragment, asset.name, asset.name, (asset.icon ?? null), asset.open);
	// add mypage preview
	if(asset.home ?? false)
	{
		add_to(div, "img", {
			cls:["clickable", "toggle-btn"],
			onclick: toggle_preview_home
		}).src = "../GBFML/assets/ui/mypage.png";
	}
	// add mypage preview
	else if(asset.profile ?? false)
	{
		add_to(div, "img", {
			cls:["clickable", "toggle-btn"],
			onclick: toggle_preview_profile
		}).src = "assets/ui/profile.png";
	}
	// for each path and file
	for(const path of asset.paths)
	{
		for(let i = 0; i < files.length; ++i)
		{
			let file = files[i];
			if((asset.file ?? null) != null)
				file = asset.file + file;
			if(asset.name != "Sky Compass") // event sky compass exception
			{
				if(!add_image(div, file, asset, path, lazy_loading))
					continue;
			}
			if(skycompass != null && (asset.skycompass ?? false) && path == asset.paths[0]) // skycompass
			{
				add_image_skycompass(div, file, id, data, asset, skycompass, mc_skycompass);
			}
		}
	}
	return div;
}

function load_assets_scene(fragment, id, npcdata, indexed, openscene)
{
	if(id in index["npc_replace"]) // manual_npc_replace.json
		id = index["npc_replace"][id];
	let assets = [
		{name:"Raid Bubble Arts", path:["sp/raid/navi_face/", "png"], icon:"assets/ui/result_icon/bubble.png"},
		{name:"Scene Arts", path:["sp/quest/scene/character/body/", "png"], icon:"assets/ui/result_icon/scene.png"}
	];
	let first = null;
	for(let asset of assets)
	{
		if(npcdata.length == 0) continue;
		let div = add_result(fragment, asset.name, asset.name, asset.icon, openscene);
		if(!first) first = div;
		let count = 0;
		for(let i = 0; i < npcdata.length; ++i)
		{
			let file = npcdata[i];
			if(asset[0] == "Raid Bubble Arts" && no_speech_bubble_filter.includes(file.split("_").slice(-1)[0])) continue; // ignore those
			add_image_scene(div, file, id, asset);
			++count;
		}
		if(count == 0) div.parentNode.remove();
	}
	return first;
}

function load_assets_sound(fragment, id, sounds)
{
	let sorted_sound = {"Generic":[]};
	let checks = {
		"": ["Generic", "assets/ui/result_icon/voice.png"],
		"_boss_v_": ["Boss", "assets/ui/result_icon/v_boss.png"],
		"_v_": ["Standard", "assets/ui/result_icon/voice.png"],
		"birthday": ["Happy Birthday", "assets/ui/result_icon/v_birthday.png"],
		"year": ["Happy New Year", "assets/ui/result_icon/art.png"],
		"alentine": ["Valentine", "assets/ui/result_icon/v_valentine.png"],
		"hite": ["White Day", "assets/ui/result_icon/v_valentine.png"],
		"alloween": ["Halloween", "assets/ui/result_icon/v_halloween.png"],
		"mas": ["Christmas", "assets/ui/result_icon/v_christmas.png"],
		"mypage": ["My Page", "assets/ui/result_icon/home.png"],
		"introduce": ["Recruit", "assets/ui/result_icon/v_recruit.png"],
		"formation": ["Add to Party", "assets/ui/result_icon/v_party.png"],
		"evolution": ["Evolution", "assets/ui/result_icon/v_uncap.png"],
		"zenith_": ["Extended Mastery", "assets/ui/result_icon/v_emp.png"],
		"archive": ["Journal", "assets/ui/result_icon/journal.png"],
		"cutin": ["Battle", "assets/ui/result_icon/v_battle.png"],
		"attack": ["Attack", "assets/ui/result_icon/auto.png"],
		"kill": ["Enemy Defeated", "assets/ui/result_icon/v_kill.png"],
		"ability_them": ["Offensive Skill", "assets/ui/result_icon/skill.png"],
		"ability_us": ["Buff Skill", "assets/ui/result_icon/buff.png"],
		"ready": ["CA Ready", "assets/ui/result_icon/ca.png"],
		"mortal": ["Charge Attack", "assets/ui/result_icon/ca.png"],
		"chain": ["Chain Burst Banter", "assets/ui/result_icon/v_banter.png"],
		"damage": ["Damaged", "assets/ui/result_icon/v_damaged.png"],
		"healed": ["Healed", "assets/ui/result_icon/ability.png"],
		"power_down": ["Debuffed", "assets/ui/result_icon/v_debuffed.png"],
		"dying": ["Dying", "assets/ui/result_icon/v_dying.png"],
		"lose": ["K.O.", "assets/ui/result_icon/v_death.png"],
		"win": ["Win", "assets/ui/result_icon/v_win.png"],
		"player": ["To Player", "assets/ui/result_icon/v_player.png"],
		"pair": ["Banter", "assets/ui/result_icon/v_banter.png"]
	};
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
				if(!(v[0] in sorted_sound)) sorted_sound[v[0]] = [];
				sorted_sound[v[0]].push(sound);
				break;
			}
		}
		if(!found) sorted_sound["Generic"].push(sound);
	}
	if(sorted_sound["Generic"].length == 0) delete sorted_sound["Generic"];
	// loop over categories and sort
	let first = null;
	for(const [k, v] of Object.entries(checks))
	{
		if(v[0] in sorted_sound)
		{
			let div = add_result(fragment, v[0], v[0] + " Voices", v[1]);
			if(!first) first = div;
			sorted_sound[v[0]].sort(sound_sort);
			for(let sound of sorted_sound[v[0]])
			{
				add_sound(div, id, sound);
			}
		}
	}
	return first;
}

function add_result(fragment, identifier, name, icon, open=false) // add an asset category
{
	let details = document.createElement("details");
	details.open = open;
	
	let summary = document.createElement("summary");
	summary.classList.add("detail");
	if(icon != null && icon != "")
	{
		let img = document.createElement("img");
		img.classList.add("result-icon");
		img.src = icon;
		summary.appendChild(img);
	}
	summary.appendChild(document.createTextNode(name));
	
	let div = document.createElement("div");
	div.classList.add("container");
	div.setAttribute("data-id", identifier);
	
	details.appendChild(summary);
	details.appendChild(div);
	fragment.appendChild(details);
	return div;
}

function add_image(div, file, asset, path, lazy_loading) // add an asset
{
	if(!(asset.form ?? true) && (file.endsWith('_f') || file.endsWith('_f1'))) return false;
	let img = document.createElement("img");
	let ref = document.createElement('a');
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
	ref.setAttribute('href', img.src.replace("img_low", "img").replace("img_mid", "img")); // set link
	img.classList.add("loading");
	// preview stuff
	if(asset.home ?? false)
	{
		if(settings.home)
		{
			img.classList.add("homepage-bg");
			img.src = img.src.replace('/img_low/', '/img/');
			ref.classList.add("homepage-ui");
		}
		else img.classList.add("homepage");
	}
	else if(asset.profile ?? false)
	{
		if(settings.profile)
		{
			img.src = img.src.replace('/img_low/', '/img/');
			ref.classList.add("profilepage-ui");
		}
		img.classList.add("profilepage");
	}
	if(lazy_loading) img.setAttribute('loading', 'lazy');
	img.onerror = function() {
		let details = this.parentNode.parentNode.parentNode;
		let result = this.parentNode.parentNode; // parent div
		this.parentNode.remove();
		const n = (this.classList.contains("homepage-bg") || this.classList.contains("homepage") || this.classList.contains("profilepage")) ? 1 : 0;
		this.remove();
		if(result.childNodes.length <= n) details.remove();
	};
	img.onload = function() {
		this.classList.remove("loading");
		if(!this.classList.contains("homepage-bg") && (!this.classList.contains("profilepage") || !settings.profile))
			this.classList.add("asset");
		this.onload = null;
	};
	div.appendChild(ref);
	ref.appendChild(img);
	return true;
}

function add_image_scene(div, file, id, asset) // add a npc/scene asset
{
	let img = document.createElement("img");
	let ref = document.createElement('a');
	img.src = gbf.get_endpoint() + "assets_en/img_low/" + asset.path[0] + id + file + "." + asset.path[1];
	if(file != "") img.title = file.replaceAll('_', ' ').trim();
	ref.setAttribute('href', img.src.replaceAll("img_low", "img"));
	img.classList.add("loading");
	img.setAttribute('loading', 'lazy');
	img.onerror = function() {
		let details = this.parentNode.parentNode.parentNode;
		let result = this.parentNode.parentNode;
		this.parentNode.remove();
		this.remove();
		if(result.childNodes.length <= 0) details.remove();
	};
	img.onload = function() {
		this.classList.remove("loading");
		this.classList.add("asset");
	};
	div.appendChild(ref);
	ref.appendChild(img);
}

function add_image_skycompass(div, file, id, data, asset, skycompass, mc_skycompass) // add a skycompass asset
{
	let img = document.createElement("img");
	img.setAttribute('loading', 'lazy');
	let ref = document.createElement('a');
	if(!skycompass[2]) // if false, use first file string and no uncap suffix
	{
		if(file != data[asset.index][0]) return false;
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
		let details = this.parentNode.parentNode.parentNode;
		let result = this.parentNode.parentNode;
		this.parentNode.remove();
		this.remove();
		if(result.childNodes.length <= 0) details.remove();
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

function add_sound(div, id, sound) // add a sound asset
{
	let elem = document.createElement("div");
	elem.classList.add("sound-file");
	elem.classList.add("clickable");
	elem.title = "Click to play " + id + sound + ".mp3";
	// format element text
	let s = sound;
	if(s[0] == '_') s = s.substring(1);
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
	return elem;
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