# GBF Asset Lookup  
Web page to search for GBF assets.  
Click [Here](https://mizagbf.github.io/GBFAL) to access it.  
  
### Updater Requirements  
* Python 3.11.
* Run `pip install -r requirements.txt` in a command prompt.
* See [requirements.txt](https://github.com/MizaGBF/GBFAP/blob/master/requirements.txt) for a list of third-party modules.  
  
## Front-End  
The project consists of a single HTML, javascript and css files.  
[Github Pages](https://pages.github.com/) are used for hosting but it can technically be hosted anywhere.  
  
## Back-End  
Two of the JSON files in the `json` folder are the core of the system:  
- [changelog.json](https://github.com/MizaGBF/GBFAL/blob/main/json/changelog.json) is the first file loaded upon opening the page. It contains the timestamp of the last update and a list of recently updated elements.  
- [data.json](https://github.com/MizaGBF/GBFAL/blob/main/json/data.json) is loaded next and contains the data used to catalog all the assets, and more.  
  
Others JSON files are used for debug or update purpose:  
- [job_data_export.json](https://github.com/MizaGBF/GBFAL/blob/main/json/job_data_export.json) is used to quickly link some MC jobs to their weapon animations using the built-in CLI.  
- [relation_name.json](https://github.com/MizaGBF/GBFAL/blob/main/json/relation_name.json) is used to maintain and create the related section.  
  
More JSON files not specified here might appear in this folder.  
  
## [updater.py](https://github.com/MizaGBF/GBFAL/blob/main/updater.py)  
This script is in charge of updating the JSON files.  
Do note than using it can be time and bandwidth consuming and the code isn't always optimized (especially for recent additions).  
Running `python updater.py` without any parameters will give you an up-to-date list of parameters, but here's a description of them at the time of writing this README:
Start parameters:
- `-wait`: Wait for GBF to update before running.  
- `-nochange`: Disable changes to [changelog.json](https://github.com/MizaGBF/GBFAL/blob/main/json/changelog.json) "new" list.  
  
Action parameters (Only one of those can be used at a time):
- `-run`: Look for new content. If new content is found, it will automatically run `-update`, `-event`, `-thumb`, `-relation` and `-lookup`. Can append a list of element to `-update`.  
- `-update`: Update the content for specified IDs. Example usage: `python updater.py-update 3040000000 3040001000` to update those two characters. Usable with all ten digit IDs, boss IDs and indexed background IDs. It will run `-lookup` after.  
- `-job`: Check for new MC jobs. Time consuming and not always accurate.  
- `-jobedit`: Open the `JOB EDIT` CLI, allowing you to manually edit the job data.  
- `-lookup`: Force update the lookup table. Time consuming.  
- `-lookupfix`: Open a CLI to manually add lookup data to elements without any. Last resort option.  
- `-relation`: Check for new relationships between elements.  
- `-relationedit`: Open a CLI to create relationships between elements. Last resort option.  
- `-scenenpc`: Update scene datas for NPCs. Very time consuming.  
- `-scenechara`: Update scene datas for characters. Very time consuming.  
- `-sceneskin`: Update scene datas for outfits. Very time consuming.  
- `-scenefull`: Update scene datas for characters, outfits and NPCs. Very time consuming.  
- `-scenesort`: Sort scene datas for every elements. It's called automatically in most cases but this is a way to trigger it manually.  
- `-thumb`: Check thumbnail data for NPCs.  
- `-sound`: Update sound datas for characters, outfits and NPCs. Very time consuming.  
- `-partner`: Update all partner datas. Very time consuming.  
- `-enemy`: Update all enemy datas. Time consuming.  
- `-story`: Update main story datas. Can add `all` to update existing chapters and/or a number to limit set manually the last chapter number.  
- `-event`: Update event datas. Time consuming.  
- `-eventedit`: Open the `EVENT EDIT` CLI, allowing you to add event thumbnail, update skycompass arts and more.  
- `-buff`: Update all buff datas. Time consuming.  
- `-bg`: Update all background datas. Time consuming.  
  
## Other Informations  
- On Windows, [local_server.bat](https://github.com/MizaGBF/GBFAL/blob/main/local_server.bat) can be used to test the project locally, in a web browser.  
- On other OS, just run `python-m http.server` in a terminal, in the project folder.  
- [GBFAP](https://github.com/MizaGBF/GBFAP) is the sister project, dealing with character animations.  
- Alternatively, you can just request for `https://raw.githubusercontent.com/MizaGBF/GBFAL/main/json/changelog.json` to check if the timestamp changed and then download `https://github.com/MizaGBF/GBFAL/blob/main/json/data.json` for your project.  