javascript:(function () {
let obj = {
	files:new Set(),
	names:{},
	images:new Set()
};
let scenes = ("eventSceneView" in Game.view) ? Game.view.eventSceneView : Game.view.scene_view.eventSceneView;
for(const line of scenes.scenarioCollection.models)
{
	const attr = line.attributes;
	if(attr && attr.charcter1_big_image && attr.charcter1_big_image != "")
	{
		const sp = attr.charcter1_big_image.split("/");
		if(attr.charcter1_big_image.includes("character/body/3"))
		{
			const file = sp[sp.length - 1].split(".")[0];
			obj.files.add(file);
			if(attr.charcter1_name != "null" && attr.charcter1_name != "" && attr.charcter1_name != "???")
			{
				const id = file.split("_")[0];
				if(!(id in obj.names))
				{
					obj.names[id] = new Set();
				}
				obj.names[id].add(attr.charcter1_name);
			}
		}
		else if(attr.charcter1_big_image.startsWith("/sp/quest/scene/character/body/scene_evt"))
		{
			obj.images.add(sp[sp.length - 1]);
		}
	}
}
obj.files = [...obj.files];
obj.images = [...obj.images];
for(const k of Object.keys(obj.names))
{
	obj.names[k] = [...obj.names[k]];
}
let copyListener = event => {
	document.removeEventListener("copy", copyListener, true);
	event.preventDefault();
	let clipboardData = event.clipboardData;
	clipboardData.clearData();
	clipboardData.setData("text/plain", JSON.stringify(obj));
};
document.addEventListener("copy", copyListener, true);
document.execCommand("copy");
})();