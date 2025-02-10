# GBF Asset Lookup  
[![pages-build-deployment](https://github.com/MizaGBF/GBFAL/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/MizaGBF/GBFAL/actions/workflows/pages/pages-build-deployment)  
Web page to search for Granblue Fantasy assets.  
Click [Here](https://mizagbf.github.io/GBFAL) to access it.  
  
# Front-End  
There are two pages:  
- The Asset Lookup, to search assets, consisting of one HTML, one javascript and one css files.  
- The Spark Maker, for users to keep track of their "spark", which has its own HTML, javascript and css files too, on top of reusing the Asset Lookup javascript and css files. 
  
> [!NOTE]  
> These pages are static and are currently hosted on [Github Pages](https://pages.github.com/), but it can technically be hosted anywhere.  
  
# Back-End  
Two of the JSON files in the `json` folder are the core of the system:  
- [changelog.json](https://github.com/MizaGBF/GBFAL/blob/main/json/changelog.json) is the first file loaded upon opening the page. It contains the timestamp of the last update and a list of recently updated elements.  
- [data.json](https://github.com/MizaGBF/GBFAL/blob/main/json/data.json) is loaded next and contains the data used to catalog all the assets, and more.  
  
Others JSON files are used for debug or update purpose:  
- [job_data_export.json](https://github.com/MizaGBF/GBFAL/blob/main/json/job_data_export.json) is used to quickly link some MC jobs to their weapon animations using the built-in CLI.  
- [manual_lookup.json](https://github.com/MizaGBF/GBFAL/blob/main/json/manual_lookup.json) is used to fill lookup entries without wiki data.  
- [manual_fate.json](https://github.com/MizaGBF/GBFAL/blob/main/json/manual_fate.json) is used to associate fate episode entries with other elements.  
- [manual_npc_replace.json](https://github.com/MizaGBF/GBFAL/blob/main/json/manual_npc_replace.json) is used to manually update the internal npc id subtitution list (Used for a handful of collab NPCs).  
- [manual_constants.json](https://github.com/MizaGBF/GBFAL/blob/main/json/manual_constants.json) contains constant values used by the Updater, loaded and set on boot. They are in this separate file for maintainability and clarity.  
  
More JSON files not specified here might appear in this folder, for development or testing purpose.  
  
## [updater.py](https://github.com/MizaGBF/GBFAL/blob/main/updater.py)  
This script is in charge of updating the JSON files.  
> [!CAUTION]  
> Using it can be time and bandwidth consuming.  
  
### Updater Requirements  
* Python 3.13.
* Run `pip install -r requirements.txt` in a command prompt.
* See [requirements.txt](https://github.com/MizaGBF/GBFAP/blob/master/requirements.txt) for a list of third-party modules.  
  
### Usage
```
GBFAL Updater v3.11
usage: updater.py [-h] [-r] [-u UPDATE [UPDATE ...]] [-j [FULL]]
                  [-sc [SCENE ...]] [-sd [SOUND ...]] [-ev [EVENT ...]] [-ne]
                  [-st [LIMIT]] [-ft [FATES]] [-pt] [-ij] [-ej] [-lk] [-fj]
                  [-it] [-et] [-mt] [-au [ADDUNCAP ...]] [-nc] [-nr] [-dg]

Asset Updater v3.11 for GBFAL https://mizagbf.github.io/GBFAL/

options:
  -h, --help            show this help message and exit

primary:
  main commands to update the data.

  -r, --run             search for new content.
  -u, --update UPDATE [UPDATE ...]
                        update given elements.
  -j, --job [FULL]      detailed job search. Add something to trigger a full search.

secondary:
  commands to update some specific data.

  -sc, --scene [SCENE ...]
                        update scene content. Add optional strings to match.
  -sd, --sound [SOUND ...]
                        update sound content. Add optional strings to match.
  -ev, --event [EVENT ...]
                        update event content. Add optional event IDs to update specific events.
  -fe, --forceevent FORCEEVENT [FORCEEVENT ...]
                        force update event content for specific event IDs.
  -ne, --newevent       check new event content.
  -st, --story [LIMIT]  update story content. Add an optional chapter to stop at.
  -ft, --fate [FATES]   update fate content. Add an optional fate ID to update or a range (START-END) or 'last' to update the latest.
  -pt, --partner        update all parner content. Time consuming.
  -mn, --missingnpc     search for missing NPCs. Time consuming.

maintenance:
  commands to perform specific maintenance tasks.

  -ij, --importjob      import data from job_data_export.json.
  -ej, --exportjob      export data to job_data_export.json.
  -lk, --lookup         import and update manual_lookup.json and fetch the wiki to update the lookup table.
  -fj, --fatejson       import and manual_fate.json.
  -it, --importthumb    import data from manual_event_thumbnail.json.
  -et, --exportthumb    export data to manual_event_thumbnail.json.
  -mt, --maintenance    run all existing maintenance tasks.
  -mb, --maintenancebuff
                        maintenance task to check existing buffs for new icons.
  -ms, --maintenancesky
                        maintenance task to check sky compass arts for existing events.
  -mu, --maintenancenpcthumbnail
                        maintenance task to check NPC thumbnails for existing NPCs.
  -js, --json           import all manual JSON files.

settings:
  commands to alter the update behavior.

  -au, --adduncap [ADDUNCAP ...]
                        add elements to be updated during the next run.
  -nc, --nochange       disable update of the New category of changelog.json.
  -nr, --noresume       disable the use of the resume file.
  -if, --ignorefilecount
                        ignore known file count when updating elements.
  -da, --gbfdaio PATH   import index.json from GBFDAIO.
  -dg, --debug          enable the debug infos in the progress string.
```  
  
> [!TIP]  
> For an **"every day" use case**, you'll only need to:  
> Use `-r` after game updates.  
> Use `-u` for element uncaps or if an older NPC got new arts, with their IDs.  
> Use `-j`, `-ej` and `-ij` when new MC classes or skins are released, to find and set their datas and export then import `json/job_data_export.json`.  
> Use `-lk` to update the string lookup and import `json/manual_lookup.json`.  
> Use `-fj` to force import of `json/manual_fate.json`.  
> Use `-it` to force import of `json/manual_event_thumbnail.json`.  
> Use `-mt` to check for updates of existing elements (An equivalent is usually automatically run by `-r` except for buff icons, so it shouldn't be needed. You can just run `-mb` once in a while for the buffs.).  
  
### Pause  
You can pause `updater.py` with a simple `CTRL+C`. It opens a CLI letting you save, exit or resume with text commands.  
  
### Resume file  
When you interrupt some tasks (like the ones invoked by `-sc` and `-sd`), the updater creates a `resume` file (a JSON file without the extension) in the same folder.  
If you restart the same action at a later time, that file will be loaded and content already processed will be skipped.  
  
### Task System  
The Updater uses wrappers around Asyncio Tasks to execute code.  
Tasks/Functions calls can be queued into the Task Manager. There are 5 queues available, the first one having the highest priority.  
The Task Manager itself won't run more than 90 Tasks concurrently (The number itself can be changed in the code). In the same way, the Updater is limited to 80 concurrent requests.  
When a Task or the Updater judges more Task are needed, they will be queued too. That's why the number of Tasks will likely grow when executing the Updater.  
It's designed to limit the memory usage while keeping the Updater always busy, to not have idle/dead times.  
  
### Additional Notes   
- Use one of the `server` scripts to start a Python HTTP server and test the project locally, in your web browser.  
- Or, on other OS, just run `python-m http.server` in a terminal, in the project folder.  
- [GBFAP](https://github.com/MizaGBF/GBFAP) is the sister project, dealing with character animations. It reuses some Javascript, HTML, CSS and Python code.  
- For developers, I documented some things in this [file](https://github.com/MizaGBF/GBFAL/blob/main/docs.md).  