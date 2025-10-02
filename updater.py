from __future__ import annotations
from typing import Any, Callable
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, UTC
import asyncio
import aiohttp
import os
import sys
import re
import time
import json
import string
import html
import traceback
import signal
import argparse

### Constant variables
VERSION = '3.38'
CONCURRENT_TASKS = 90
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Rosetta/GBFAL'
SAVE_VERSION = 1
# limit
HTTP_CONN_LIMIT = 80
LOOKUP_TYPES = ['characters', 'summons', 'weapons', 'job', 'skins', 'npcs']
UPDATABLE = {"characters", "enemies", "summons", "skins", "weapons", "partners", 'npcs', "background", "job", "shields"}
# addition type
ADD_JOB = 0
ADD_WEAP = 1
ADD_SUMM = 2
ADD_CHAR = 3
ADD_BOSS = 4
ADD_NPC = 5
ADD_PARTNER = 6
ADD_EVENT = 7
ADD_SKILL = 8
ADD_BUFF = 9
ADD_BG = 10
ADD_STORY = 11
ADD_FATE = 12
ADD_SHIELD = 13
ADD_MANATURA = 14
ADD_SINGLE_ASSET = ["title", "subskills", "suptix", "mypage_bg", "sky_title"]
# chara/skin/partner update
CHARA_SPRITE = 0
CHARA_PHIT = 1
CHARA_SP = 2
CHARA_AB_ALL = 3
CHARA_AB = 4
CHARA_GENERAL = 5
CHARA_SD = 6
CHARA_SCENE = 7
CHARA_SOUND = 8
CHARA_MYPAGE = 9
CHARA_SPECIAL_REUSE = {"3710171000":"3710167000","3710170000":"3710167000","3710169000":"3710167000","3710168000":"3710167000"} # bobobo skins reuse bobobo data
# npc update
NPC_JOURNAL = 0
NPC_SCENE = 1
NPC_SOUND = 2
# MC update
JOB_ID = 0
JOB_ALT = 1
JOB_DETAIL = 2
JOB_DETAIL_ALT = 3
JOB_DETAIL_ALL = 4
JOB_SD = 5
JOB_MH = 6
JOB_SPRITE = 7
JOB_PHIT = 8
JOB_SP = 9
JOB_AB_ALL = 10
JOB_AB = 11
JOB_UNLOCK = 12
JOB_MYPAGE = 13
# summon update
SUM_GENERAL = 0
SUM_CALL = 1
SUM_DAMAGE = 2
SUM_MYPAGE = 3
# weapon update
WEAP_GENERAL = 0
WEAP_PHIT = 1
WEAP_SP = 2
# enemy update
BOSS_GENERAL = 0
BOSS_SPRITE = 1
BOSS_APPEAR = 2
BOSS_HIT = 3
BOSS_SP = 4
BOSS_SP_ALL = 5
# event update
EVENT_CHAPTER_COUNT = 0
EVENT_THUMB = 1
EVENT_OP = 2
EVENT_ED = 3
EVENT_INT = 4
EVENT_CHAPTER_START = 5
EVENT_MAX_CHAPTER = 20
EVENT_SKY = EVENT_CHAPTER_START+EVENT_MAX_CHAPTER
EVENT_UPDATE_COUNT = 20
# story update
STORY_CONTENT = 0
STORY_UPDATE_COUNT = 10
# fate update
FATE_CONTENT = 0
FATE_UNCAP_CONTENT = 1
FATE_TRANSCENDENCE_CONTENT = 2
FATE_OTHER_CONTENT = 3
FATE_LINK = 4
# buff suffix list
BUFF_LIST_EXTENDED =  ["", "_1", "_2", "_10", "_11", "_101", "_110", "_111", "_20", "_30", "1", "_1_1", "_2_1", "_0_10", "_1_10", "_1_20", "_2_10"]
BUFF_LIST =  BUFF_LIST_EXTENDED.copy()
BUFF_LIST.pop(BUFF_LIST.index("1"))
# job update
MAINHAND = ['sw', 'wa', 'kn', 'me', 'bw', 'mc', 'sp', 'ax', 'gu', 'kt'] # weapon type keywords
# CDN endpoints
ENDPOINT = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/"
JS = ENDPOINT + "js/"
MANIFEST = JS + "model/manifest/"
CJS = JS + "cjs/"
IMG = ENDPOINT + "img/"
SOUND = ENDPOINT + "sound/"
VOICE = SOUND + "voice/"
# regex
CHAPTER_REGEX = re.compile("Chapter (\\d+)(-(\\d+))?")
# others
QUEUE_KEY = ['uncap_queue']
STRING_CHAR = string.ascii_lowercase + string.digits

# dynamic constants
MISSING_EVENTS : list[str] = []
SPECIAL_EVENTS : dict[str, str] = {}
CUT_CONTENT : list[str] = []
SHARED_LOOKUP : list[list[str]] = []
SPECIAL_LOOKUP : dict[str, str] = {}
UNIQUE_SKIN : list[str] = []
MALINDA : str = ""
SCENE_SUFFIXES : dict[str, dict[Any]] = {}
SCENE_BUBBLE_FILTER : dict[str, dict[Any]] = {}
MSQ_RECAPS : dict[str, str] = {}
# load dynamic constants
try:
    with open("json/manual_constants.json", mode="r", encoding="utf-8") as f:
        globals().update(json.load(f)) # add to global scope
        # extra, SCENE_BUBBLE_FILTER for performance
        SCENE_BUBBLE_FILTER = {k[1:] for k in SCENE_SUFFIXES["default"]["end"] if len(k) > 0}
    del f
except Exception as e:
    print("Failed to load and set json/manual_constants.json")
    print("Please fix the file content and try again")
    print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
    raise Exception("Failed to load GBFAL Constants")

# Handle tasks
@dataclass(slots=True)
class TaskManager():
    debug : bool
    is_running : bool
    updater : Updater
    queues : tuple[deque, ...]
    running : deque[asyncio.Task]
    total : int
    finished : int
    print_flag : bool
    elapsed : float
    written_len : int
    def __init__(self : TaskManager, updater : Updater) -> None:
        self.debug = False
        self.is_running = False
        self.updater = updater
        self.queues = (deque(), deque(), deque(), deque(), deque())
        self.running = deque()
        self.total = 0
        self.finished = 0
        self.print_flag = False
        self.elapsed = 0
        self.written_len = 0

    # reinitialize variables
    def reset(self : TaskManager) -> None:
        self.total = 0
        self.finished = 0
        self.is_running = False
        self.print_flag = False

    # add a task to one queue
    def add(self : TaskManager, awaitable : Callable, *, parameters : tuple[Any, ...]|None = None, priority : int = -1) -> None:
        if parameters is not None and not(isinstance(parameters, tuple)):
            raise Exception("Invalid parameters")
        if priority < 0 or priority >= len(self.queues):
            priority = len(self.queues) - 1
        self.queues[priority].append(Task.make(awaitable, parameters))
        self.total += 1

    # return True if all queues are empty
    def queues_are_empty(self : TaskManager) -> bool:
        for q in self.queues:
            if len(q) > 0:
                return False
        return True

    # run tasks in queue
    async def run(self : TaskManager, *, skip : int = 0) -> None:
        if self.is_running:
            self.print("ERROR: run() is already running, ignoring...)")
            return
        self.is_running = True
        start_time : float = time.time()
        self.elapsed : float = start_time
        to_sleep : bool = False
        i : int
        # loop
        while len(self.running) > 0 or not self.queues_are_empty():
            # remove from queue and run
            for i, q in enumerate(self.queues):
                while len(self.running) < CONCURRENT_TASKS and len(q) > 0:
                    try:
                        t : Task = q.popleft()
                        if skip <= 0:
                            if t.parameters is not None:
                                self.running.append(asyncio.create_task(t.awaitable(*t.parameters)))
                            else:
                                self.running.append(asyncio.create_task(t.awaitable()))
                        else:
                            skip -= 1
                    except Exception as e:
                        self.print("Can't start task, the following exception occured in queue", i)
                        self.print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
                        self.finished += 1
                        break
            # check process flags
            await self.updater.process_flags()
            # remove completed tasks
            prev : int = self.finished
            for i in range(len(self.running)):
                t : asyncio.Task = self.running.popleft()
                if t.done():
                    try:
                        t.result()
                    except Exception as e:
                        self.print("The following exception occured:")
                        self.print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
                    self.finished += 1
                    # t is discarded
                else:
                    self.running.append(t) # put back in
            # update status
            if prev != self.finished: # number of finished task changed
                # print t he progress
                self.print_progress()
                # auto save if needed
                if time.time() - self.elapsed >= 3600:
                    if self.updater.modified:
                        self.print("Progress: {} / {} Tasks, autosaving...".format(self.finished, self.total))
                    self.updater.save()
                    self.updater.save_resume()
                    self.elapsed = time.time()
                to_sleep = False
            else:
                to_sleep = True
            # ... and sleep if we haven't finished tasks
            if to_sleep:
                await asyncio.sleep(0.1)
            # if ALL tasks are done, check flags
            if len(self.running) == 0 and self.queues_are_empty():
                await self.updater.process_flags()
        self.print("Complete")
        # finished
        diff : float = time.time() - start_time # elapsed time
        # format to H:M:S
        elapsed_s : int = int(diff)
        h : int = elapsed_s // 3600 # hours
        m : int = (elapsed_s % 3600) // 60 # minutes
        s : int = elapsed_s % 60 # seconds
        strings : list[str] = ["Run time: "]
        if h > 0:
            strings.append(str(h).zfill(2))
            strings.append('h')
        if m > 0:
            strings.append(str(m).zfill(2))
            strings.append('m')
        strings.append(str(s).zfill(2))
        strings.append('s')
        self.reset()
        print("".join(strings))

    # start to run queued tasks
    async def start(self : TaskManager) -> bool:
        if self.is_running or self.queues_are_empty(): # return if already running or no tasks pending
            return False
        await self.run()
        return True

    # print the progression string
    def print_progress(self : TaskManager) -> None:
        if self.running and self.total > 0:
            if self.print_flag:
                sys.stdout.write("\r")
                if self.written_len > 0:
                    sys.stdout.write((" " * self.written_len) + "\r")
            else:
                self.print_flag = True
            if self.debug:
                self.written_len = sys.stdout.write("P:{}/{} | R:{} | Q:{} {} {} {} {}".format(self.finished, self.total, len(self.running), len(self.queues[0]), len(self.queues[1]), len(self.queues[2]), len(self.queues[3]), len(self.queues[4])))
            else:
                self.written_len = sys.stdout.write("Progress: {} / {} Tasks".format(self.finished, self.total))
            sys.stdout.flush()

    # print whatever you want, to use instead of print to handle the \r
    def print(self : TaskManager, *args) -> None:
        if self.print_flag:
            self.print_flag = False
            sys.stdout.write("\r")
            if self.written_len > 0:
                sys.stdout.write((" " * self.written_len) + "\r")
        print(*args)
        self.print_progress()

    # called when CTRL+C is used
    def interrupt(self : TaskManager, *args) -> None:
        if self.total <= 0 or self.finished >= self.total:
            return
        if self.print_flag:
            self.print_flag = False
            sys.stdout.write("\r")
            if self.written_len > 0:
                sys.stdout.write((" " * self.written_len) + "\r")
        print("Process PAUSED")
        print("{} / {} Tasks completed".format(self.finished, self.total))
        print("{} Tasks running".format(len(self.running)))
        for i, q in enumerate(self.queues):
            print("Tasks in queue lv{}: {}".format(i, len(q)))
        if self.updater.modified:
            print("Pending Data is waiting to be saved")
        print("Type 'help' for a command list, or a command to execute, anything else to resume")
        while True:
            s = input(":").lower().split(' ')
            match s[0]:
                case 'help':
                    print("save    - call the save() function")
                    print("exit    - force exit the process, changes won't be saved, but resume file will be updated if used")
                    print("peek    - check the content of data.json. Take two parameters: the index to look at and an id")
                    print("tchange - toggle update_changelog setting")
                case 'save':
                    if not self.updater.modified:
                        print("No changes waiting to be saved")
                    else:
                        self.updater.save()
                    self.updater.save_resume()
                case 'peek':
                    if len(s) < 3:
                        print("missing 1 parameter: ID")
                    elif len(s) < 2:
                        print("missing 2 parameters: index, ID")
                    else:
                        try:
                            d : Any = self.data[s[1]][s[2]]
                            print(s[1], '-', s[2])
                            print(d)
                        except Exception as e:
                            print("Can't read", s[1], '-', s[2])
                            print(e)
                case 'tchange':
                    self.updater.update_changelog = not self.updater.update_changelog
                    print("changelog.json updated list WILL be modified" if self.updater.update_changelog else "changelog.json updated list won't be modified")
                case 'exit':
                    print("Exiting...")
                    os._exit(0)
                case _:
                    print("Process RESUMING...")
                    break

# A queued task
@dataclass(frozen=True, slots=True)
class Task():
    awaitable : Callable
    parameters : tuple[Any, ...]|None

    @classmethod
    def make(cls : Task, awaitable : Callable, parameters : tuple[Any, ...]|None) -> Task:
        return cls(awaitable, parameters)

@dataclass(slots=True)
class TaskStatus():
    index : int
    max_index : int
    err : int
    max_err : int
    running : int
    
    def __init__(self : TaskStatus, max_index : int, max_err : int, *, start : int = 0, running : int = 0):
        self.index = start
        self.max_index = max_index
        self.err = 0
        self.max_err = max_err
        self.running = running

    def get_next_index(self : TaskStatus) -> int:
        i : int = self.index
        self.index += 1
        return i

    def good(self : TaskStatus) -> None:
        self.err = 0

    def bad(self : TaskStatus) -> None:
        self.err += 1

    @property
    def complete(self : TaskStatus) -> bool:
        return self.err >= self.max_err or self.index >= self.max_index

    def finish(self : TaskStatus) -> None:
        self.running -= 1

    @property
    def finished(self : TaskStatus) -> bool:
        return self.running <= 0

@dataclass(slots=True)
class Updater():
    # other init
    client : aiohttp.ClientSession|None
    flags : set[str]
    http_sem : asyncio.Semaphore
    tasks : TaskManager
    use_wiki : bool
    update_changelog : bool
    use_resume : bool
    ignore_file_count : bool
    data : dict[str, Any]
    modified : bool
    resume : dict[str, Any]
    stat_string : str|None
    addition : set[tuple[str, int|str]]
    updated_elements : set[str]
    job_list : dict[str, str]|None
    scene_strings : None|tuple[dict, dict]
    sound_base_strings : list[str, list[str], int, int, int]
    def __init__(self : Updater):
        # other init
        self.client = None # the http client
        self.flags = set() # to contain and manage various flag values
        self.http_sem = asyncio.Semaphore(HTTP_CONN_LIMIT) # http semaphor to limit http connections
        self.tasks = TaskManager(self) # the task manager
        self.use_wiki = False # flag to see if the wiki usable
        self.update_changelog  = True # flag to enable or disable the generation of changelog.json
        self.use_resume = True # flag to use the resume file
        self.ignore_file_count = False # flag to control the count_file function behavior
        self.data = { # data structure
            "version":SAVE_VERSION,
            "uncap_queue":[],
            "valentines":[],
            "characters":{},
            "partners":{},
            "summons":{},
            "weapons":{},
            "shields":{},
            "manaturas":{},
            "enemies":{},
            "skins":{},
            "job":{},
            "job_wpn":{},
            "job_key":{},
            'npcs':{},
            "background":{},
            "mypage_bg":{},
            "title":{},
            "sky_title":{},
            "suptix":{},
            "lookup":{},
            'events':{},
            "skills":{},
            "subskills":{},
            'buffs':{},
            'eventthumb':{},
            "story":{},
            "fate":{},
            "premium":{},
            "npc_replace":{}
        }
        self.load() # load self.data NOW
        self.modified = False # if set to true, data.json will be written on the next call of save()
        self.resume = {} # list of items completed (for the resume file)
        self.stat_string = None # set and updated by make_stats
        self.addition = set() # new elements for changelog.json
        self.updated_elements = set() # set of elements ran through update_element()
        self.job_list = None # job dictionary of id string pair
        self.scene_strings = None # scene string containers
        # sound strings containers
        self.sound_base_strings = []

    ### Utility #################################################################################################################

    # Load data.json
    def load(self : Updater) -> None:
        try:
            # load file
            with open('json/data.json', mode='r', encoding='utf-8') as f:
                data : dict[str, Any] = json.load(f)
                if not isinstance(data, dict):
                    return
            # update if old version
            data = self.retrocompatibility(data)
            # load only expected keys
            k : str
            for k in self.data:
                if k in data:
                    self.data[k] = data[k]
        except OSError as e:
            self.tasks.print(e)
            if input("Continue anyway? (type 'y' to continue):").lower() != 'y':
                os._exit(0)
        except Exception as e:
            self.tasks.print("The following error occured while loading data.json:")
            self.tasks.print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            self.tasks.print(e)
            os._exit(0)
        try:
            with open('json/manual_npc_replace.json', mode='r', encoding='utf-8') as f:
                data : dict[str, str] = json.load(f)
                if not isinstance(data, dict):
                    raise Exception("Not a dictionary")
            if self.data["npc_replace"] != data:
                self.data["npc_replace"] = data
                self.modified = True
        except Exception as e:
            self.tasks.print("Failed to import manual_npc_replace.json")
            self.tasks.print("Exception:", e)

    # make older data.json compatible with newer versions
    def retrocompatibility(self : Updater, data : dict[str, Any]) -> dict[str, Any]:
        version = data.get("version", 0)
        if version == 0:
            self.tasks.print("This version is unsupported and might not work properly")
        data["version"] = SAVE_VERSION
        return data

    # Save data.json and changelog.json (only if self.modified is True)
    def save(self : Updater) -> None:
        try:
            if self.modified:
                self.modified = False
                # remove dupes from queues
                for k in QUEUE_KEY:
                    self.data[k] = list(dict.fromkeys(self.data[k]))
                # json.dump isn't used to keep the file small AND easily editable by hand
                with open('json/data.json', mode='w', encoding='utf-8') as outfile:
                    # custom json indentation
                    outfile.write("{\n")
                    keys : list[str] = list(self.data.keys())
                    k : str
                    v : Any
                    for k, v in self.data.items():
                        outfile.write('"{}":\n'.format(k))
                        if isinstance(v, int): # INT
                            outfile.write('{}\n'.format(v))
                            if k != keys[-1]:
                                outfile.write(",")
                            outfile.write("\n")
                        elif isinstance(v, list): # LIST
                            outfile.write('[\n')
                            d : Any
                            for d in v:
                                json.dump(d, outfile, separators=(',', ':'), ensure_ascii=False)
                                if d is not v[-1]:
                                    outfile.write(",")
                                outfile.write("\n")
                            outfile.write("]")
                            if k != keys[-1]:
                                outfile.write(",")
                            outfile.write("\n")
                        elif isinstance(v, dict): # DICT
                            outfile.write('{\n')
                            last : list[str] = list(v.keys())
                            if len(last) > 0:
                                last = last[-1]
                                i : int
                                d : Any
                                for i, d in v.items():
                                    outfile.write('"{}":'.format(i))
                                    json.dump(d, outfile, separators=(',', ':'), ensure_ascii=False)
                                    if i != last:
                                        outfile.write(",")
                                    outfile.write("\n")
                            outfile.write("}")
                            if k != keys[-1]:
                                outfile.write(",")
                            outfile.write("\n")
                    outfile.write("}")
                # changelog.json
                stat : str|None
                new : dict[str, list[Any]]
                issues : list[str]
                help : bool
                try: # load its content
                    with open('json/changelog.json', mode='r', encoding='utf-8') as f:
                        data = json.load(f)
                        stat = data.get('stat', None)
                        issues = data.get('issues', [])
                        help = data.get('help', False)
                        new = data.get('new', {})
                except:
                    new = {}
                    stat = None
                    issues = []
                    help = False
                if self.update_changelog and len(self.addition) > 0: # update new content
                    # get date of today
                    now : str = datetime.now(UTC).strftime('%Y-%m-%d')
                    if now in new: # if date present
                        existing : set[tuple[str, int|str]] = {(e[0], e[1]) for e in new[now]} # get old data
                        for el in self.addition:
                            if el not in existing:
                                new[now].append(list(el))
                    else:
                        new[now] = [list(el) for el in self.addition] # else just set new data
                    # sort keys
                    keys : list[str]= list(new.keys())
                    keys.sort(reverse=True)
                    if len(keys) > 5: # and remove oldest
                        keys = keys[:5]
                    new = {k:new[k] for k in keys}
                    # sort updated one
                    new[now] = sorted(new[now], key=lambda x: (0 if isinstance(x[1], int) else 1, x[1], x[0]), reverse=True)
                    # clear self.addition
                    self.addition = set()
                # update stat
                if self.stat_string is not None:
                    stat = self.stat_string
                with open('json/changelog.json', mode='w', encoding='utf-8') as outfile: # the timestamp is upated below
                    json.dump({'timestamp':int(datetime.now(timezone.utc).timestamp()*1000), 'new':new, 'stat':stat, 'issues':issues, 'help':help}, outfile, indent=2, separators=(',', ':'), ensure_ascii=False)
                if self.update_changelog:
                    self.tasks.print("data.json and changelog.json updated")
                else:
                    self.tasks.print("data.json updated")
        except Exception as e:
            self.tasks.print(e)
            self.tasks.print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    def add(self : Updater, element_id : str, element_type : int|str) -> bool:
        r : bool = (element_id, element_type) in self.addition
        self.addition.add((element_id, element_type))
        return r

    # Generic GET request function
    async def get(self : Updater, url : str) -> Any:
        async with self.http_sem:
            response : aiohttp.HTTPResponse = await self.client.get(url, headers={'connection':'keep-alive'})
            async with response:
                if response.status != 200:
                    raise Exception("HTTP error {}".format(response.status))
                return await response.content.read()

    # Same as GET but for gbf.wiki
    async def get_wiki(self : Updater, url : str, *, get_json : bool = False) -> Any:
        async with self.http_sem:
            response : aiohttp.HTTPResponse = await self.client.get(url, headers={'User-Agent':USER_AGENT}, timeout=10)
            async with response:
                if response.status != 200: raise Exception("HTTP error {}".format(response.status))
                if get_json:
                    return await response.json()
                return await response.content.read()

    # Generic HEAD request function
    async def head(self : Updater, url : str) -> Any:
        async with self.http_sem:
            response : aiohttp.HTTPResponse = await self.client.head(url, headers={'connection':'keep-alive'})
            async with response:
                if response.status != 200:
                    raise Exception("HTTP error {}".format(response.status))
                return response.headers

    # wrapper of head() if the exception isn't needed (return None in case of error instead)
    async def head_nx(self : Updater, url : str):
        # copy paste to avoid a needless functions call and exception
        async with self.http_sem:
            try:
                response : aiohttp.HTTPResponse = await self.client.head(url, headers={'connection':'keep-alive'})
            except Exception as e:
                self.tasks.print("The following exception occured in head_nx():\nURL: " + url + "\n" + "".join(traceback.format_exception(type(e), e, e.__traceback__)))
                return None
            async with response:
                if response.status != 200:
                    return None
                return response.headers

    # Extract json data from a GBF animation manifest file
    async def processManifest(self, file : str, verify_file : bool = False) -> list:
        # request the file
        manifest = (await self.get(MANIFEST + file + ".js")).decode('utf-8')
        # fine start and end of object part
        st = manifest.find('manifest:') + len('manifest:')
        ed = manifest.find(']', st) + 1
        # format and load as json
        data : dict[str, str] = json.loads(manifest[st:ed].replace('Game.imgUri+', '').replace('src:', '"src":').replace('type:', '"type":').replace('id:', '"id":'))
        # list image srcs
        res : list[str] = [src for l in data if (src := l['src'].split('?')[0].split('/')[-1])]
        # check if at least one file is accessible
        if verify_file:
            path : list[str] = [IMG, "sp/cjs/", ""]
            for k in res:
                path[2] = k
                try:
                    await self.head("".join(path))
                    return res
                except:
                    pass
            raise Exception("Invalid Spritesheets")
        return res

    # test if the wiki is usable
    async def test_wiki(self : Updater) -> bool:
        try:
            t : str = (await self.get_wiki("https://gbf.wiki")).decode('utf-8') # request main page
            if "<p id='status'>50" in t or 'gbf.wiki unavailable' in t: # check if down
                return False
            return True
        except: # bad request or cloudflare = down/not usable
            return False

    ### Main #################################################################################################################

    # called by -run
    async def run(self : Updater) -> None:
        self.flags.add("run_process")
        i : int
        j : int
        r : int
        ts : TaskStatus
        # jobs
        if self.job_list is not None:
            jkeys = [k for k in list(self.job_list.keys()) if (k not in self.data['job'] or self.data['job'][k] == 0)]
            # Adding jobs added by other means
            for k in self.data['job']:
                if self.data['job'][k] == 0 and k not in jkeys:
                    jkeys.append(k)
            for k in jkeys:
                self.tasks.add(self.update_job, parameters=(k,))
        # skills
        ts = TaskStatus(10000, 12)
        highest : int = 0
        try:
            highest = max([int(k) for k in self.data["skills"]])
        except:
            pass
        for i in range(10):
            self.tasks.add(self.search_skill, parameters=(ts, highest))
        # buffs
        for i in range(10):
            for j in range(4):
                ts = TaskStatus(i*1000+250*(j+1), 20, start=i*1000+250*j)
                n : int
                for n in range(3):
                    self.tasks.add(self.search_buff, parameters=(ts, ))
        # manatura
        ts = TaskStatus(1000, 4)
        for i in range(4):
            self.tasks.add(self.search_manatura, parameters=(ts, ))
        # npc
        ts = TaskStatus(10000, 90)
        for i in range(20):
            self.tasks.add(self.search_generic, parameters=(ts, 'npcs', "399{}000", 4, [
                "img/sp/quest/scene/character/body/{}.png",
                "img/sp/quest/scene/character/body/{}_shadow.png",
                "img/sp/quest/scene/character/body/{}_a.png",
                "img/sp/raid/navi_face/{}.png",
                "img/sp/assets/npc/b/{}_01.png",
                "sound/voice/{}_v_001.mp3",
                "sound/voice/{}_boss_v_1.mp3",
                "sound/voice/{}_boss_v_10.mp3",
                "sound/voice/{}_boss_v_20.mp3",
            ]))
        # special npc
        ts = TaskStatus(10000, 2)
        for i in range(10):
            self.tasks.add(self.search_generic, parameters=(ts, 'npcs', "305{}000", 4, ["img/sp/quest/scene/character/body/{}.png"]))
        #rarity of various stuff
        for r in range(1, 5):
            # weapons
            for j in range(10):
                ts = TaskStatus(1000, 20)
                for i in range(5):
                    self.tasks.add(self.search_generic, parameters=(ts, 'weapons', "10"+str(r)+"0{}".format(j) + "{}00", 3, ["img/sp/assets/weapon/m/{}.jpg"]))
            # shields
            for j in range(2):
                ts = TaskStatus(1000, 5)
                for i in range(5):
                    self.tasks.add(self.search_generic, parameters=(ts, 'shields', str(r)+"{}", 3, ["img/sp/assets/shield/m/{}.jpg"]))
            # summons
            ts = TaskStatus(1000, 20)
            for i in range(5):
                self.tasks.add(self.search_generic, parameters=(ts, 'summons', "20"+str(r)+"0{}000", 3, ["img/sp/assets/summon/m/{}.jpg"]))
            if r > 1:
                # characters
                ts = TaskStatus(1000, 20)
                for i in range(5):
                    self.tasks.add(self.search_generic, parameters=(ts, 'characters', "30"+str(r)+"0{}000", 3, ["img/sp/assets/npc/m/{}_01.jpg"]))
                # partners
                ts = TaskStatus(1000, 20)
                for i in range(5):
                    self.tasks.add(self.search_generic, parameters=(ts, 'partners', "38"+str(r)+"0{}000", 3, [
                        "img/sp/assets/npc/raid_normal/{}_01.jpg",
                        "js/model/manifest/phit_{}.js",
                        "js/model/manifest/nsp_{}_01.js"
                    ]))
        # other partners
        for r in range(8, 10):
            ts = TaskStatus(1000, 20)
            for i in range(5):
                self.tasks.add(self.search_generic, parameters=(ts, 'partners', "38"+str(r)+"0{}000", 3, [
                    "img/sp/assets/npc/raid_normal/{}_01.jpg",
                    "js/model/manifest/phit_{}.js",
                    "js/model/manifest/nsp_{}_01.js"
                ]))
        # skins
        ts = TaskStatus(1000, 20)
        for i in range(5):
            self.tasks.add(self.search_generic, parameters=(ts, 'skins', "3710{}000", 3, ["js/model/manifest/npc_{}_01.js"]))
        # enemies
        main : int
        sub : int
        for main in range(1, 10):
            for sub in range(1, 4):
                ts = TaskStatus(10000, 40)
                prefix : str = str(main) + str(sub)
                for i in range(10):
                    self.tasks.add(self.search_enemy, parameters=(ts, prefix))
        # backgrounds
        # event & common
        ev : str
        for ev in ("event_{}", "common_{}"):
            ts = TaskStatus(1000, 10)
            for j in range(5):
                self.tasks.add(self.search_generic, parameters=(ts, 'background', ev, 3 if ev.startswith("common_") else 1, ["img/sp/raid/bg/{}.jpg"]))
        # main
        ts = TaskStatus(1000, 10)
        for j in range(5):
            self.tasks.add(self.search_generic, parameters=(ts, 'background', "main_{}", 1, ["img/sp/guild/custom/bg/{}.png"]))
        # others
        ss : str
        for ss in ("ra", "rb", "rc"):
            ts = TaskStatus(1000, 50)
            for j in range(5):
                self.tasks.add(self.search_generic, parameters=(ts, 'background', "{}"+ss, 2, ["img/sp/raid/bg/{}_1.jpg"]))
        bgt : tuple[str, str]
        for bgt in (("e", ""), ("e", "r"), ("f", ""), ("f", "r"), ("f", "ra"), ("f", "rb"), ("f", "rc"), ("e", "r_3_a"), ("e", "r_4_a")):
            ts = TaskStatus(1000, 50)
            for j in range(5):
                self.tasks.add(self.search_generic, parameters=(ts, 'background', bgt[0]+"{}"+bgt[1], 3, ["img/sp/raid/bg/{}_1.jpg"]))
        # mypage island background
        for i in (range(0, 40), range(70, 75)):
            for j in i:
                ts = TaskStatus(1000, 20)
                self.tasks.add(self.search_generic, parameters=(ts, 'mypage_bg', str(j).zfill(2) + "{}", 3, ["img/sp/mypage/town/{}/bg.jpg"]))
        # titles
        ts = TaskStatus(1000, 5)
        for i in range(3):
            self.tasks.add(self.search_generic, parameters=(ts, 'title', "{}", 1, ["img/sp/top/bg/bg_{}.jpg"]))
        # sky compass title
        ts = TaskStatus(1000, 8)
        for i in range(2):
            self.tasks.add(self.search_generic, parameters=(ts, 'sky_title', "{}", 1, ["assets/archives/galleries/{}/detail_s.png"], "https://media.skycompass.io/"))
        # subskills
        ts = TaskStatus(1000, 5)
        for i in range(3):
            self.tasks.add(self.search_generic, parameters=(ts, 'subskills', "{}", 1, ["img/sp/assets/item/ability/s/{}_1.jpg"]))
        # suptix
        ts = TaskStatus(1000, 15)
        for i in range(3):
            self.tasks.add(self.search_generic, parameters=(ts, 'suptix', "{}", 1, ["img/sp/gacha/campaign/surprise/top_{}.jpg"]))
        # start the tasks
        await self.tasks.start()

    # generic search for assets
    async def search_generic(self : Updater, ts : TaskStatus, index : str, file : str, zfill : int, paths : list[str], endpoint : str = ENDPOINT) -> None:
        data = self.data[index] # reference
        while not ts.complete:
            i : int = ts.get_next_index()
            f : str = file.format(str(i).zfill(zfill)) # while the letter f is used to signify the file, it's also the id used in the index
            if f in data: # if indexed
                if data[f] == 0 and index in UPDATABLE: # set to update if no data and it's updatable
                    self.tasks.print("In need of update:", f, "for index:", index)
                    self.tasks.add(self.update_element, parameters=(f, index), priority=3)
                ts.good()
            else:
                j : int
                path : str
                for j, path in enumerate(paths): # request for each path
                    try:
                        await self.head(endpoint + path.format(f))
                        ts.good()
                        self.tasks.print("Found:", f, "for index:", index)
                        data[f] = 0 # set data to 0 (until it's updated)
                        if index in ADD_SINGLE_ASSET: # these index don't have changelog ID
                            self.add(index+":"+f, index)
                        self.modified = True
                        self.tasks.add(self.update_element, parameters=(f, index), priority=3) # call update task for that element
                        break
                    except: # request failed
                        if j == len(paths) - 1: # if it was the last path
                            ts.bad()

    # Search for enemies
    async def search_enemy(self : Updater, ts : TaskStatus, prefix : str) -> None:
        enemies = self.data['enemies'] # reference
        while not ts.complete:
            i : int = ts.get_next_index()
            fi : str = prefix + str(i).zfill(4)
            found : bool = False
            for n in range(1, 4):
                sfi : str = fi + str(n)
                if sfi in enemies:
                    if enemies[sfi] == 0:
                        self.tasks.print("In need of update:", sfi, "for index:", 'enemies')
                        self.tasks.add(self.update_element, parameters=(sfi, 'enemies'), priority=3)
                    found = True
                else:
                    #Note: 6200483, 6099502 and possibly more got no icons and raid_appear must be checked instead
                    try:
                        await self.head(ENDPOINT + "img/sp/assets/enemy/s/{}.png".format(sfi))
                        self.tasks.print("Found:", sfi, "for index:", 'enemies')
                        enemies[sfi] = 0 # set data to 0 (until it's updated)
                        self.modified = True
                        self.tasks.add(self.update_element, parameters=(sfi, 'enemies'), priority=3) # call update task for that element
                        found = True
                    except: # request failed
                        pass
            if found:
                ts.good()
            else:
                ts.bad()

    # Search for new skills
    async def search_skill(self, ts : TaskStatus, highest : int) -> None: # skill search
        skills = self.data['skills'] # reference
        # highest is the highest registered id
        # it's used to keep going if we know there are further ID to be found later
        # this way, is there are large gaps of unused skills, we can still keep going
        while not ts.complete:
            i : int = ts.get_next_index()
            fi = str(i).zfill(4) # formatted id
            if fi in skills: # already indexed
                ts.good()
            else:
                found : bool = False
                s : str
                for s in ("_1.png", "_2.png", "_3.png", "_4.png", "_5.png", ".png"): # request for each (we only need one good one), ".png" is last because it's rarely used nowadays
                    try:
                        headers : Any = await self.head(IMG + "sp/ui/icon/ability/m/" + str(i) + s)
                        if 'content-length' in headers and int(headers['content-length']) < 200:
                            raise Exception()
                        ts.good()
                        found = True
                        skills[fi] = [[str(i) + s.split('.')[0]]]
                        self.add(fi, ADD_SKILL)
                        self.modified = True
                        break
                    except:
                        pass
                if not found and i > highest:
                    ts.bad()

    # Search for new manaturas
    async def search_manatura(self, ts : TaskStatus) -> None:
        manaturas = self.data['manaturas'] # reference
        path : list[str] = [IMG, "sp/assets/familiar/m/", None, "", ".jpg"]
        while not ts.complete:
            i : int = ts.get_next_index()
            fi : str = str(i).zfill(4) # formatted id
            if fi in manaturas:
                ts.good()
            else:
                try:
                    path[2] = str(i)
                    await self.head("".join(path))
                    manaturas[fi] = [[str(i)]]
                    self.add(fi, ADD_MANATURA)
                    self.modified = True
                    self.tasks.print("Found:", fi, "for index:", "manaturas")
                    ts.good()
                except:
                    ts.bad()

    # Search for new buffs
    async def search_buff(self, ts : TaskStatus) -> None:
        buffs = self.data['buffs'] # reference
        path : list[str] = [IMG, "sp/ui/icon/status/x64/status_", None, "", ".png"]
        while not ts.complete:
            i : int = ts.get_next_index()
            fi : str = str(i).zfill(4) # formatted id
            if fi in buffs: # already indexed
                if buffs[fi] == 0:
                    await self.prepare_update_buff(fi, priority=3) # call update task for that element
                ts.good()
                continue
            found : bool = False
            slist : list[str] = BUFF_LIST_EXTENDED if i >= 1000 else BUFF_LIST
            path[2] = str(i)
            for s in slist:
                path[3] = s
                try:
                    # make sure the file size is right, some buff icons are empty transparent files
                    if int((await self.head("".join(path))).get('content-length', 0)) < 200:
                        raise Exception()
                    buffs[fi] = [[path[2]], [s]]
                    found = True
                    break
                except:
                    pass
            if found:
                ts.good()
                self.tasks.print("Found:", fi, "for index:", "buffs")
                await self.prepare_update_buff(fi, priority=3) # call update task for that element
            else:
                ts.bad()

    # Prepare the update_buff tasks
    async def prepare_update_buff(self : Updater, element_id : str, *, priority : int = -1) -> None:
        buffs = self.data['buffs'] # reference
        i : int = int(element_id)
        fi : str = str(i)
        if buffs.get(element_id, 0) == 0: # init array
            buffs[element_id] = [[str(int(element_id))], []]
        known : set[str] = set(buffs.get(element_id, [[], []])[1])
        path : list[str] = [IMG, "sp/ui/icon/status/x64/status_", fi, "", ".png"]
        ts : TaskStatus = TaskStatus(1, 1, running=6)
        
        # add tasks to verify variations
        for mode in range(6):
            if (mode == 0 and "" in known) or (mode == 2 and i < 1000): # skip these if the condition matches
                ts.finish()
                continue
            self.tasks.add(self.update_buff, parameters=(mode, ts, path, element_id, fi, known), priority=priority)

    # Subroutine of prepare_update_buff to check for varitions
    # Mode control which variation to check
    # Mode 0 is only if "" is not in known files, Mode 2 is only for IDs lesser than 1000
    async def update_buff(self : Updater, mode : int, ts : TaskStatus, path : list[str], element_id : str, fi : str, known : set[str]) -> None:
        err : int = 0
        n : int = 0
        m : int
        match mode:
            case 0:
                # default
                path[3] = ""
                try:
                    if int((await self.head("".join(path))).get('content-length', 0)) < 200:
                        raise Exception()
                    known.add("")
                except:
                    pass
            case 1:
                # _1, _2...
                while err < 3 and n < 10:
                    path[3] = "_" + str(n)
                    if path[3] in known:
                        err = 0
                    else:
                        try:
                            if int((await self.head("".join(path))).get('content-length', 0)) < 200:
                                raise Exception()
                            known.add("_" + str(n))
                            err = 0
                        except:
                            err += 1
                    n += 1
            case 2:
                # 1, 2...
                while err < 3:
                    path[3] = str(n)
                    if path[3] in known:
                        err = 0
                    else:
                        try:
                            if int((await self.head("".join(path))).get('content-length', 0)) < 200:
                                raise Exception()
                            known.add(str(n))
                            err = 0
                        except:
                            err += 1
                    n += 1
            case 3:
                errlimit : int = 10 if element_id in ("3000", "1008") else 3
                for x in range(1, 10):
                    # _10, _11, _20, _30...
                    n = 10 * x
                    m = n + 10
                    err = 0
                    while err < errlimit and n < m:
                        path[3] = "_" + str(n)
                        if path[3] in known:
                            err = 0
                        else:
                            try:
                                if int((await self.head("".join(path))).get('content-length', 0)) < 200:
                                    raise Exception()
                                known.add("_" + str(n))
                                err = 0
                            except:
                                err += 1
                        n += 1
            case 4:
                for x in range(1, 8): # stopping at _7XX included
                    # _101, _102...
                    n = 0
                    err = 0
                    while err < 3:
                        path[3] = "_" + str(x) + str(n).zfill(2)
                        if path[3] in known:
                            err = 0
                        else:
                            try:
                                if int((await self.head("".join(path))).get('content-length', 0)) < 200:
                                    raise Exception()
                                known.add("_" + str(x) + str(n).zfill(2))
                                err = 0
                            except:
                                err += 1
                                if err == 3 and n < 10:
                                    n = 9
                                    err = 0
                        n += 1
                # exception, testing for _110
                path[3] = "_110"
                if path[3] not in known:
                    try:
                        if int((await self.head("".join(path))).get('content-length', 0)) < 200:
                            raise Exception()
                        known.add("_110")
                    except:
                        pass
            case 5:
                baselimit : int = 15 if element_id in ("6579",) else 8
                errlimit : int = 6 if element_id in ("1019",) else 3
                for x in range(0, baselimit):
                    #_0_1, _0_2...
                    n = 0
                    err = 0
                    while err < errlimit:
                        path[3] = "_" + str(x) + "_" + str(n)
                        if path[3] in known:
                            err = 0
                        else:
                            try:
                                if int((await self.head("".join(path))).get('content-length', 0)) < 200:
                                    raise Exception()
                                known.add("_" + str(x) + "_" + str(n))
                                err = 0
                            except:
                                err += 1
                        n += 1
        ts.finish()
        buffs = self.data['buffs'] # reference
        if ts.finished and len(known) > len(buffs.get(element_id, [[], []])[1]):
            buffs[element_id] = [[str(int(element_id))], list(known)]
            buffs[element_id][1].sort(key=lambda x: str(x.count('_'))+"".join([j.zfill(3) for j in x.split('_')]))
            self.modified = True
            self.add(element_id, ADD_BUFF)
            self.flags.add("found_buff")
            self.tasks.print("Updated:", element_id, "for index:", 'buffs')

    ### Update #################################################################################################################

    # Attempt to update all given element ids
    async def update_all(self : Updater, elements : list[str]) -> None:
        element_id : str
        for element_id in elements:
            self.tasks.add(self.update_element, parameters=(element_id, None))
        if await self.tasks.start():
            if len(self.addition) > 0: # update lookup
                await self.lookup()

    # Update element data by calling the corresponding function
    async def update_element(self : Updater, element_id : str, index : str|None) -> None:
        # Check if it has already been updated by the current instance, then skip if it's the case
        if element_id in self.updated_elements:
            return
        self.updated_elements.add(element_id)
        # No index provided, deduce index
        if index is None: 
            if element_id in self.data.get('background', {}):
                index = 'background'
            elif len(element_id) == 10:
                if element_id[0] == '2':
                    index = 'summons'
                elif element_id[0] == '1':
                    index = 'weapons'
                elif element_id.startswith('39') or element_id.startswith('305'):
                    index = 'npcs'
                elif element_id.startswith('38'):
                    index = 'partners'
                elif element_id.startswith('371'):
                    index = 'skins'
                elif element_id.startswith('3'):
                    index = 'characters'
            elif len(element_id) == 7:
                index = 'enemies'
            elif len(element_id) == 6:
                index = 'job'
        # Call function corresponding the index
        match index:
            case 'background':
                await self.update_background(element_id)
            case 'summons':
                await self.update_summon(element_id)
            case 'weapons':
                await self.update_weapon(element_id)
            case 'shields':
                await self.update_shield(element_id)
            case 'npcs':
                await self.update_npc(element_id)
            case 'partners':
                if element_id.endswith("000"):
                    ts : TaskStatus = TaskStatus(1000, -1) # partner is separated in ten, because of the heavy load
                    for i in range(10):
                        self.tasks.add(self.update_partner, parameters=(ts, element_id))
                else:
                    start_index : int = int(element_id[-3:])
                    await self.update_partner(
                        TaskStatus(start_index + 1, 1, start=start_index),
                        element_id[:-3] + "000"
                    )
            case 'characters'|'skins':
                await self.update_character(element_id)
            case 'enemies':
                await self.update_enemy(element_id)
            case 'job':
                await self.update_job(element_id)
            case _:
                pass

    # Update Enemy data
    async def update_enemy(self : Updater, element_id : str) -> None:
        enemies = self.data['enemies'] # reference
        # get existing file_count
        try:
            if self.ignore_file_count: raise Exception()
            file_count = self.count_file(enemies[element_id])
        except:
            file_count = 0
        # Make empty container
        data = [[], [], [], [], [], []] # general, sprite, appear, ehit, esp, esp_all
        # icon
        try:
            await self.head(IMG + "sp/assets/enemy/s/{}.png".format(element_id))
            data[BOSS_GENERAL].append("{}".format(element_id))
        except:
            try:
                await self.head(IMG + "sp/assets/enemy/m/{}.png".format(element_id))
                data[BOSS_GENERAL].append("{}".format(element_id))
            except:
                pass
        # sprite
        try:
            fn = "enemy_{}".format(element_id)
            data[BOSS_SPRITE] += await self.processManifest(fn)
        except:
            pass
        # appear
        for k in ("", "_2", "_3", "_4", "_5", "_6", "_7", "_8", "_9", "_shade"):
            try:
                fn = "raid_appear_{}{}".format(element_id, k)
                data[BOSS_APPEAR] += await self.processManifest(fn)
            except:
                pass
        if self.count_file(data) == 0:
            return
        # ehit
        try:
            fn = "ehit_{}".format(element_id)
            data[BOSS_HIT] += await self.processManifest(fn)
        except:
            pass
        # esp
        for i in range(0, 20):
            try:
                fn = "esp_{}_{}".format(element_id, str(i).zfill(2))
                data[BOSS_SP] += await self.processManifest(fn)
            except:
                pass
            try:
                fn = "esp_{}_{}_all".format(element_id, str(i).zfill(2))
                data[BOSS_SP_ALL] += await self.processManifest(fn)
            except:
                pass
        if self.count_file(data) > file_count:
            self.modified = True
            enemies[element_id] = data
            self.add(element_id, ADD_BOSS)
            self.tasks.print("Updated:", element_id, "for index:", 'enemies')
            self.remove_from_uncap_queue(element_id)

    # Update Background data
    async def update_background(self : Updater, element_id : str) -> None:
        backgrounds = self.data['background'] # reference
        modified : bool = False
        data : list[list[str]]
        try: # retrieve container if it exists or make new one
            if isinstance(backgrounds[element_id], list):
                data = backgrounds[element_id]
            else:
                data = [[]]
        except: # it shouldn't fail, but just in case
            data = [[]]
        # 2 paths depending on the background file name (aka element_id)
        if element_id.startswith("event_") or element_id.startswith("main_") or element_id.startswith("common_"):
            path : str
            # set path
            if element_id.startswith("main_"):
                path = "sp/guild/custom/bg/{}.png"
            else:
                path = "sp/raid/bg/{}.jpg"
            s : str
            # for each suffix
            for s in ("", "_a", "_b", "_c"):
                f : str = element_id + s
                if f in data[0]: # known, we skip
                    continue
                elif s == "": # empty, we know it probably exists (this function is likely called from run() or from existing data)
                    data[0].append(f)
                    modified = True
                    self.add(f, ADD_BG)
                else: # request for given suffix
                    try:
                        await self.head(IMG + path.format(f))
                        data[0].append(f)
                        modified = True
                        self.add(f, ADD_BG)
                    except:
                        break
        else: # type 2, these backgrouns always come 3 per 3 usually, no need to check
            if len(data[0]) != 3:
                data[0] = [element_id+"_1",element_id+"_2",element_id+"_3"]
                modified = True
                for f in data[0]: # set to changelog for each
                    self.add(f, ADD_BG)
        if modified:
            data[0].sort()
            self.modified = True
            backgrounds[element_id] = data
            self.tasks.print("Updated:", element_id, "for index:", 'background')
            self.remove_from_uncap_queue(element_id)

    # Update Summon data
    async def update_summon(self, element_id : str) -> None:
        summons = self.data['summons'] # reference
        # get existing file_count
        try:
            if self.ignore_file_count: raise Exception()
            file_count = self.count_file(summons[element_id])
        except:
            file_count = 0
        # Set container
        data : list[list[str]] = [[], [], [], []] # general, call, damage, mypage
        uncaps : list[str] = []
        fn : str
        # main sheet
        uncap : str
        for uncap in ("", "_02", "_03", "_04"):
            try:
                fn = "{}_{}".format(element_id, uncap)
                await self.head(IMG + "sp/assets/summon/m/{}{}.jpg".format(element_id, uncap))
                data[SUM_GENERAL].append("{}{}".format(element_id, uncap))
                uncaps.append(uncap if uncap != "" else "")
                if uncap == "":
                    uncaps.append("_01")
            except:
                break
        if len(uncaps) == 0 and element_id not in CUT_CONTENT:
            return
        if len(data[SUM_GENERAL]) == 0 and element_id in CUT_CONTENT:
            data[SUM_GENERAL].append(element_id)
            uncaps = ["", "_01"]
        # attack
        u : str
        m : str
        for u in uncaps:
            for m in ("", "_a", "_b", "_c", "_d", "_e"):
                try:
                    fn = "summon_{}{}{}_attack".format(element_id, u, m)
                    data[SUM_CALL] += await self.processManifest(fn)
                except:
                    pass
        data[SUM_CALL] = list(dict.fromkeys(data[SUM_CALL]))
        # damage
        try:
            data[SUM_DAMAGE] += await self.processManifest("summon_{}".format(element_id)) # old summons
        except:
            pass
        for u in uncaps:
            for m in ("", "_a", "_b", "_c", "_d", "_e"):
                try:
                    fn = "summon_{}{}{}_damage".format(element_id, u, m)
                    data[SUM_DAMAGE] += await self.processManifest(fn)
                except:
                    pass
        data[SUM_DAMAGE] = list(dict.fromkeys(data[SUM_DAMAGE]))
        # mypage
        for u in uncaps:
            try:
                if u == "_01":
                    continue
                fn = "mypage_{}{}".format(element_id, u)
                data[SUM_MYPAGE] += await self.processManifest(fn)
            except:
                pass
        data[SUM_MYPAGE] = list(dict.fromkeys(data[SUM_MYPAGE]))
        if self.count_file(data) > file_count:
            self.modified = True
            summons[element_id] = data
            self.add(element_id, ADD_SUMM)
            self.tasks.print("Updated:", element_id, "for index:", 'summons')
            self.remove_from_uncap_queue(element_id)

    # Art check system for characters. Detect gendered arts, etc...
    async def artCheck(self : Updater, element_id : str, style : str, uncaps : list[str]) -> dict[str, list[bool]]:
        if element_id.startswith("38"):
            uncaps = ["01", "02", "03", "04"]
        flags : dict[str, list[bool]] = {}
        i : int
        for i in (0, 80, 90):
            j : int = 1
            while j < 9:
                uncap : str = str(i + j).zfill(2)
                if (uncap[0] == "0" and uncap not in uncaps) or (uncap[0] != "0" and element_id.startswith("38")):
                    break
                tasks : dict[tuple[str, str, str, str], asyncio.Task] = {}
                g : str
                m : str
                n : str
                async with asyncio.TaskGroup() as tg:
                    for g in ("_1", ""): # gender
                        for m in ("_101", ""): # multi
                            for n in ("_01", ""): # null
                                tasks[(uncap, g, m, n)] = tg.create_task(self.head_nx(IMG + "sp/assets/npc/raid_normal/{}_{}{}{}{}{}.jpg".format(element_id, uncap, style, g, m, n)))
                positive : bool = False
                for tup, task in tasks.items():
                    if task.result() is not None:
                        positive = True
                        uncap, g, m, n = tup
                        if uncap not in flags:
                            flags[uncap] = [False, False, False]
                        flags[uncap][0] = flags[uncap][0] or (g == "_1")
                        flags[uncap][1] = flags[uncap][1] or (m == "_101")
                        flags[uncap][2] = flags[uncap][2] or (n == "_01")
                if not positive:
                    break
                j += 1
        return flags

    # Update character and skin data
    async def update_character(self : Updater, element_id : str) -> None:
        index : str = "skins" if element_id.startswith("371") else "characters"
        chara_data = self.data[index] # reference
        # get existing file_count
        try:
            
            if self.ignore_file_count: raise Exception()
            file_count = self.count_file(chara_data[element_id])
        except:
            file_count = 0
        # init
        data : list[list[str]] = [[], [], [], [], [], [], [], [], [], []] # sprite, phit, sp, aoe, single, general, sd, scene, sound, mypage
        if element_id in chara_data and chara_data[element_id] != 0:
            data[CHARA_SCENE] = chara_data[element_id][CHARA_SCENE]
            data[CHARA_SOUND] = chara_data[element_id][CHARA_SOUND]
        for style in ("", "_st2"):
            uncaps = []
            sheets = []
            altForm = False
            if index == "skins" and style != "": # skin & style check
                break
            # # # Main sheets
            tid : str = CHARA_SPECIAL_REUSE.get(element_id, element_id) # special substitution (mostly for bobobo)
            for uncap in ("01", "02", "03", "04"):
                for gender in ("", "_0", "_1"):
                    for ftype in ("", "_s2", "_0", "_1"):
                        for form in ("", "_f", "_f1", "_f2"):
                            try:
                                fn = "npc_{}_{}{}{}{}{}".format(tid, uncap, style, gender, form, ftype)
                                sheets += await self.processManifest(fn)
                                if form == "":
                                    uncaps.append(uncap)
                                else:
                                    altForm = True
                            except:
                                if form == "":
                                    break
            data[CHARA_SPRITE] += sheets
            if len(uncaps) == 0:
                if style == "":
                    return False
                continue
            # # # Assets
            # arts
            flags : dict[str, list[bool]] = await self.artCheck(element_id, style, uncaps)
            targets : list[str] = []
            sd : list[str] = []
            for uncap in flags:
                base_fn = "{}_{}{}".format(element_id, uncap, style)
                # sprites
                sd.append(base_fn)
                # other portraits
                uf = flags[uncap]
                for g in (["", "_0", "_1"] if (uf[0] is True) else [""]):
                    for m in (["", "_101", "_102", "_103", "_104", "_105"] if (uf[1] is True) else [""]):
                        for n in (["", "_01", "_02", "_03", "_04", "_05", "_06"] if (uf[2] is True) else [""]):
                            for af in (["", "_f", "_f1", "_f2"] if altForm else [""]):
                                targets.append(base_fn + af + g + m + n)
                    # different sprites
                    if g != "":
                        try:
                            await self.head(IMG + "/sp/assets/npc/sd/" + base_fn + g + ".png")
                            sd.append(base_fn + g)
                        except:
                            pass
            data[CHARA_GENERAL] += targets
            data[CHARA_SD] += sd
            if len(targets) == 0:
                if style == "":
                    return False
                continue
            # # # Other sheets
            # mypage
            sheets = []
            for uncap in flags:
                try:
                    fn = "mypage_{}_{}{}".format(tid, uncap, style)
                    data[CHARA_MYPAGE] += await self.processManifest(fn)
                except:
                    pass
            sheets = list(dict.fromkeys(sheets)) # remove dupes
            data[CHARA_MYPAGE] += sheets
            # attack
            targets = [""]
            for i in range(1, len(uncaps)):
                targets.append("_" + uncaps[i])
            sheets = []
            if tid == MALINDA:
                for i in range(0, 7):
                    mid = tid[:-1] + str(i)
                    for t in targets:
                        for u in ("", "_2", "_3", "_4"):
                            for form in (("", "_f", "_f1", "_f2") if altForm else ("",)):
                                try:
                                    fn = "phit_{}{}{}{}{}".format(mid, t, style, u, form)
                                    sheets += await self.processManifest(fn)
                                except:
                                    pass
            else:
                for t in targets:
                    for u in ("", "_2", "_3", "_4"):
                        for form in (("", "_f", "_f1", "_f2") if altForm else ("",)):
                            try:
                                fn = "phit_{}{}{}{}{}".format(tid, t, style, u, form)
                                sheets += await self.processManifest(fn)
                            except:
                                pass
            sheets = list(dict.fromkeys(sheets)) # remove dupes
            data[CHARA_PHIT] += sheets
            # ougi
            sheets = []
            for uncap in uncaps:
                if uncap not in flags:
                    self.tasks.print("")
                    self.tasks.print("Warning: Missing uncap art", uncap, "for character:", id)
                    continue
                uf = flags[uncap]
                for g in ("", "_0", "_1"):
                    for form in (("", "_f", "_f1", "_f2") if altForm else ("",)):
                        for catype in ("", "_s2", "_s3"):
                            for sub in (("",) if tid == MALINDA else ("", "_a", "_b", "_c", "_d", "_e", "_f", "_g", "_h", "_i", "_j")):
                                for ex in (("", "_1", "_2", "_3", "_4", "_5", "_6") if tid == MALINDA else ("",)):
                                    try:
                                        fn = "nsp_{}_{}{}{}{}{}{}{}".format(tid, uncap, style, g, form, catype, sub, ex)
                                        sheets += await self.processManifest(fn)
                                    except:
                                        pass
            sheets = list(dict.fromkeys(sheets)) # remove dupes
            data[CHARA_SP] += sheets
            # skills
            sheets = []
            for el in range(1, 15):
                try:
                    fn = "ab_all_{}{}_{}".format(tid, style, str(el).zfill(2))
                    sheets += await self.processManifest(fn)
                except:
                    pass
            sheets = list(dict.fromkeys(sheets)) # remove dupes
            data[CHARA_AB_ALL] += sheets
            sheets = []
            for el in range(1, 15):
                try:
                    fn = "ab_{}{}_{}".format(tid, style, str(el).zfill(2))
                    sheets += await self.processManifest(fn)
                except:
                    pass
            sheets = list(dict.fromkeys(sheets)) # remove dupes
            data[CHARA_AB] += sheets
        if self.count_file(data) > file_count:
            self.modified = True
            chara_data[element_id] = data
            self.tasks.add(self.update_scenes_of, parameters=(element_id, index))
            self.tasks.add(self.update_sound_of, parameters=(element_id, index))
            self.add(element_id, ADD_CHAR)
            self.flags.add("found_character")
            # updating corresponding fate episode
            if index == 'characters':
                for k, v in self.data['fate'].items():
                    if v[FATE_LINK] == element_id:
                        self.tasks.add(self.update_all_fate, parameters=(k,), priority=0)
                        break
            self.tasks.print("Updated:", element_id, "for index:", index, "(Queuing secondary updates...)")
            self.remove_from_uncap_queue(element_id)

    # Update partner data. Note: It's based on charaUpdate and is terribly inefficient
    async def update_partner(self : Updater, ts : TaskStatus, element_id : str) -> None:
        partners = self.data['partners'] # reference
        is_mc : bool = element_id.startswith("389")
        lookup : set[str] = set()
        i : int
        try:
            data = partners[element_id]
            # build set of existing ids to avoid looking for them again
            for i in data[CHARA_SPRITE]:
                if i.startswith("npc_"):
                    lookup.add(i.split('_')[1])
            for i in data[CHARA_PHIT]:
                if i.startswith("phit_"):
                    lookup.add(i.split('_')[1])
            for i in data[CHARA_SP]:
                if i.startswith("nsp_"):
                    lookup.add(i.split('_')[1])
            for i in data[CHARA_AB_ALL]:
                if i.startswith("ab_all_"):
                    lookup.add(i.split('_')[2])
            for i in data[CHARA_AB]:
                if i.startswith("ab_"):
                    lookup.add(i.split('_')[1])
            for i in data[CHARA_GENERAL]:
                lookup.add(i.split('_')[0])
        except:
            data = [[], [], [], [], [], []] # sprite, phit, sp, aoe, single, general
            lookup = set()
        style = "" # placeholder, unused
        # set error
        if ts.max_err == -1:
            ts.max_err = 15 if element_id == "3890005000" else 5 # special one
        edited : bool = False
        while not ts.complete:
            tid : str = str(int(element_id) + ts.get_next_index())
            if tid in lookup:
                ts.good()
            else:
                tmp : list[list[str]] = [[], [], [], [], [], []]
                uncaps : list[str] = []
                sheets : list[str] = []
                altForm : bool = False
                # # # Assets
                # # # Main sheets
                for uncap in (("0_01", "1_01", "0_02", "1_02") if is_mc else ("01", "02", "03", "04")):
                    for gender in ("", "_0", "_1"):
                        for ftype in ("", "_s2", "_0", "_1"):
                            for form in ("", "_f", "_f1", "_f2"):
                                try:
                                    fn = "npc_{}_{}{}{}{}{}".format(tid, uncap, style, gender, form, ftype)
                                    if fn not in lookup:
                                        sheets += await self.processManifest(fn, True)
                                    if form == "":
                                        uncaps.append(uncap)
                                    else:
                                        altForm = True
                                except:
                                    if form == "":
                                        break
                tmp[CHARA_SPRITE] = sheets
                # arts
                flags : dict[str, list[bool]] = await self.artCheck(tid, style, [])
                targets = []
                for uncap in flags:
                    # main
                    base_fn = "{}_{}{}".format(tid, uncap, style)
                    uf = flags[uncap]
                    for g in (("_0", "_1") if (uf[0] is True) else ("",)):
                        for m in (("_101", "_102", "_103", "_104", "_105") if (uf[1] is True) else ("",)):
                            for n in (("_01", "_02", "_03", "_04", "_05", "_06") if (uf[2] is True) else ("",)):
                                for af in (("", "_f", "_f1", "_f2") if altForm else ("",)):
                                    targets.append(base_fn + g + af + m + n)
                tmp[CHARA_GENERAL] = targets
                if is_mc: uncaps = ["01", "02"]
                # # # Other sheets
                # attack
                targets = [""]
                for i in range(2, len(uncaps)):
                    targets.append("_" + uncaps[i])
                attacks = []
                for t in targets:
                    for u in ("", "_2", "_3", "_4"):
                        for form in (("", "_f", "_f1", "_f2") if altForm else ("",)):
                            try:
                                fn = "phit_{}{}{}{}{}".format(tid, t, style, u, form)
                                if fn not in lookup: attacks += await self.processManifest(fn, True)
                            except:
                                pass
                tmp[CHARA_PHIT] = attacks
                # ougi
                attacks = []
                for uncap in uncaps:
                    try: uf = flags[uncap.split('_')[-1]]
                    except: uf = [False]
                    found = False
                    for g in (("", "_0", "_1") if (uf[0] is True) else ("",)):
                        for form in (("", "_f", "_f1", "_f2") if altForm else ("",)):
                            for catype in ("", "_s2", "_s3"):
                                for sub in ("", "_a", "_b", "_c", "_d", "_e", "_f", "_g", "_h", "_i", "_j"):
                                    try:
                                        fn = "nsp_{}_{}{}{}{}{}{}".format(tid, uncap, style, g, form, catype, sub)
                                        if fn not in lookup: attacks += await self.processManifest(fn, True)
                                        found = True
                                    except:
                                        pass
                                if found: break
                tmp[CHARA_SP] = attacks
                # skills
                attacks = []
                for el in range(1, 15):
                    try:
                        fn = "ab_all_{}{}_{}".format(tid, style, str(el).zfill(2))
                        if fn not in lookup: attacks += await self.processManifest(fn, True)
                    except:
                        pass
                tmp[CHARA_AB_ALL] = attacks
                attacks = []
                for el in range(1, 15):
                    try:
                        fn = "ab_{}{}_{}".format(tid, style, str(el).zfill(2))
                        if fn not in lookup: attacks += await self.processManifest(fn, True)
                    except:
                        pass
                tmp[CHARA_AB] = attacks
                # verification
                l = 0
                for i, e in enumerate(tmp):
                    if len(e) > 0:
                        l += len(e)
                        data[i] += e
                if l == 0:
                    ts.bad()
                else:
                    ts.good()
                    edited = True
        if edited:
            self.modified = True
            partners[element_id] = data
            for i in range(len(data)):
                partners[element_id][i] = list(set(partners[element_id][i] + data[i]))
                partners[element_id][i].sort()
            self.add(element_id, ADD_PARTNER)
            self.flags.add("found_character")
            self.tasks.print("Updated:", element_id, "for index:", 'partners')
            self.remove_from_uncap_queue(element_id)

    # Update NPC data
    async def update_npc(self, element_id : str) -> None:
        npcs = self.data['npcs'] # reference
        # init
        data : list[list[str]|None] = [False, [], []] # journal flag, npc, voice
        if element_id in npcs and npcs[element_id] != 0:
            data[NPC_SCENE] = npcs[element_id][NPC_SCENE]
            data[NPC_SOUND] = npcs[element_id][NPC_SOUND]
        exist : bool = False
        try:
            await self.head(IMG + "sp/assets/npc/m/{}_01.jpg".format(element_id))
            data[NPC_JOURNAL] = True
            exist = True
        except:
            if element_id.startswith("305"):
                return # don't continue for special npcs
        if not exist:
            # base scene
            base_target, main_x, uncap_x = self.generate_scene_file_list(element_id)
            path : list[str] = [IMG, "", element_id, "", "", ".png"]
            for u in ("", "_02", "_03"):
                for f in base_target:
                    if f != "" and u != "":
                        break
                    if u+f in data[NPC_SCENE]:
                        exist = True
                    else:
                        path[3] = u
                        path[4] = f
                        found : bool = False
                        for fpath in ("sp/quest/scene/character/body/", "sp/raid/navi_face/"):
                            path[1] = fpath
                            try:
                                await self.head("".join(path))
                                data[NPC_SCENE].append(u+f)
                                exist = True
                                found = True
                                break
                            except:
                                pass
                        if found:
                            break
            # base sound
            if not exist:
                base_target = ["_v_001", "_boss_v_1", "_boss_v_2", "_boss_v_10", "_boss_v_20"]
                for k in base_target:
                    try:
                        if k not in data[NPC_SOUND]:
                            f = "{}{}".format(element_id, k)
                            await self.head(SOUND + "voice/" + f + ".mp3")
                            data[NPC_SOUND].append(k)
                            exist = True
                        else:
                            exist = True
                        break
                    except:
                        pass
        if exist:
            self.modified = True
            npcs[element_id] = data
            self.tasks.add(self.update_scenes_of, parameters=(element_id, 'npcs'))
            self.tasks.add(self.update_sound_of, parameters=(element_id, 'npcs'))
            self.add(element_id, ADD_NPC)
            self.flags.add("found_character")
            self.tasks.print("Updated:", element_id, "for index:", 'npcs', "(Queuing secondary updates...)")
            self.remove_from_uncap_queue(element_id)

    # Update Weapon data
    async def update_weapon(self, element_id : str) -> None:
        weapons = self.data['weapons'] # reference
        # get existing file_count
        try:
            if self.ignore_file_count: raise Exception()
            file_count = self.count_file(weapons[element_id])
        except:
            file_count = 0
        # init
        data : list[list[str]] = [[], [], []] # general, phit, sp
        s : str
        for s in ("", "_02", "_03"):
            # art
            try:
                await self.head(IMG + "sp/assets/weapon/m/{}{}.jpg".format(element_id, s))
                data[WEAP_GENERAL].append("{}{}".format(element_id, s))
            except:
                if s == "":
                    return
                else:
                    break
            # attack
            u : str
            g : str
            for u in ("", "_2", "_3", "_4"):
                for g in ("", "_0", "_1"):
                    try:
                        fn = "phit_{}{}{}{}".format(element_id, s, g, u)
                        data[WEAP_PHIT] += await self.processManifest(fn)
                    except:
                        if g == '_0':
                            break
            # ougi
            t : str
            for u in ("", "_0", "_1", "_2", "_3"):
                for t in ("", "_s2", "_s3"):
                    for g in ("", "_0", "_1"):
                        try:
                            fn = "sp_{}{}{}{}{}".format(element_id, s, g, u, t)
                            data[WEAP_SP] += await self.processManifest(fn)
                        except:
                            if g == '_0':
                                break
        # clean dupes
        if self.count_file(data) > file_count:
            data[WEAP_PHIT] = list(dict.fromkeys(data[WEAP_PHIT]))
            data[WEAP_SP] = list(dict.fromkeys(data[WEAP_SP]))
            self.modified = True
            weapons[element_id] = data
            self.add(element_id, ADD_WEAP)
            self.tasks.print("Updated:", element_id, "for index:", 'weapons')
            self.remove_from_uncap_queue(element_id)

    # Update Weapon data
    async def update_shield(self, element_id : str) -> None:
        shields = self.data['shields'] # reference
        if element_id not in shields:
            # art check
            try:
                await self.head(IMG + "sp/assets/shield/m/{}.jpg".format(element_id))
            except:
                return
        elif isinstance(shields[element_id], list):
            return
        
        self.modified = True
        shields[element_id] = [[element_id]]
        self.add(element_id, ADD_SHIELD)
        self.tasks.print("Updated:", element_id, "for index:", 'shields')

    # Update Job data
    async def update_job(self, element_id : str) -> None:
        jobs = self.data['job'] # reference
        # get existing file_count
        try:
            if self.ignore_file_count: raise Exception()
            file_count = self.count_file(jobs[element_id])
        except:
            file_count = 0
        # init
        cmh = []
        colors = [int(element_id[-1])]
        alts = []
        # mh check
        for mh in MAINHAND:
            try:
                await self.head(IMG + "sp/assets/leader/raid_normal/{}_{}_0_01.jpg".format(element_id, mh))
                cmh.append(mh)
            except:
                continue
        if len(cmh) > 0:
            # alt check
            if colors[0] == 1:
                for j in (2, 3, 4, 5, 80):
                    try:
                        await self.head(IMG + "sp/assets/leader/sd/{}_{}_0_01.png".format(element_id[:-2]+str(j).zfill(2), cmh[0]))
                        if element_id in UNIQUE_SKIN:
                            await self.update_job(element_id[:-2]+str(j).zfill(2))
                        else:
                            colors.append(j)
                            if j >= 80:
                                alts.append(j)
                    except:
                        continue
            # set data
            # main id, alt id, detailed id (main), detailed id (alt), detailed id (all), sd, mainhand, sprites, phit, sp, unlock, mypage
            data = [[element_id], [element_id+"_01"], [], [], [], [], cmh, [], [], [], [], [], [], []]
            
            data[JOB_ALT] = [element_id+"_01"] + [element_id[:-2]+str(j).zfill(2)+"_01" for j in alts]
            data[JOB_DETAIL] = [element_id+"_"+cmh[0]+"_"+str(k)+"_01" for k in range(2)]
            for j in [int(element_id[-1])]+alts:
                for k in range(2):
                    data[JOB_DETAIL_ALT].append(element_id[:-2]+str(j).zfill(2)+"_"+cmh[0]+"_"+str(k)+"_01")
            for j in colors:
                for k in range(2):
                    data[JOB_DETAIL_ALL].append(element_id[:-2]+str(j).zfill(2)+"_"+cmh[0]+"_"+str(k)+"_01")
            for j in colors:
                data[JOB_SD].append(element_id[:-2]+str(j).zfill(2))
            for h in data[JOB_ALT]:
                for j in range(2):
                    try:
                        data[JOB_UNLOCK] += await self.processManifest("eventpointskin_release_{}_{}".format(h.split('_', 1)[0], j))
                    except:
                        pass
            # clean dupe
            data[JOB_UNLOCK] = list(dict.fromkeys(data[JOB_UNLOCK]))
            if self.count_file(data) > file_count:
                jobs[element_id] = data
                self.modified = True
                self.add(element_id, ADD_JOB)
                self.tasks.print("Updated:", element_id, "for index:", 'job')
                self.remove_from_uncap_queue(element_id)

    ### Job #################################################################################################################
    
    # To be called once when needed
    async def init_job_list(self : Updater) -> None:
        if self.job_list is not None:
            return
        # get existing classes
        try:
            job_list : dict[str, str] = json.loads((await self.get(JS + "constant/job.js")).decode('utf-8').split("=", 1)[1].split(";return", 1)[0].replace('{', '{"').replace(',', '","').replace(':', '":"').replace('}', '"}')) # contain a list of all classes. it misses the id of the outfits however.
        except Exception as ee:
            self.tasks.print("Couldn't initialize the job list:", ee)
            return
        # invert pairs (+ format characters)
        job_list = {v : "".join(set(k.lower())) for k, v in job_list.items()}
        # old skins
        for e in (("125001","snt"), ("165001","stf"), ("185001", "idl")):
            job_list[e[0]] = e[1]
        # new skins
        async with asyncio.TaskGroup() as tg:
            tasks = []
            for i in range(31, 41):
                for j in range(0, 20):
                    if str(i * 100 + j)+"01" in job_list: continue
                    tasks.append(tg.create_task(self.init_job_list_check(str(i * 100 + j)+"01")))
        for t in tasks:
            r = t.result()
            if r is not None:
                job_list[r] = STRING_CHAR
        self.job_list = job_list

    # Subroutine for init_job_list
    async def init_job_list_check(self, id : str) -> str|None:
        try:
            await self.head(IMG + "sp/assets/leader/m/{}_01.jpg".format(id))
            return id
        except:
            return None

    # Used by --job, more specific but also slower job detection system
    async def search_job_detail(self, full_key_search : bool) -> None: # even slower with full_key_search but sure to find something
        if self.job_list is None:
            self.tasks.print("Couldn't retrieve job list from the game")
            return
        # key search
        for k, v in self.data['job'].items():
            if v == 0:
                continue
            if len(v[JOB_SPRITE]) == 0:
                if k in self.job_list and self.job_list[k] != STRING_CHAR:
                    self.tasks.add(self.detail_job_search, parameters=(self.job_list[k], k))
                else:
                    full_key_search = True
        # class weapon search
        weapons = self.data['weapons'] # reference
        job_wpn = self.data["job_wpn"] # reference
        for i in range(0, 999):
            err = 0
            for j in range(10):
                wid = "1040{}{}00".format(j, i) # class weapons always use SSR, afaik
                if wid in weapons or wid in job_wpn:
                    err = 0
                    continue
                self.tasks.add(self.detail_job_weapon_search, parameters=(wid, ))
                err += 1
                if err > 15: break
        # full key search
        if full_key_search:
            job_keys = self.data["job_key"] # reference
            for a in STRING_CHAR:
                for b in STRING_CHAR:
                    for c in STRING_CHAR:
                        d = a+b+c
                        if d in job_keys:
                            continue
                        self.tasks.add(self.detail_job_search_single, parameters=(d, MAINHAND))
        await self.tasks.start()

    async def search_job_second_id(self : Updater, mhs : list[str]) -> None:
        if len(mhs) == 0:
            mhs = MAINHAND
        job_keys = self.data["job_key"] # reference
        for a in STRING_CHAR:
            for b in STRING_CHAR:
                for c in STRING_CHAR:
                    d = a+b+c
                    if d in job_keys:
                        continue
                    self.tasks.add(self.detail_job_search_single, parameters=(d, mhs))
        await self.tasks.start()

    # test a job mh
    async def detail_job_search(self : Updater, key : str, job : str) -> None:
        job_keys = self.data["job_key"] # reference
        cmh = self.data['job'][job][JOB_MH]
        a = key[0]
        for b in key:
            for c in key:
                d = a+b+c
                if d in job_keys and job_keys[d] is not None: continue
                passed = True
                for mh in cmh:
                    try:
                        await self.head(MANIFEST + "{}_{}_0_01.js".format(d, mh))
                    except:
                        passed = False
                        break
                if passed:
                    job_keys[d] = job
                    self.modified = True
                    self.tasks.print("Set", job, "to", d)

    # search for job weapon
    async def detail_job_weapon_search(self: Updater, wid : str) -> None:
        try:
            await self.head(IMG + '_low/sp/assets/weapon/m/' + wid + ".jpg")
            return
        except:
            pass
        for k in (("phit_", ""), ("phit_", "_2"), ("phit_", "_3"), ("sp_", "_s2"), ("sp_", "")):
            for g in ("", "_0"):
                try:
                    await self.head(MANIFEST + k[0] + wid + g + k[1] + ".js")
                    self.data["job_wpn"][wid] = None
                    self.modified = True
                    self.tasks.print("Possible job skin related weapon:", wid)
                    return
                except:
                    pass

    # test a job key
    async def detail_job_search_single(self, key : str, mhs : list[str]) -> None:
        for mh in mhs:
            try:
                await self.head(MANIFEST + "{}_{}_0_01.js".format(key, mh))
                self.data["job_key"][key] = None
                self.modified = True
                self.tasks.print("\nUnknown job key", key, "for mh", mh)
                break
            except:
                pass

    # import job_data_export data
    async def importjob(self : Updater) -> None:
        try:
            with open("json/job_data_export.json", mode="r", encoding="ascii") as f:
                tmp = json.load(f)
                if 'lookup' not in tmp or 'weapon' not in tmp:
                    raise Exception()
        except OSError as e:
            self.tasks.print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            self.tasks.print("Couldn't open json/job_data_export.json")
            return
        except Exception as e:
            self.tasks.print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            self.tasks.print("Couldn't load json/job_data_export.json")
            return
        self.tasks.print("Import the data from json/job_data_export.json? (y/Y)")
        if input().lower() == 'y':
            self.tasks.print("Importing data...")
            for jid, s in tmp["lookup"].items():
                # add job if needed
                if jid not in self.data['job']:
                    self.tasks.add(self.update_job, parameters=(jid,))
                if s is not None:
                    self.tasks.add(self.job_import_task, parameters=(jid, s, 0))
            for jid, s in tmp["weapon"].items():
                if s is not None:
                    self.tasks.add(self.job_import_task, parameters=(jid, s, 1))
            if await self.tasks.start():
                self.tasks.print("Job Data Import finished with success")
            else:
                self.tasks.print("An error occured, exiting to not compromise the data")
                os._exit(0)

    # task to verify job_data_export data and import it
    async def job_import_task(self : Updater, jid : str, s : Any, mode : int) -> None:
        match mode:
            case 0:
                # set key
                sheets = []
                for v in self.data['job'][jid][JOB_DETAIL_ALL]:
                    try:
                        if jid in UNIQUE_SKIN:
                            sheets += await self.processManifest(s + "_" + '_'.join(v.split('_')[1:3]) + "_01")
                        else:
                            sheets += await self.processManifest(s + "_" + '_'.join(v.split('_')[1:3]) + "_" + v.split('_')[0][-2:])
                    except:
                        pass
                self.data['job'][jid][JOB_SPRITE] = list(dict.fromkeys(sheets))
                self.data['job_key'][s] = jid
                self.modified = True
                self.tasks.print(len(sheets),"sprites set to job", jid)
            case 1:
                # phit
                sheets = []
                for u in ("", "_1", "_2", "_3"):
                    for g in ("", "_0", "_1"):
                        try:
                            sheets += await self.processManifest("phit_{}{}{}".format(s, u, g))
                        except:
                            if g == "_0":
                                break
                if jid == "360101": # special exception for racing suit
                    try:
                        sheets += await self.processManifest("phit_racer")
                    except:
                        pass
                sheets = list(dict.fromkeys(sheets))
                self.data['job'][jid][JOB_PHIT] = sheets
                # ougi
                sheets = []
                for u in ("", "_0", "_1", "_0_s2", "_1_s2", "_0_s3", "_1_s3"):
                    try:
                        sheets += await self.processManifest("sp_{}{}".format(s, u))
                    except:
                        pass
                sheets = list(dict.fromkeys(sheets))
                self.data['job'][jid][JOB_SP] = sheets
                # ab_all
                sheets = []
                for u in range(1, 10):
                    try:
                        sheets += await self.processManifest("ab_all_{}_{}".format(s, str(u).zfill(2)))
                    except:
                        pass
                sheets = list(dict.fromkeys(sheets))
                self.data['job'][jid][JOB_AB_ALL] = sheets
                # ab
                sheets = []
                for u in range(1, 10):
                    try:
                        sheets += await self.processManifest("ab_{}_{}".format(s, str(u).zfill(2)))
                    except:
                        pass
                sheets = list(dict.fromkeys(sheets))
                self.data['job'][jid][JOB_AB] = sheets
                # mypage
                sheets = []
                for g in range(0, 2):
                    for mh in MAINHAND:
                        try:
                            sheets += await self.processManifest("mypage_{}_{}_{}_01".format(jid, mh,g))
                        except:
                            pass
                sheets = list(dict.fromkeys(sheets))
                self.data['job'][jid][JOB_MYPAGE] = sheets

                self.tasks.print(len(self.data['job'][jid][JOB_PHIT])+len(self.data['job'][jid][JOB_SP])+len(self.data['job'][jid][JOB_AB_ALL])+len(self.data['job'][jid][JOB_AB]),"weapon sprites set to job", jid)
                self.data['job_wpn'][s] = jid
                self.modified = True

    # export job_data_export data
    async def exportjob(self : Updater) -> None:
        self.tasks.print("Export the data to json/job_data_export.json? (y/Y)")
        if input().lower() == 'y':
            tmp = {"lookup":{}, "weapon":{}, "unset_key":[], "unset_wpn":[]}
            for k in self.data['job']:
                tmp['lookup'][k] = None
            for k in self.data['job_key']:
                if self.data['job_key'][k] is None:
                    tmp['unset_key'].append(k)
                else:
                    tmp['lookup'][self.data['job_key'][k]] = k
            for k in self.data['job_wpn']:
                if self.data['job_wpn'][k] is None:
                    tmp['unset_wpn'].append(k)
                else:
                    tmp['weapon'][self.data['job_wpn'][k]] = k
            with open("json/job_data_export.json", mode="w", encoding="ascii") as f:
                json.dump(tmp, f, ensure_ascii=True, indent=4)
                self.tasks.print("Job Data exported to json/job_data_export.json")

    ### Scene #################################################################################################################
    
    # update npc/character/skin scene files for given IDs
    async def update_all_scene_for_ids(self : Updater, ids : list[str] = []) -> None:
        # references
        characters = self.data["characters"]
        skins = self.data["skins"]
        npcs = self.data["npcs"]
        
        for element_id in ids:
            if element_id in characters:
                self.tasks.add(self.update_scenes_of, parameters=(element_id, "characters"))
            elif element_id in skins:
                self.tasks.add(self.update_scenes_of, parameters=(element_id, "skins"))
            elif element_id in npcs:
                self.tasks.add(self.update_scenes_of, parameters=(element_id, "npcs"))
        self.tasks.print("Updating scenes for {} elements...".format(self.tasks.total))
        await self.tasks.start()

    # update ALL npc/character/skin scene files, time consuming, can be resumed, can be filtered
    async def update_all_scene(self : Updater, filters : list[str] = []) -> None:
        self.flags.add("use_resume")
        self.flags.add("scene_update")
        self.load_resume("scene")
        if len(self.resume.get('done', {})) != 0:
            self.tasks.print("Note: Resuming the previous run...")
        if len(filters) > 0:
            self.tasks.print("Note: {} filter(s) in use. Not matching filenames will be ignored.".format(len(filters)))
        if 'name' not in self.resume:
            self.resume['name'] = "scene"
        if 'done' not in self.resume:
            self.resume['done'] = {}
        for index in ("characters", "skins", 'npcs'):
            for element_id in self.data[index]:
                self.tasks.add(self.update_scenes_of, parameters=(element_id, index, filters))
        self.tasks.print("Updating scenes for {} elements...".format(self.tasks.total))
        await self.tasks.start()
        self.clear_resume()
    
    # set self.scene_strings if needed and return them along with base strings
    def generate_scene_file_list(self, element_id : str = "") -> tuple[list[str], list[str], list[str]]:
        # set scene strings
        # it's mostly a concatenation work
        if self.scene_strings is None:
            self.scene_strings = [{}, {}] # dict to keep order
            for main in SCENE_SUFFIXES["default"]["main"]:
                for end in SCENE_SUFFIXES["default"]["end"]:
                    if main != "" and main == end: continue
                    f = main + end
                    self.scene_strings[0][f] = None
            self.scene_strings[1] = self.scene_strings[0].copy()
            self.scene_strings[1] = list(self.scene_strings[1].keys())
            for unique in SCENE_SUFFIXES["default"]["unique"]:
                for end in SCENE_SUFFIXES["default"]["end"]:
                    if unique != "" and unique == end: continue
                    f = unique + end
                    self.scene_strings[0][f] = None
            self.scene_strings[0] = list(self.scene_strings[0].keys())
        
        if element_id in SCENE_SUFFIXES: # this part is similar to the above but for special elements with dedicated strings
            if "base" in SCENE_SUFFIXES[element_id]:
                base = SCENE_SUFFIXES["default"]["base"] + SCENE_SUFFIXES[element_id]["base"]
            else:
                base = SCENE_SUFFIXES["default"]["base"]
            if "main" in SCENE_SUFFIXES[element_id] or "end" in SCENE_SUFFIXES[element_id] or "unique" in SCENE_SUFFIXES[element_id]:
                d = {}
                for k in ("main", "unique", "end"):
                    if k not in SCENE_SUFFIXES[element_id]:
                        d[k] = SCENE_SUFFIXES["default"][k]
                    else:
                        s = set()
                        d[k] = []
                        for f in (SCENE_SUFFIXES["default"][k] + SCENE_SUFFIXES[element_id].get(k, [])):
                            if f not in s:
                                s.add(f)
                                d[k].append(f)
                A = {}
                for main in d["main"]:
                    for end in d["end"]:
                        if main != "" and main == end: continue
                        f = main + end
                        A[f] = None
                B = {}
                for unique in d["unique"]:
                    for end in d["end"]:
                        if unique != "" and unique == end: continue
                        f = unique + end
                        A[f] = None
                A = list(A.keys())
                B = list(B.keys())
            else:
                A = self.scene_strings[0]
                B = self.scene_strings[1]
            return base, A, B
        else:
            return SCENE_SUFFIXES["default"]["base"], self.scene_strings[0], self.scene_strings[1]

    # Execution flow
    #
    #   update_scenes_of
    #       v
    #   update_scene (for each uncap)
    #       v
    #   update_scene_continue & (multiples) update_scene_check  (for each uncap)
    #       v
    #   update_scene_end & (multiples) update_scene_check  (for each uncap)
    #
    
    # update the scene files of one element
    async def update_scenes_of(self : Updater, element_id : str, index : str, filters : list[str] = []) -> None:
        u : str
        uncaps : list[str]
        idx : int
        # retrieve infos (index, index in the data, uncaps) and create existing set of file
        try:
            data : list[Any] = self.data[index][element_id]
            match index:
                case 'characters'|'skins':
                    idx = CHARA_SCENE
                    uncaps= []
                    for u in data[CHARA_GENERAL]:
                        uu = u.replace(element_id+"_", "")
                        if "_" not in uu and uu.startswith("0"):
                            uncaps.append(uu)
                case 'npcs':
                    idx = NPC_SCENE
                    uncaps = ["", "02", "03"]
                case _:
                    return
            existing : set[str] = set(data[idx])
        except:
            return
        # retrieve strings
        base_target, main_x, uncap_x = self.generate_scene_file_list(element_id) # we save memory this way as most elements share the same strings, instead of building them on the spot
        # for each uncap...
        for u in uncaps:
            if u in ("", "01"):
                u = ""
            else:
                u = "_" + u
            if 'scene_update' in self.flags and u in self.resume.get('done', {}).get(element_id, []): # skip if in resume file
                continue
            # start update_scene
            self.tasks.add(self.update_scene, parameters=(index, element_id, idx, u, existing, base_target, main_x if u == "" else uncap_x, filters), priority=2)

    # update character/NPC scene data
    async def update_scene(self : Updater, index : str, element_id : str, idx : int, uncap : str, existing : set[str], bases : list[str], suffixes : list[str], filters : list[str]) -> None:
        ts : TaskStatus
        file_id : str = self.data['npc_replace'].get(element_id, element_id)
        # check if uncap string exists
        if uncap not in existing:
            await self.update_scene_check(TaskStatus(1, 1, running=1), file_id, uncap, existing)
        # quit if npc and no uncap string existing beyond base one
        if index == 'npcs' and uncap != "" and uncap not in existing:
            return
        # check other base strings
        base : str
        f : str # file
        files : list[str] = []
        # list all files to test
        for base in bases:
            f = uncap + base
            if f in existing or base == "" or not self.file_is_matching(f, filters): # exists OR empty (later is already tested by run() and update())
                continue
            files.append(f)
        if len(files) > 0: # for each file
            ts = TaskStatus(1, 1, running=len(files))
            for i in range(len(files)): # make ONE check task
                self.tasks.add(self.update_scene_check, parameters=(ts, file_id, files[i], existing), priority=1)
            # and queue next step
            self.tasks.add(self.update_scene_continue, parameters=(ts, index, element_id, idx, uncap, existing, bases, suffixes, filters), priority=1)
        else:
            # no file, directly go to next step
            await self.update_scene_continue(TaskStatus(0, 1), index, element_id, idx, uncap, existing, bases, suffixes, filters)

    # part 2 of the function, wait for TaskStatus completion
    async def update_scene_continue(self : Updater, ts : TaskStatus, index : str, element_id : str, idx : int, uncap : str, existing : set[str], bases : list[str], suffixes : list[str], filters : list[str]) -> None:
        # wait previous tasks completion
        while not ts.finished:
            await asyncio.sleep(1)
        file_id : str = self.data['npc_replace'].get(element_id, element_id)
        files : list[str] = []
        suffix : str
        # search variations now, make a list of file again
        for base in bases:
            f : str = uncap + base
            if base != "" and f not in existing:
                continue
            for suffix in suffixes:
                g : str = f + suffix
                if suffix == "" or g in existing or not self.file_is_matching(g, filters):
                    continue
                files.append(g)
        if len(files) > 0: # for each file
            ts = TaskStatus(1, 1, running=len(files))
            for i in range(len(files)): # make ONE check task
                self.tasks.add(self.update_scene_check, parameters=(ts, file_id, files[i], existing), priority=1)
            # and queue final step
            self.tasks.add(self.update_scene_end, parameters=(ts, index, element_id, idx, uncap, existing, bases, suffixes), priority=1)
        else: # else go to end
            await self.update_scene_end(TaskStatus(0, 1), index, element_id, idx, uncap, existing, bases, suffixes)

    # part 3 of the function, wait for TaskStatus completion
    async def update_scene_end(self : Updater, ts : TaskStatus, index : str, element_id : str, idx : int, uncap : str, existing : set[str], bases : list[str], suffixes : list[str]) -> None:
        # wait previous tasks completion
        while not ts.finished:
            await asyncio.sleep(1)
        # check if the data has new strings
        if len(existing) > len(self.data[index][element_id][idx]):
            self.data[index][element_id][idx] = list(existing) # set it
            self.data[index][element_id][idx].sort(key=lambda e: (int(e.split("_")[1]) if ("_" in e and e.split("_")[1].isnumeric()) else 0, e, len(e))) # and sort it
            self.modified = True
            match index:
                case 'npcs':
                    self.add(element_id, ADD_NPC)
                case 'characters'|'skins':
                    self.add(element_id, ADD_CHAR)
            # valentine check
            if "_white" in existing or "_valentine" in existing and element_id not in self.data['valentines']:
                self.data['valentines'][element_id] = 0
        # add element id and uncap to resume save
        if "scene_update" in self.flags:
            if element_id not in self.resume['done']:
                self.resume['done'][element_id] = []
            self.resume['done'][element_id].append(uncap)

    # request scene assets
    async def update_scene_check(self : Updater, ts : TaskStatus, file_id : str, f : str, existing : set[str]) -> None:
        try:
            await self.head(IMG + "sp/quest/scene/character/body/{}{}.png".format(file_id, f)) # check if scene file exists
            existing.add(f)
        except:
            if (f == "" or f.split("_")[-1] not in SCENE_BUBBLE_FILTER):
                try:
                    await self.head(IMG + "sp/raid/navi_face/{}{}.png".format(file_id, f)) # or check navi_face is the file name matches the SCENE_BUBBLE_FILTER
                    existing.add(f)
                except:
                    pass
        ts.finish() # task ended

    ### Generic Chapter Update #################################################################################################################

    # generic function to update: A story chapter, a fate episode scene or an event chapter
    # horrible but can't find a better way
    async def update_chapter(self : Updater, ts : TaskStatus, index : str, element_id : str, idx : int, base_url : str, existing : set[str]) -> tuple:
        is_tuto = "tuto_scene" in base_url # check for MSQ tutorial
        Z = 1 if is_tuto else 2 # zfill value used in the filename, for MSQ tutorial
        suffix : str
        stem_suffix : str
        while not ts.complete:
            i : int = ts.get_next_index() # next ID to check
            url : str = base_url + "_" + str(i).zfill(Z) # prepare url
            stem : str = url.split("/")[-1]
            good : bool = False # flag to determine if we have at least a positive match
            flag : bool = False # flag used along the way
            # Check base ones
            for k in ("", "_up", "_ef", "_shadow"): # there are likely more variations but I don't want to add pointless files to slow it down further
                try:
                    stem_suffix = stem + k
                    if stem_suffix not in existing:
                        await self.head(url + k + ".png")
                        existing.add(stem_suffix)
                    flag = True
                    good = True
                except:
                    pass
            # check for extras
            for ss in (("a", "b", "c", "d", "e", "f"), ("1", "2", "3", "4", "5", "6")):
                for k in ss:
                    try:
                        stem_suffix : str = stem + k
                        if stem_suffix not in existing:
                            await self.head(url + k + ".png")
                            existing.add(stem_suffix)
                        flag = True
                        good = True
                    except:
                        pass
            # Check the variations (yes, it's slow)
            for k in string.ascii_lowercase:
                found = False
                try:
                    suffix = "_" + k
                    stem_suffix = stem + suffix
                    if stem_suffix not in existing:
                        await self.head(url + suffix + ".png")
                        existing.add(stem_suffix)
                    flag = True
                    found = True
                    good = True
                except:
                    pass
                # and sub variations (yes, it's VERY slow)
                for ss in (("a", "b", "c", "d", "e", "f"), ("1", "2", "3", "4", "5")):
                    for kkk in ss:
                        try:
                            suffix = "_" + k + kkk
                            stem_suffix = stem + suffix
                            if stem_suffix not in existing:
                                await self.head(url + suffix + ".png")
                                existing.add(stem_suffix)
                            flag = True
                            found = True
                            good = True
                        except:
                            break
                if not found: # stop if no files found for this particular variation
                    break
            # if NOTHING found until now OR we're in the MSQ tutorial
            if not flag or is_tuto:
                # we test another filename format
                try:
                    stem_suffix = stem + "_00"
                    if stem_suffix not in existing:
                        await self.head(url + "_00.png")
                        existing.add(stem_suffix)
                    good = True
                except:
                    pass
                # some variations
                for k in ("_up", "_shadow"):
                    try:
                        suffix = "_00"+k
                        stem_suffix = stem + suffix
                        if stem_suffix not in existing:
                            await self.head(url + suffix + ".png")
                            existing.add(stem_suffix)
                        good = True
                    except:
                        pass
                err = 0
                i = 1
                # now test ALL numbered variations
                while i < 100 and err < 10: # they are in sequence usually, I check until 100 or if we go 10 in a row without a single match
                    k = str(i).zfill(Z)
                    try:
                        suffix = "_"+k
                        stem_suffix = stem + suffix
                        if stem_suffix not in existing:
                            await self.head(url + suffix + ".png")
                            existing.add(stem_suffix)
                        good = True
                        err = 0
                        # these variations are only possible if the above file exists (in theory)
                        for kk in string.ascii_lowercase:
                            found = False
                            try:
                                suffix = "_"+k+"_"+kk
                                stem_suffix = stem + suffix
                                if stem_suffix not in existing:
                                    await self.head(url + suffix + ".png")
                                    existing.add(stem_suffix)
                                found = True
                            except:
                                pass
                            for ss in (("a", "b", "c", "d", "e", "f"), ("1", "2", "3", "4", "5")):
                                for kkk in ss:
                                    try:
                                        suffix = "_" + k + "_" + kk + kkk
                                        stem_suffix = stem + suffix
                                        if stem_suffix not in existing:
                                            await self.head(url + suffix + ".png")
                                            existing.add(stem_suffix)
                                        found = True
                                    except:
                                        break
                            if not found:
                                break
                    except:
                        err += 1
                    i += 1
                i = 1
                # now test ALL numbered variations
                while i < 100 and err < 10: # they are in sequence usually, I check until 100 or if we go 10 in a row without a single match
                    k = str(i).zfill(Z)
                    try:
                        suffix = "_"+k
                        stem_suffix = stem + suffix
                        if stem_suffix not in existing:
                            await self.head(url + suffix + ".png")
                            existing.add(stem_suffix)
                        good = True
                        err = 0
                        # these variations are only possible if the above file exists (in theory)
                        for kk in string.ascii_lowercase:
                            found = False
                            try:
                                suffix = "_"+k+"_"+kk
                                stem_suffix = stem + suffix
                                if stem_suffix not in existing:
                                    await self.head(url + suffix + ".png")
                                    existing.add(stem_suffix)
                                found = True
                            except:
                                pass
                            for ss in (("a", "b", "c", "d", "e", "f"), ("1", "2", "3", "4", "5")):
                                for kkk in ss:
                                    try:
                                        suffix = "_"+k+"_"+kk+kkk
                                        stem_suffix = stem + suffix
                                        if stem_suffix not in existing:
                                            await self.head(url + suffix + ".png")
                                            existing.add(stem_suffix)
                                        found = True
                                    except:
                                        break
                            if not found:
                                break
                    except:
                        err += 1
                    i += 1
            # check if we found at least ONE file
            if good:
                ts.good()
            else:
                ts.bad()
                if ts.err >= ts.max_err and ts.index < 50: # special edge case, for 250329 so far
                    ts.index = 50
                    ts.err = 0
        ts.finish()
        # all tasks for this chapter finished
        # the last one is in charge of cleaning it up
        if ts.finished and len(existing) > 0:
            data = self.data[index] # reference
            # if data has changed (or we have matches and no data in index)
            if (len(existing) > 0 and element_id not in data) or (element_id in data and len(existing) > len(data[element_id][idx])):
                # create data if not initialized
                if element_id not in data:
                    match index:
                        case 'events':
                            data[element_id] = self.create_event_container()
                        case 'story':
                            data[element_id] = [[]]
                        case 'fate':
                            data[element_id] = [[],[],[],[],None]
                # set data
                data[element_id][idx] = list(existing)
                # and sort
                data[element_id][idx].sort()
                # add to changelog (and set flag) if not done yet (using self.addition to check)
                if element_id not in self.addition:
                    match index:
                        case 'events':
                            if data[element_id][EVENT_CHAPTER_COUNT] == -1:
                                data[element_id][EVENT_CHAPTER_COUNT] = 0
                            if not self.add(element_id, ADD_EVENT):
                                self.tasks.print("Updated:", element_id, "for index:", index)
                            self.flags.add("found_event")
                        case 'story':
                            if not self.add(element_id, ADD_STORY):
                                self.tasks.print("Updated:", element_id, "for index:", index)
                        case 'fate':
                            if not self.add(element_id, ADD_FATE):
                                self.tasks.print("Updated:", element_id, "for index:", index)
                            self.flags.add("found_fate")
                # raise modified flag
                self.modified = True

    ### Event #################################################################################################################
    
    # Use the wiki to build a list of existing events with their start date. Note: It needs to be updated for something more efficient
    async def get_event_list(self : Updater) -> list[str]:
        try:
            l = MISSING_EVENTS # missing events
            # add our special events
            for k in SPECIAL_EVENTS:
                l.append(k)
            # try to access the wiki
            if not self.use_wiki:
                raise Exception()
            data = await self.get_wiki("https://gbf.wiki/index.php?title=Special:CargoExport&tables=event_history&fields=time_start,name&format=json&limit=20000", get_json=True)
            # retrieve the start date from each event
            for e in data:
                t = e['time start'].split(' ', 1)[0].split('-')
                t = t[0][2:] + t[1].zfill(2) + t[2].zfill(2) # and create a date from it
                l.append(t)
        except:
            pass
        # remove dupes and sort
        l = list(set(l))
        l.sort()
        return l
    
    # convert event id string to day count integer ((year x 12 + month) x 31 + day), used for comparison purposes
    def ev2daycount(self : Updater, ev : str) -> int:
        return (int(ev[:2]) * 12 + int(ev[2:4])) * 31 + int(ev[4:6])
    
    # create the array containing the event data
    # the one for events is quite big, so I'm using a function to not miss a list somewhere
    def create_event_container(self : Updater) -> list:
        l = [-1, None]
        while len(l) < EVENT_CHAPTER_START:
            l.append([])
        for i in range(EVENT_MAX_CHAPTER):
            l.append([])
        l.append([])
        return l
    
    # exactly what the name implies. A specific list of events can also be provided to only update those
    async def update_all_event(self : Updater, events : list[str], forceflag : bool = False) -> None:
        if len(events) == 0:
            if forceflag: # shouldn't be used without specific events
                return
            evt_data = self.data['events'] # reference
            events = [ev for ev in evt_data if (evt_data[ev][EVENT_CHAPTER_COUNT] >= 0 or evt_data[ev][EVENT_THUMB] is not None)]
        self.tasks.print("Updating", len(events), "event(s)...")
        for ev in events:
            self.tasks.add(self.update_event, parameters=(ev, forceflag))
        await self.tasks.start()

    # also a pretty implicit name
    async def check_new_event(self : Updater) -> None:
        self.flags.add("checking_event")
        evt_data = self.data['events'] # reference
        # get today date
        nowd : datetime = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=32400)
        now : int = int(str(nowd.year)[2:] + str(nowd.month).zfill(2) + str(nowd.day).zfill(2))
        now_day = self.ev2daycount(str(now))
        # and the event list
        known_events : list[str] = await self.get_event_list()
        # go over that list
        for ev in known_events:
            if not ev.isdigit(): # our special ids (such as babyl0)
                if ev not in evt_data: # not set, update this event
                    self.tasks.print("Checking special event:", ev)
                    evt_data[ev] = self.create_event_container()
                    evt_data[ev][EVENT_CHAPTER_COUNT] = 0
                    self.tasks.add(self.update_event, parameters=(ev,), priority=3)
            elif ev in evt_data: # this event already exists
                if now >= int(ev) and now_day - self.ev2daycount(ev) <= 14: # if happened in the last 14 days, we try to update again (mostly for daily skits)
                    self.tasks.print("Checking existing event:", ev)
                    self.tasks.add(self.update_event, parameters=(ev,), priority=3)
            else: # if the date is in the past, update, we skip anything else
                if now >= int(ev):
                    self.tasks.print("Checking new event:", ev)
                    self.tasks.add(self.check_event_exist, parameters=(ev,), priority=3)
        await self.tasks.start()

    # we check if we can access voice lines to detect if an event is accessible and its number of chapters. This solution isn't perfect
    async def check_event_exist(self : Updater, element_id : str) -> None:
        new_format = (element_id.isdigit() and int(element_id) == 241017) # bandaid for this particular event
        ts : TaskStatus = TaskStatus(-1, 1, running=EVENT_MAX_CHAPTER*2*2*(2 if new_format else 1)) # used to share the highest number of chapter found
        for i in range(0, EVENT_MAX_CHAPTER): # create takes for each chapter and possible sub episode and quest
            for j in range(1, 3):
                for k in range(1, 3):
                    self.tasks.add(self.check_event_voice_line, parameters=(ts, element_id, i, VOICE + "scene_evt{}_cp{}_q{}_s{}0".format(element_id, i, j, k)), priority=2)
                    if new_format: # bandaid
                        self.tasks.add(self.check_event_voice_line, parameters=(ts, element_id, i, VOICE + "scene_evt20{}_cp{}_q{}_s{}0".format(element_id, i, j, k)), priority=2)

    # check voice line existence
    async def check_event_voice_line(self : Updater, ts : TaskStatus, element_id : str, cp : int, uri : str) -> None:
        # we look over the 20 first lines to check if one exists
        for m in range(1, 20):
            if cp <= ts.index:
                break
            try:
                await self.head(uri + "_{}.mp3".format(m)) # note: we don't bother checking for variations, this function is simply trying to find ONE file
                if cp > ts.index:
                    ts.index = cp # we use the TaskStatus index variable to store the highest chapter we encountered
                break
            except:
                pass
        ts.finish()
        # the very last task is in charge of cleaning up
        if ts.finished:
            evt_data = self.data['events'] # reference
            if element_id not in evt_data: # add container in index if it doesn't exist yet
                evt_data[element_id] = self.create_event_container()
            if ts.index != -1: # if index not -1, we found a chapter
                evt_data[element_id][EVENT_CHAPTER_COUNT] = ts.index + 1 # set it
                self.tasks.add(self.update_event, parameters=(element_id,), priority=3)

    # Update an event data
    async def update_event(self : Updater, element_id : str, forceflag : bool = False) -> None:
        evt_data = self.data['events'] # reference
        if element_id not in evt_data: # add container to index if not set
            evt_data[element_id] = self.create_event_container()
        # we must have a valid chapter count (==0 : undefined but valid event, >=0 : chapter count)
        if forceflag or evt_data[element_id][EVENT_CHAPTER_COUNT] >= 0:
            name : str = SPECIAL_EVENTS.get(element_id, element_id) # retrieve file name id if special event
            prefix : str = "evt" if name.isdigit() else "" # and change prefix if the file name is special
            existings : list[set[str]] = [set(evt_data[element_id][i]) for i in range(EVENT_OP, len(evt_data[element_id]))] # make set of existing files
            ch_count = evt_data[element_id][EVENT_CHAPTER_COUNT] if not forceflag and evt_data[element_id][EVENT_CHAPTER_COUNT] > 0 else EVENT_MAX_CHAPTER # get the number of chapter to check
            ts : TaskStatus
            # chapters
            for i in range(0, ch_count+1):
                fn = "scene_{}{}_cp{}".format(prefix, name, str(i).zfill(2))
                ts = TaskStatus(200, 5, running=10)
                didx = EVENT_CHAPTER_START+i-1 if i > 0 else EVENT_INT
                for n in range(10):
                    self.tasks.add(self.update_chapter, parameters=(ts, 'events', element_id, didx, IMG + "sp/quest/scene/character/body/"+fn, existings[didx - EVENT_OP]), priority=2)
                if i < 10:
                    fn = "scene_{}{}_cp{}".format(prefix, name, i)
                    ts = TaskStatus(200, 5, running=10)
                    for n in range(10):
                        self.tasks.add(self.update_chapter, parameters=(ts, 'events', element_id, didx, IMG + "sp/quest/scene/character/body/"+fn, existings[didx - EVENT_OP]), priority=2)
            # opening
            fn = "scene_{}{}_op".format(prefix, name)
            ts = TaskStatus(200, 5, running=10)
            for n in range(10):
                self.tasks.add(self.update_chapter, parameters=(ts, 'events', element_id, EVENT_OP, IMG + "sp/quest/scene/character/body/"+fn, existings[EVENT_OP - EVENT_OP]), priority=2)
            # ending
            fn = "scene_{}{}_ed".format(prefix, name)
            ts = TaskStatus(200, 5, running=10)
            for n in range(10):
                self.tasks.add(self.update_chapter, parameters=(ts, 'events', element_id, EVENT_ED, IMG + "sp/quest/scene/character/body/"+fn, existings[EVENT_ED - EVENT_OP]), priority=2)
            # ending 2
            fn = "scene_{}{}_ed2".format(prefix, name)
            ts = TaskStatus(200, 5, running=10)
            for n in range(10):
                self.tasks.add(self.update_chapter, parameters=(ts, 'events', element_id, EVENT_ED, IMG + "sp/quest/scene/character/body/"+fn, existings[EVENT_ED - EVENT_OP]), priority=2)
            if element_id == "babyl0": # special exception (only for babyl right now)
                for ss in range(1, 30):
                    fn = "scene_babeel_01_ed{}".format(ss)
                    ts = TaskStatus(200, 5, running=10)
                    for n in range(10):
                        self.tasks.add(self.update_chapter, parameters=(ts, 'events', element_id, EVENT_ED, IMG + "sp/quest/scene/character/body/"+fn, existings[EVENT_ED - EVENT_OP]), priority=2)
                    fn = "scene_babeel_ed{}".format(ss)
                    ts = TaskStatus(200, 5, running=10)
                    for n in range(10):
                        self.tasks.add(self.update_chapter, parameters=(ts, 'events', element_id, EVENT_ED, IMG + "sp/quest/scene/character/body/"+fn, existings[EVENT_ED - EVENT_OP]), priority=2)
            # others
            fn = "scene_{}{}".format(prefix, name)
            ts = TaskStatus(200, 5, running=10)
            for n in range(10):
                self.tasks.add(self.update_chapter, parameters=(ts, 'events', element_id, EVENT_INT, IMG + "sp/quest/scene/character/body/"+fn, existings[EVENT_INT - EVENT_OP]), priority=2)

    ### Event Thumbnail #################################################################################################################

    async def update_all_event_thumbnail(self : Updater) -> None:
        # might need a revamp later as GBF is running out of space
        ts : TaskStatus = TaskStatus(2000, 50)
        for i in range(20):
            self.tasks.add(self.update_event_thumbnail, parameters=(7001, ts)) # 70000 range
        ts = TaskStatus(1000, 50)
        for i in range(20):
            self.tasks.add(self.update_event_thumbnail, parameters=(9001, ts)) # 90000 range

    async def update_event_thumbnail(self : Updater, start : int, ts : TaskStatus) -> None:
        eventthumb = self.data['eventthumb'] # reference
        while not ts.complete:
            try:
                i : int = start+ts.get_next_index() # get next id
                f : str = "{}0".format(i) # make filename/id
                if f not in eventthumb:
                    await self.head(IMG + "sp/archive/assets/island_m2/{}.png".format(f)) # try to request
                    eventthumb[f] = 0 # set it in memory
                    self.modified = True
                    self.tasks.print("New event thumbnail", f)
                ts.good()
            except:
                ts.bad()

    # function to import or export (controlled by in_or_out) manual_event_thumbnail.json
    def update_manual_event_thumbnail(self : Updater, in_or_out : bool = False) -> None:
        evt_data = self.data['events'] # reference
        if in_or_out: # import
            try:
                with open("json/manual_event_thumbnail.json", mode="r", encoding="utf-8") as f:
                    data = json.load(f)
                rdata = {}
                for k, v in data.items():
                    for ev in v:
                        rdata[ev] = k
                for element_id in evt_data:
                    tid = evt_data[element_id][EVENT_THUMB]
                    if tid is None:
                        if element_id in rdata:
                            evt_data[element_id][EVENT_THUMB] = rdata[element_id]
                            self.modified = True
                    else:
                        if element_id not in rdata:
                            evt_data[element_id][EVENT_THUMB] = None
                            self.modified = True
                        elif rdata[element_id] != evt_data[element_id][EVENT_THUMB]:
                            evt_data[element_id][EVENT_THUMB] = None
                            self.modified = True
                self.tasks.print("json/manual_event_thumbnail.json imported")
            except Exception as e:
                self.tasks.print("Failed to import json/manual_event_thumbnail.json")
                self.tasks.print("Exception:", e)
        else: # export
            try:
                data = {k:[] for k in self.data['eventthumb']}
                for element_id, evdata in evt_data.items():
                    if evdata[EVENT_THUMB] is not None:
                        if str(evdata[EVENT_THUMB]) not in data:
                            data[str(evdata[EVENT_THUMB])] = []
                        data[str(evdata[EVENT_THUMB])].append(element_id)
                keys = list(data.keys())
                keys.sort()
                data = {k:data[k] for k in keys}
                with open("json/manual_event_thumbnail.json", mode="w", encoding="utf-8") as f:
                    json.dump(data, f, separators=(',', ':'), ensure_ascii=False, indent=0)
                self.tasks.print("json/manual_event_thumbnail.json exported")
            except Exception as e:
                self.tasks.print("Failed to export json/manual_event_thumbnail.json")
                self.tasks.print("Exception:", e)

    ### Story #################################################################################################################

    # Update every (unset) story chapters
    async def update_all_story(self : Updater, limit : int|None = None) -> None:
        if limit is None or limit < 1: # upate limit accordingly
            if not self.use_wiki:
                self.tasks.print("Can't access the wiki to update the story")
                return
            try:
                # retrieve current last chapter from wiki
                m = CHAPTER_REGEX.findall((await self.get_wiki("https://gbf.wiki/Main_Quest")).decode('utf-8'))
                s = set()
                for i in m:
                    for j in i:
                        if j != "": s.add(int(j.replace('-', '')))
                limit = max(s)
            except:
                self.tasks.print("An error occured while attempting to retrieve the MSQ Chapter count from gbf.wiki")
                return
        existing : set[str]
        ts : TaskStatus
        # special recap chapters
        msq_data = self.data['story'] # reference
        for k in MSQ_RECAPS:
            if k not in msq_data:
                if k not in msq_data:
                    msq_data[k] = [[]]
                ts = TaskStatus(200, 5, running=10)
                existing = set(msq_data[k][STORY_CONTENT])
                for n in range(10):
                    self.tasks.add(self.update_chapter, parameters=(ts, 'story', k, STORY_CONTENT, IMG + "sp/quest/scene/character/body/scene_skip"+MSQ_RECAPS[k], existing), priority=2)
        # chapters
        for i in range(0, limit+1):
            element_id = str(i).zfill(3)
            if element_id not in msq_data:
                msq_data[element_id] = [[]]
                # set file name
                if i == 0:
                    fn = "tuto_scene"
                else:
                    fn = "scene_cp{}".format(i)
                ts = TaskStatus(200, 5, running=10)
                existing = set(msq_data[element_id][STORY_CONTENT])
                for n in range(10):
                    self.tasks.add(self.update_chapter, parameters=(ts, 'story', element_id, STORY_CONTENT, IMG + "sp/quest/scene/character/body/" + fn, existing), priority=2)
                for q in range(1, 6):
                    ts = TaskStatus(200, 5, running=10)
                    for n in range(10):
                        self.tasks.add(self.update_chapter, parameters=(ts, 'story', element_id, STORY_CONTENT, IMG + "sp/quest/scene/character/body/" + fn + "_q" + str(q), existing), priority=2)
        await self.tasks.start()

    ### Fate #################################################################################################################

    # load manual_fate.json, update it if needed and load/use its content if needed
    def update_manual_fate(self : Updater) -> None:
        try:
            with open("json/manual_fate.json", mode="r", encoding="utf-8") as f:
                data = json.load(f)
            self.tasks.print("Checking manual_fate.json...")
            modified = False
            # checking matching
            fate_data = self.data['fate'] # reference
            for k, v in data.items():
                if v is not None:
                    if k not in fate_data:
                        fate_data[k] = [[], [], [], [], v]
                        self.modified = True
                    elif fate_data[k][FATE_LINK] == None:
                        fate_data[k][FATE_LINK] = v
                        self.modified = True
                    else:
                        if v != fate_data[k][FATE_LINK]:
                            self.tasks.print("Mismatched ID for fate", k)
                else:
                    if k in fate_data and fate_data[k][FATE_LINK] is not None:
                        data[k] = fate_data[k][FATE_LINK]
                        modified = True
            # checking missing slots
            try:
                max_id = max([int(k) for k in list(fate_data.keys())])
                for i in range(1, max_id+1):
                    fi = str(i).zfill(4)
                    if fi not in data:
                        if fi in fate_data and fate_data[fi][FATE_LINK] is not None:
                            data[fi] = fate_data[fi][FATE_LINK]
                        else:
                            data[fi] = None
                        modified = True
            except:
                pass
            if modified:
                keys = list(data.keys())
                keys.sort()
                data = {k:data[k] for k in keys}
                with open("json/manual_fate.json", mode="w", encoding="utf-8") as f:
                    json.dump(data, f, separators=(',', ':'), ensure_ascii=False, indent=0)
                self.tasks.print("manual_fate.json updated")
        except Exception as e:
            self.tasks.print("Error checking manual_fate.json")
            self.tasks.print("Exception:", e)

    # get the latest/highest fate id
    def get_latest_fate(self : Updater) -> int:
        try:
            return max([int(k) for k in self.data['fate']]) # highest id in the index
        except:
            try:
                return len(self.data['characters']) # else the number of characters
            except:
                return 999 # else a placeholder

    # start tasks to check for a fate content
    # can set up to two file names to check, for an uncap level (see update_all_fate)
    async def check_fate(self : Updater, element_id : str, index : int, fid : str, nameA : str|None, epA_check : bool, nameB : str|None, epB_check : bool) -> None:
        ts : TaskStatus
        existing = set(self.data['fate'].get(fid, [[], [], [], [], None])[index])
        if nameA is not None:
            # nameA
            ts = TaskStatus(200, 5, running=10)
            for n in range(10):
                self.tasks.add(self.update_chapter, parameters=(ts, 'fate', fid, index, IMG + "sp/quest/scene/character/body/"+nameA, existing), priority=2)
            if epA_check:
                for q in range(1, 5):
                    ts = TaskStatus(200, 5, running=10)
                    for n in range(10):
                        self.tasks.add(self.update_chapter, parameters=(ts, 'fate', fid, index, IMG + "sp/quest/scene/character/body/"+nameA+"_ep"+str(q), existing), priority=2)
        if nameB is not None:
            # nameB
            ts = TaskStatus(200, 5, running=10)
            for n in range(10):
                self.tasks.add(self.update_chapter, parameters=(ts, 'fate', fid, index, IMG + "sp/quest/scene/character/body/"+nameB, existing), priority=2)
            if epB_check:
                for q in range(1, 5):
                    ts = TaskStatus(200, 5, running=10)
                    for n in range(10):
                        self.tasks.add(self.update_chapter, parameters=(ts, 'fate', fid, index, IMG + "sp/quest/scene/character/body/"+nameB+"_ep"+str(q), existing), priority=2)

    # Update all fate data (or the ones specified)
    # param can be:
    # None : Every fates are checked
    # a number : The corresponding fate is checked
    # a range (START-END included, format) : To check multiple episodes
    # last (a string) : To check most recent fates
    async def update_all_fate(self : Updater, param : str|None = None) -> None:
        # parse param
        try:
            if param is None or param == "":
                raise Exception()
            elif param == "last":
                self.flags.add("checking_event")
                max_chapter = self.get_latest_fate() + 5
                min_chapter = max_chapter - 8
            else:
                try:
                    min_chapter = int(param)
                    max_chapter = min_chapter
                except:
                    min_chapter, max_chapter = param.split("-")
                    min_chapter = int(min_chapter)
                    max_chapter = int(max_chapter)
        except:
            max_chapter = self.get_latest_fate() + 5
            min_chapter = 1
        min_chapter = max(1, min_chapter)
        if max_chapter < min_chapter:
            return
        if max_chapter == min_chapter:
            self.tasks.print("Checking fate episode:", min_chapter)
        else:
            self.tasks.print("Checking fate episode", min_chapter, "to", max_chapter)
        # check unique fates added via manual_fate.json (currently for baha and lucifer)
        fate_data = self.data['fate'] # reference
        for fid, v in fate_data.items():
            if not fid.isdigit() and len(v[0])+len(v[1])+len(v[2])+len(v[3]) == 0: # id not digit and data empty
                self.tasks.add(self.check_fate, parameters=(fid, FATE_UNCAP_CONTENT, fid, "scene_ult_{}".format(fid), True, None, False)) # only check this one for now
        # chapters
        chara_data = self.data['characters'] # reference
        for i in range(min_chapter, max_chapter+1):
            element_id = str(i).zfill(3)
            fid = str(i).zfill(4)
            # check base level
            self.tasks.add(self.check_fate, parameters=(element_id, FATE_CONTENT, fid, "scene_chr{}".format(element_id), False, "scene_fate_chr{}".format(element_id), False))
            # check uncaps (only if corresponding chara exists in memory and is set via manual_fate.json)
            if fid in fate_data and fate_data[fid][FATE_LINK] is not None:
                cid = fate_data[fid][FATE_LINK]
                if cid in chara_data:
                    if chara_data[cid]  == 0:
                        continue
                    uncap = 0
                    # calculate uncap
                    for entry in chara_data[cid][CHARA_GENERAL]:
                        if entry.endswith("_03"):
                            uncap = max(uncap, 1)
                        elif entry.endswith("_04"):
                            uncap = max(uncap, 2)
                    if uncap >= 1: # uncap
                        self.tasks.add(self.check_fate, parameters=(element_id, FATE_UNCAP_CONTENT, fid, "scene_ult_chr{}".format(element_id), True, None, False))
                    if uncap >= 2: # transcendence
                        self.tasks.add(self.check_fate, parameters=(element_id, FATE_TRANSCENDENCE_CONTENT, fid, "scene_ult2_chr{}".format(element_id), True, None, False))
                # evokers
                if cid in ("3040160000", "3040161000", "3040162000", "3040163000", "3040164000", "3040165000", "3040166000", "3040167000", "3040168000", "3040169000"):
                    self.tasks.add(self.check_fate, parameters=(element_id, FATE_UNCAP_CONTENT, fid, "scene_ult_chr{}_world".format(element_id), True, None, False))
        await self.tasks.start()

    ### Sound #################################################################################################################

    # the functions are similar to scene ones
    # this one update the sound data of all elements and support resuming and filtering
    async def update_all_sound(self : Updater, filters : list[str] = []) -> None:
        self.flags.add("use_resume")
        self.flags.add("sound_update")
        self.load_resume("sound")
        if len(self.resume.get('done', {})) != 0:
            self.tasks.print("Note: Resuming the previous run...")
        if len(filters) > 0:
            self.tasks.print("Note: {} filter(s) in use. Not matching filenames will be ignored.".format(len(filters)))
        if 'name' not in self.resume:
            self.resume['name'] = "sound"
        if 'done' not in self.resume:
            self.resume['done'] = {}
        for index in ("characters", "skins", 'npcs'):
            for element_id in self.data[index]:
                self.tasks.add(self.update_sound_of, parameters=(element_id, index, filters))
        self.tasks.print("Updating sounds for {} elements...".format(self.tasks.total))
        await self.tasks.start()
        self.clear_resume()

    # cache sound strings if needed and return them
    def get_sound_strings(self : Updater) -> list[tuple[str, list[str], int, int, int]]:
        if len(self.sound_base_strings) == 0:
            suffixes : list[str]
            A : int
            max_err : int
            for mid, Z in (("_", 3), ("_introduce", 1), ("_mypage", 1), ("_formation", 2), ("_evolution", 2), ("_archive", 2), ("_zenith_up", 2), ("_zenith_lankup", 2), ("_kill", 2), ("_ready", 2), ("_damage", 2), ("_healed", 2), ("_dying", 2), ("_power_down", 2), ("_cutin", 1), ("_attack", 1), ("_attack", 2), ("_ability_them", 1), ("_ability_us", 1), ("_mortal", 1), ("_win", 1), ("_lose", 1), ("_hp_down", 2), ("_to_player", 1), ("d_boss_v_", 1)):
                match mid: # opti
                    case "_":
                        suffixes = ["", "a", "b"]
                        A = 1
                        max_err = 2
                    case "d_boss_v_": # athena militis only ?...
                        suffixes = [""]
                        A = 1
                        max_err = 5
                    case _:
                        suffixes = ["", "a", "_a", "_1", "b", "_b", "_2", "_mix"]
                        A = 0 if mid == "_cutin" else 1
                        max_err = 2
                self.sound_base_strings.append((mid + "{}", suffixes, A, Z, max_err))
            for i in range(0, 10): # break down _navi for speed, up to 100
                self.sound_base_strings.append(("_boss_v_" + ("" if i == 0 else str(i)) + "{}", ["", "a", "_a", "_1", "b", "_b", "_2", "_mix"], 0, 1, 6))
            for i in range(0, 65): # break down _v_ for speed, up to 650
                self.sound_base_strings.append(("_v_" + str(i).zfill(2) + "{}", ["", "a", "_a", "_1", "b", "_b", "_2", "c", "_c", "_3"], 0, 1, 6))
            # chain burst
            self.sound_base_strings.append(("_chain_start", [], None, None, None))
            for A in range(2, 5):
                self.sound_base_strings.append(("_chain{}_"+str(A), [], 1, 1, 1))
            # seasonal A
            for mid, Z in (("_birthday", 1), ("_Birthday", 1), ("_birthday_mypage", 1), ("_newyear_mypage", 1), ("_newyear", 1), ("_Newyear", 1), ("_valentine_mypage", 1), ("_valentine", 1), ("_Valentine", 1), ("_white_mypage", 1), ("_whiteday", 1), ("_Whiteday", 1), ("_WhiteDay", 1), ("_halloween_mypage", 1), ("_halloween", 1), ("_Halloween", 1), ("_christmas_mypage", 1), ("_christmas", 1), ("_Christmas", 1), ("_xmas", 1), ("_Xmas", 1)):
                self.sound_base_strings.append((mid + "{}", [], 1, Z, 5))
            for suffix in ("white","newyear","valentine","christmas","halloween","birthday"):
                for s in range(1, 6):
                    self.sound_base_strings.append(("_s{}_{}".format(s, suffix) + "{}", [], 1, 1, 5))
        return self.sound_base_strings

    # Execution flow
    #
    #   update_sound_of
    #       v
    #   update_sound_end & update_sound_banter (one) & update_sound (for each string and uncap)
    #

    async def update_sound_of(self : Updater, element_id : str, index : str, filters : list[str] = []) -> None:
        if 'sound_update' in self.flags and element_id in self.resume.get('done', {}):
            return
        u : str
        uncaps : list[str]
        idx : int
        try: # first retrieve index, index in data, uncaps and existing strings
            data : list[Any] = self.data[index][element_id]
            match index:
                case 'characters'|'skins':
                    idx = CHARA_SOUND
                    uncaps= []
                    for u in data[CHARA_GENERAL]:
                        uu = u.replace(element_id+"_", "")
                        if "_" not in uu and uu.startswith("0") and uu != "02": # 02 unused(?)
                            uncaps.append(uu)
                    if len(uncaps) == 0:
                        uncaps.append("")
                case 'npcs':
                    idx = NPC_SOUND
                    uncaps = [""]
                case _:
                    return
            existing : set[str] = set(data[idx])
        except:
            return
        # retrieve suffix strings to be used
        bs = self.get_sound_strings()
        # TaskStatus for all tasks
        ts = TaskStatus(1, 1, running=(len(bs) * len(uncaps) + 1))
        # banter files
        if self.file_is_matching("_pair_", filters): # don't start this task if it doesn't match filter
            self.tasks.add(self.update_sound_banter, parameters=(index, element_id, idx, existing, ts, filters), priority=0)
        else:
            ts.finish()
        # other files (per uncap)
        for u in uncaps:
            if u in ("", "01"):
                u = ""
            else:
                u = "_" + u
            for sound_string in bs: # for each string
                if self.file_is_matching(sound_string[0], filters): # don't start this task if it doesn't match filter
                    self.tasks.add(self.update_sound, parameters=(index, element_id, idx, existing, ts, u, sound_string), priority=0)
                else:
                    ts.finish()
        # call final step (if needed)
        if not ts.finished:
            self.tasks.add(self.update_sound_end, parameters=(index, element_id, idx, existing, ts), priority=0)

    # Updae sound data for given suffix and uncap
    async def update_sound(self : Updater, index : str, element_id : str, idx : int, existing : set[str], ts : TaskStatus, uncap : str, sound_string : tuple[str, list[str], int, int, int]) -> None:
        # unpack sound_string
        suffix, post, current, zfill, max_err = sound_string
        # don't test uncaps for those suffixes
        if uncap != "" and suffix in ("_", "d_boss_v_", "_boss_v_"):
            ts.finish()
            return
        # post suffix not set
        if len(post) == 0:
            post = [""]
        # there are two possible mode, used depending on the file
        if current is None: # simple mode
            for p in post:
                f = uncap + suffix + p
                if f in existing:
                    existing.add(f)
                else:
                    try:
                        await self.head(VOICE + "{}{}.mp3".format(element_id, f))
                        existing.add(f)
                    except:
                        pass
        else: # complex mode
            err = 0
            is_z_limited = suffix.startswith('_v_') or suffix.startswith('_boss_v_')
            while not is_z_limited or (is_z_limited and len(str(current)) <= zfill):
                found = False
                for p in post: # check if already processed in the past
                    f = uncap + suffix.format(str(current).zfill(zfill)) + p
                    if f in existing:
                        found = True
                        err = 0
                        break
                if not found: # if not
                    for p in post:
                        f = uncap + suffix.format(str(current).zfill(zfill)) + p
                        if f not in existing:
                            try:
                                await self.head(VOICE + "{}{}.mp3".format(element_id, f))
                                found = True
                                existing.add(f)
                            except:
                                pass
                        else:
                            found = True
                    if not found:
                        err += 1
                        if err >= max_err and current > 0:
                            break
                    else:
                        err = 0
                current += 1
        ts.finish()

    # special one for banter files
    async def update_sound_banter(self : Updater, index : str, element_id : str, idx : int, existing : set, ts : TaskStatus, filters : list[str] = []) -> None:
        A : int = 1
        B : int = 1
        Z : int|None = None
        while True:
            success = False
            for i in range(1, 3):
                if Z is None or Z == i:
                    try:
                        f = "_pair_{}_{}".format(A, str(B).zfill(i))
                        if f not in existing:
                            await self.head(VOICE + "{}{}.mp3".format(element_id, f))
                        existing.add(f)
                        success = True
                        Z = i
                        break
                    except:
                        pass
            if success:
                B += 1
            else:
                if B == 1:
                    break
                else:
                    A += 1
                    B = 1
        ts.finish()

    # final step
    async def update_sound_end(self : Updater, index : str, element_id : str, idx : int, existing : set[str], ts : TaskStatus) -> None:
        # Wait tasks to finish
        while not ts.finished:
            await asyncio.sleep(1)
        # If modified
        elem_data = self.data[index][element_id] # reference
        if len(existing) > len(elem_data[idx]):
            elem_data[idx] = list(existing) # no need to sort
            self.modified = True
        # Add to resume file
        if "sound_update" in self.flags:
            self.resume['done'][element_id] = 0

    ### Lookup ##################################################################################################################

    # Check for new elements to lookup on the wiki, to update the lookup list
    # Gigantic function but nothing complicated
    async def lookup(self : Updater) -> None:
        if not self.use_wiki or 'lookup_updated' in self.flags:
            return
        self.flags.add('lookup_updated')
        npcs = self.data['npcs'] # reference
        lookup_data = self.data['lookup'] # reference
        modified = set()
        # Read manual_lookup.json and update data.json
        try:
            self.tasks.print("Importing manual_lookup.json ...")
            with open("json/manual_lookup.json", mode="r", encoding="utf-8") as f:
                data = json.load(f)
            # check entries
            to_save = False
            for t in ('npcs', "enemies"):
                for k in self.data[t]:
                    s = lookup_data.get(k, None)
                    valid = s is not None and s != "" and not s.startswith("missing-help-wanted")
                    if valid and data.get(k, None) is None:
                        if '@@' in s:
                            s = s.split("@@", 1)[1].split(" ", 1)[1]
                        s = s.split(" ")
                        i = 0
                        while i < len(s):
                            if s[i] in ("/", "N", "R", "SR", "SSR", "n", "r", "sr", "ssr", "sabre", "axe", "spear", "gun", "staff", "melee", "harp", "katana", "bow", "dagger", "fire", "water", "earth", "wind", "light", "dark"):
                                i += 1
                            else:
                                break
                        s = " ".join(s[i:]).replace(' voiced', '').replace(' voice-only', '')
                        if s == "" or data.get(k, "") == s: continue
                        data[k] = s
                        to_save = True
                    elif not valid and k not in data:
                        data[k] = None
                        to_save = True
            if to_save:
                keys = list(data.keys())
                keys.sort(key=lambda s : (10 - len(s), s))
                data = {k : data[k] for k in keys}
                with open("json/manual_lookup.json", mode="w", encoding="utf-8") as f:
                    json.dump(data, f, separators=(',', ':'), ensure_ascii=False, indent=0)
                self.tasks.print("json/manual_lookup.json updated with new entries")
        except OSError as e:
            self.tasks.print("Couldn't open json/manual_lookup.json")
            self.tasks.print(e)
            data = {}
        except Exception as e:
            self.tasks.print("Couldn't load json/manual_lookup.json")
            self.tasks.print(e)
            data = {}
        # Fill manual_lookup.json
        try:
            for k, v in data.items():
                try:
                    voice = (len(k) == 10 and npcs.get(k, 0) != 0 and len(npcs[k][NPC_SOUND]) > 0)
                    voice_only = voice and not npcs[k][NPC_JOURNAL] and len(npcs[k][NPC_SCENE]) == 0
                    if v is None or v == "":
                        if lookup_data.get(k, "missing-help-wanted").startswith("missing-help-wanted"):
                            l = "missing-help-wanted"
                            if voice:
                                l += " voiced"
                                if not voice_only:
                                    l += " voice-only"
                            if l != lookup_data.get(k, None):
                                lookup_data[k] = l
                                modified.add(k)
                        continue
                    if "$$" not in v and "$" in v: self.tasks.print("Missing $ Warning for", k, "in manual_lookup.json")
                    match len(k):
                        case 10: # npc
                            if "@@" in lookup_data.get(k, ""): continue
                            if "$$" in v:
                                v = " ".join(v.split("$$")[0])
                            append = ""
                        case 7: # enemy
                            if "$$" in v:
                                vs = v.split("$$")
                                if vs[1] not in ("fire", "water", "earth", "wind", "light", "dark", "null", "unknown-element"):
                                    self.tasks.print("Element Warning for", k, "in manual_lookup.json")
                                v = vs[1] + " " + vs[0]
                            else:
                                self.tasks.print("Element Warning for", k, "in manual_lookup.json")
                            match k[:2]:
                                case "11":
                                    append = " flying-boss"
                                case "12":
                                    append = " beast-boss"
                                case "13":
                                    append = " monster-boss"
                                case "21":
                                    append = " plant-boss"
                                case "22":
                                    append = " insect-boss"
                                case "31":
                                    append = " fish-boss"
                                case "41":
                                    append = " golem-boss"
                                case "42":
                                    append = " aberration-boss"
                                case "43":
                                    append = " machine-boss"
                                case "51":
                                    append = " otherworld-boss"
                                case "52":
                                    append = " undead-boss"
                                case "61":
                                    append = " goblin-boss"
                                case "62":
                                    append = " people-boss"
                                case "63":
                                    append = " fairy-boss"
                                case "71":
                                    append = " wyvern-boss"
                                case "72":
                                    append = " reptile-boss"
                                case "73":
                                    append = " dragon-boss"
                                case "81":
                                    append = " primal-boss"
                                case "82":
                                    append = " elemental-boss"
                                case "83":
                                    append = " core-boss"
                                case "91":
                                    append = " other-boss"
                                case _:
                                    append =" unknown-boss"
                    vs = v.split(" ")
                    if vs[0] in ("/", "N", "R", "SR", "SSR", "n", "r", "sr", "ssr"):
                        vs = vs[1:]
                    l = (" ".join(vs) + append).lower().strip().replace('(', ' ').replace(')', ' ').replace('（', ' ').replace('）', ' ').replace(',', ' ').replace('、', ' ').replace('  ', ' ').replace('  ', ' ')
                    if voice:
                        l += " voiced"
                        if voice_only:
                            l += " voice-only"
                    if l != lookup_data.get(k, ""):
                        lookup_data[k] = l
                        modified.add(k)
                except:
                    pass
        except Exception as e:
            self.tasks.print("An error occured while updating the lookup table with json/manual_lookup.json", e)
        # Wiki stuff
        premium_lookup = {}
        weapon_associations = {}
        tables = {'job':['classes', 'mc_outfits'], 'skins':['character_outfits'], 'npcs':['npc_characters']} # table of data index == wiki cargo tables
        fields = {'characters':'id,element,rarity,name,series,race,gender,type,weapon,jpname,va,jpva,release_date,obtain,join_weapon', 'weapons':'id,element,type,rarity,name,series,jpname,release_date,character_unlock', 'summons':'id,element,rarity,name,series,jpname,release_date,obtain', 'classes':'id,name,jpname,release_date', 'mc_outfits':'outfit_id,outfit_name,release_date', 'character_outfits':'outfit_id,outfit_name,character_name,release_date', 'npc_characters':'id,name,series,race,gender,jpname,va,jpva,release_date'}
        # above are the cargo table to access and the fields we want for each of them
        for t in LOOKUP_TYPES:
            for table in tables.get(t, [t]):
                try:
                    self.tasks.print("Checking", table, "wiki cargo table for", t, "lookup...")
                    data = (await self.get_wiki("https://gbf.wiki/index.php?title=Special:CargoExport&tables={}&fields=_pageName,{}&format=json&limit=20000".format(table, fields.get(table)), get_json=True))
                    await asyncio.sleep(0.2)
                    # read items in the table
                    for item in data:
                        # check main infos
                        match table:
                            case "classes"|"mc_outfits":
                                looks = ["gran", "djeeta"]
                            case _:
                                looks = []
                        if item.get('element', '') == 'any':
                            continue
                        # read all infos
                        wiki = ""
                        for k, v in item.items():
                            match v:
                                case str():
                                    match k:
                                        case "outfit id":
                                            continue
                                        case "id":
                                            continue
                                        case "gender":
                                            if v.lower() in {"other", "male", "female"}:
                                                looks.append(v.lower())
                                            else:
                                                for c in v:
                                                    looks.append({"o":"other", "m":"male", "f":"female"}.get(c.lower(), c.lower()))
                                        case "_pageName":
                                            wiki = "@@" + html.unescape(v).replace(' ', '_') + " "
                                        case "rarity":
                                            looks.append(v.lower())
                                        case "race":
                                            if v == "Other":
                                                looks.append("unknown")
                                            else:
                                                looks.append(v.lower())
                                        case "series":
                                            looks.append(v.lower().replace(';', ' '))
                                        case "join weapon":
                                            if len(item.get("obtain", [])) > 0:
                                                obtain = set(item["obtain"][0].split(","))
                                                if "classic" in obtain or  "classic2" in obtain or "flash" in obtain or "premium" in obtain:
                                                    weapon_associations[v] = item["id"]
                                                    premium_lookup[str(item["id"])] = None
                                        case "character unlock":
                                            if item["name"] in weapon_associations:
                                                premium_lookup[str(weapon_associations[item["name"]])] = str(item["id"]) # character id = weapon id
                                                premium_lookup[str(item["id"])] = str(weapon_associations[item["name"]]) # weapon id = character id
                                        case "obtain": # summon
                                            if table == "summons" and v is not None and v != "":
                                                obtain = set(v.split(","))
                                                if "classic" in obtain or  "classic2" in obtain or "flash" in obtain or "premium" in obtain:
                                                    premium_lookup[str(item["id"])] = None
                                        case _:
                                            looks.append(v.lower())
                                case list():
                                    for e in v:
                                        if k == "obtain":
                                            continue
                                        elif k == "race" and e == "Other":
                                            looks.append("unknown")
                                        elif e != "-":
                                            looks.append(e.lower())
                                case _:
                                    pass
                        try:
                            id = str(item['id']).split('_', 1)[0]
                        except:
                            id = str(item['outfit id']).split('_', 1)[0]
                        # prepare lookup string
                        looks = wiki + html.unescape(" ".join(looks)).replace(' tie-in ', ' collab ').replace('(', ' ').replace(')', ' ').replace('（', ' ').replace('）', ' ').replace(',', ' ').replace('、', ' ').replace('<br />', ' ').replace('<br />', ' ').replace('  ', ' ').replace('  ', ' ').strip()
                        # voice
                        if len(id) == 10 and npcs.get(id, 0) != 0 and len(npcs[id][NPC_SOUND]) > 0: # npc sound
                            looks += " voiced"
                            if not npcs[id][NPC_JOURNAL] and len(npcs[id][NPC_SCENE]) == 0:
                                looks += " voice-only"
                        if id not in lookup_data or lookup_data[id] != looks:
                            lookup_data[id] = looks
                            modified.add(id)
                except Exception as e:
                    self.tasks.print(e)
                    pass
        # update premium table if different
        if premium_lookup != self.data['premium']:
            self.data['premium'] = premium_lookup
            self.modified = True
        # Second pass, correcting stuff
        if len(modified) > 0:
            self.tasks.print(len(modified), "element lookup(s) added/updated")
            self.modified = True
            count = 0
            # second pass
            for t in LOOKUP_TYPES:
                for k in self.data[t]:
                    check_shared = False
                    if k not in lookup_data or lookup_data[k] is None:
                        if k in SPECIAL_LOOKUP:
                            lookup_data[k] = SPECIAL_LOOKUP[k]
                        else:
                            check_shared = True
                    else:
                        if k not in modified and k in SPECIAL_LOOKUP and lookup_data[k] != SPECIAL_LOOKUP[k]:
                            lookup_data[k] = SPECIAL_LOOKUP[k]
                        check_shared = True
                    if check_shared:
                        for l in SHARED_LOOKUP:
                            if k not in l: continue
                            for m in l:
                                if m != k and m in lookup_data and m is not None and lookup_data[m] is not None:
                                    lookup_data[k] = lookup_data[m].replace(m, k)
                                    break
                                break
                    if not check_shared:
                        count += 1
            self.tasks.print(count, "element(s) remaining without lookup data")
        self.save()
        self.tasks.print("Done")

    ### Maintenance #################################################################################################################

    # Called by maintenancebuff
    async def maintenance_buff(self : Updater) -> None:
        if "maintenance_buff" in self.flags:
            return
        self.flags.add("maintenance_buff")
        self.tasks.add(self.maintenance_compare_wiki_buff)
        self.tasks.print("Starting tasks to update known Buffs...")
        for element_id in self.data['buffs']:
            await self.prepare_update_buff(element_id)
        await self.tasks.start()

    # Called by maintenancebuff, maintenance or process_flags
    async def maintenance_compare_wiki_buff(self : Updater) -> None:
        try:
            if not self.use_wiki or "maintenance_buff_wiki" in self.flags:
                return
            self.flags.add("maintenance_buff_wiki")
            buffs = self.data['buffs'] # reference
            self.tasks.print("Comparing data with gbf.wiki buff list...")
            checked : set[str] = set()
            data = await self.get_wiki("https://gbf.wiki/api.php?action=query&prop=revisions&titles=Module:StatusList&rvslots=main&rvprop=content&formatversion=2&format=json", get_json=True)
            bid : str
            ext : str
            count : int = 0
            for line in data['query']['pages'][0]['revisions'][0]['slots']['main']['content'].split('\n'):
                if line.strip().startswith('status ='):
                    icon : str = line.split("'")[1].strip()
                    if icon == "":
                        continue
                    elif "_" in icon:
                        bid = icon.split('_', 1)[0].zfill(4)
                        ext = '_' + icon.split('_', 1)[1]
                    elif icon.isdigit() and len(icon) >= 5:
                        bid = icon[:4]
                        ext = icon[4:]
                    else:
                        bid = icon.zfill(4)
                        ext = ""
                    if len(bid) >= 5:
                        ext = bid[4:] + ext
                        bid = bid[:4]
                    if isinstance(buffs.get(bid, None), int): # uninitialized buff, skip
                        continue
                    if bid not in buffs:
                        # check if icon exists
                        if not await self.head_nx("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/ui/icon/status/x64/status_" + icon + ".png"):
                            continue
                        buffs[bid] = [[str(int(bid))], [ext]]
                        self.modified = True
                        self.add(bid, ADD_BUFF)
                        count += 1
                    elif ext not in buffs[bid][1]:
                        if not await self.head_nx("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/ui/icon/status/x64/status_" + icon + ".png"):
                            continue
                        buffs[bid][1].append(ext)
                        buffs[bid][1].sort(key=lambda x: str(x.count('_'))+"".join([j.zfill(3) for j in x.split('_')]))
                        self.modified = True
                        self.add(bid, ADD_BUFF)
                        # do a full check of that buff (if it hasn't been done)
                        if bid not in checked:
                            checked.add(bid)
                            self.tasks.add(self.prepare_update_buff, parameters=(bid,))
                        count += 1
            if count > 0:
                self.tasks.print("Updated", count, "buff(s)")
        except Exception as e:
            self.tasks.print("An error occured while comparing with gbf.wiki buff list")
            self.tasks.print(self.print("".join(traceback.format_exception(type(e), e, e.__traceback__))))

    # Called by maintenancenpcthumbnail, maintenance or process_flags
    async def maintenance_npc_thumbnail(self : Updater) -> None:
        if "maintenance_npc_thumbnail" in self.flags:
            return
        self.flags.add("maintenance_npc_thumbnail")
        self.tasks.print("Starting tasks to update known NPC thumbnails...")
        for element_id in self.data['npcs']:
            if not isinstance(self.data['npcs'][element_id], int) and not self.data['npcs'][element_id][NPC_JOURNAL]:
                self.tasks.add(self.update_npc_thumb, parameters=(element_id,))
        await self.tasks.start()

    # maintenance_npc_thumbnail() subroutine
    async def update_npc_thumb(self : Updater, element_id : str) -> None: # subroutine
        try:
            await self.head(IMG + "sp/assets/npc/m/{}_01.jpg".format(element_id))
            self.data['npcs'][id][NPC_JOURNAL] = True
            self.modified = True
        except:
            pass

    # Called by maintenanceraidappear, maintenance or process_flags
    async def maintenance_raid_appear(self : Updater) -> None:
        if "maintenanceraidappear" in self.flags:
            return
        self.flags.add("maintenanceraidappear")
        self.tasks.print("Starting tasks to update known enemies raid appear animations...")
        for element_id in self.data['enemies']:
            if not isinstance(self.data['enemies'][element_id], int):
                self.tasks.add(self.update_enemy_appear, parameters=(element_id,))
        await self.tasks.start()

    # maintenance_raid_appear() subroutine
    async def update_enemy_appear(self : Updater, element_id : str) -> None: # subroutine
        existing : list[str] = self.data["enemies"][element_id][BOSS_APPEAR]
        appear : list[str] = []
        for k in ("", "_2", "_3", "_4", "_5", "_shade"):
            try:
                fn = "raid_appear_{}{}".format(element_id, k)
                lfn = len(fn)
                found = False
                for f in existing:
                    if f.startswith(fn) and f[lfn:lfn+2] in {".p", "_a", "_b", "_c", "_d", "_e", "_f", "_g", "_h", "_i", "_j"}: # to ensure raid_appear isn't matching raid_appear_2
                        found = True
                        appear.append(f)
                if not found:
                    appear += await self.processManifest(fn)
            except:
                pass
        if len(appear) != len(existing):
            self.data["enemies"][element_id][BOSS_APPEAR] = appear
            self.add(element_id, ADD_BOSS)
            self.tasks.print("New appear animations for ", element_id)

    # Called by maintenancesky, maintenance or process_flags
    async def maintenance_event_skycompass(self : Updater) -> None:
        if "maintenance_event_skycompass" in self.flags:
            return
        self.flags.add("maintenance_event_skycompass")
        self.tasks.print("Starting tasks to update known Events Skycompass Arts...")
        for ev in self.data['events']:
            if self.data['events'][ev][EVENT_THUMB] is not None:
                self.tasks.add(self.update_event_skycompass, parameters=(ev,))
        self.tasks.add(self.update_all_event_thumbnail)
        await self.tasks.start()

    # Check if an event got skycompass art. Note: The event must have a valid thumbnail ID set
    async def update_event_skycompass(self : Updater, ev : str) -> None:
        known = set(self.data['events'][ev][EVENT_SKY])
        evid = self.data['events'][ev][EVENT_THUMB]
        try:
            i = max(self.data['events'][ev][EVENT_SKY]) + 1
        except:
            i = 1
        modified = False
        while True:
            if i not in known:
                try:
                    await self.head("https://media.skycompass.io/assets/archives/events/{}/image/{}_free.png".format(evid, i))
                    known.add(i)
                    modified = True
                except:
                    break
            i+=1
        if modified:
            self.modified = True
            known = list(known)
            known.sort()
            self.data['events'][ev][EVENT_SKY] = known

    ### Other #################################################################################################################

    # check file existence for npcs ids without any data
    async def search_missing_npc(self : Updater) -> None:
        npcs = self.data['npcs'] # reference
        try:
            highest : int = (max([int(k) for k in npcs if k.startswith('399')]) // 1000) % 10000
        except:
            return
        # scene
        base_target, main_x, uncap_x = self.generate_scene_file_list()
        scene_strings : list[str] = base_target + main_x
        # sound
        sound_strings : list[str] = (["_v_" + str(i).zfill(3) for i in range(5, 200, 5)] + ["_v_001", "_boss_v_1", "_boss_v_2", "_boss_v_3", "_boss_v_4", "_boss_v_5", "_boss_v_10", "_boss_v_15", "_boss_v_20", "_boss_v_25", "_boss_v_30", "_boss_v_35", "_boss_v_45", "_boss_v_50", "_boss_v_55", "_boss_v_60", "_boss_v_65", "_boss_v_70", "_boss_v_75", "d_boss_v_1"])
        # concat
        uris : list[tuple[str, int]] = []
        # other
        count : int = 0
        for s in scene_strings:
            for u in ("", "_02", "_03"):
                uris.append((IMG + "sp/quest/scene/character/body/{}" + "{}{}.png".format(u, s), NPC_SCENE))
                uris.append((IMG + "sp/raid/navi_face/{}" + "{}{}.png".format(u, s), NPC_SCENE))
        for s in sound_strings:
            uris.append((SOUND + "voice/{}" + "{}.mp3".format(s), NPC_SOUND))
        for i in range(0, highest+5):
            fid : str = "399{}000".format(str(i).zfill(4))
            if npcs.get(fid, 0) == 0:
                count += 1
                ts : TaskStatus = TaskStatus(len(uris), 1)
                for j in range(20):
                    self.tasks.add(self.test_missing_npc, parameters=(fid, ts, uris))
        self.tasks.print("Testing", count, "NPCs...")
        await self.tasks.start()

    async def test_missing_npc(self : Updater, element_id : str, ts : TaskStatus, uris : list[str]) -> None:
        npcs = self.data['npcs'] # reference
        while not ts.complete:
            url, idx = uris[ts.get_next_index()]
            try:
                await self.head(url.format(element_id))
                if element_id not in npcs:
                    self.modified = True
                    npcs[element_id] = [False, [], []]
                    npcs[element_id][idx].append(url.format(element_id).split('/')[-1].split('.')[0])
                    self.tasks.add(self.update_scenes_of, parameters=(element_id, 'npcs'))
                    self.tasks.add(self.update_sound_of, parameters=(element_id, 'npcs'))
                    self.add(element_id, ADD_NPC)
                    self.flags.add("found_character")
                    self.tasks.print("Found NPC:", element_id, "(Queuing secondary updates...)")
                    ts.bad() # to force stop the other tasks
            except Exception as e:
                if str(e) != "HTTP error 404":
                    self.tasks.print(url.format(element_id))
                    self.tasks.print(e)

    # simply call update_element on each partner id
    async def update_all_partner(self : Updater) -> None:
        for element_id in self.data['partners']:
            self.tasks.add(self.update_element, parameters=(element_id, None))
        await self.tasks.start()

    # Update changelog.json stat string
    def make_stats(self) -> None:
        try:
            entity_count = 0
            scene_count = 0
            sound_count = 0
            file_estimation = 0
            for t in ("characters", "partners", "summons", "weapons", "enemies", "skins", "job", 'npcs', "title", "sky_title", "suptix", 'events', "skills", "subskills", 'buffs', "story", "background", "mypage_bg"):
                ref = self.data.get(t, {})
                entity_count += len(ref.keys())
                for k, v in ref.items():
                    match t:
                        case "characters"|"skins"|"partners":
                            if v is None or v == 0: continue
                            file_estimation += len(v[CHARA_SPRITE])
                            file_estimation += len(v[CHARA_PHIT])
                            file_estimation += len(v[CHARA_SP])
                            file_estimation += len(v[CHARA_AB_ALL])
                            file_estimation += len(v[CHARA_AB])
                            file_estimation += len(v[CHARA_GENERAL]) * 32
                            if t != "partners":
                                file_estimation += len(v[CHARA_SD]) * 5
                                file_estimation += len(v[CHARA_SCENE])
                                file_estimation += len(v[CHARA_SOUND])
                                
                                scene_count += len(v[CHARA_SCENE])
                                sound_count += len(v[CHARA_SOUND])
                                sound_count += len(v[CHARA_MYPAGE])
                        case "summons":
                            if v is None or v == 0: continue
                            file_estimation += len(v[SUM_GENERAL]) * 12
                            file_estimation += len(v[SUM_CALL])
                            file_estimation += len(v[SUM_DAMAGE])
                        case "weapons":
                            if v is None or v == 0: continue
                            file_estimation += len(v[WEAP_GENERAL]) * 9
                            file_estimation += len(v[WEAP_PHIT])
                            file_estimation += len(v[WEAP_SP])
                        case "shields"|"manaturas":
                            if v is None or v == 0: continue
                            file_estimation += 3
                        case "job":
                            if v is None or v == 0: continue
                            file_estimation += len(v[JOB_ID]) * 5
                            file_estimation += len(v[JOB_ALT]) * 3
                            file_estimation += len(v[JOB_DETAIL]) * 4
                            file_estimation += len(v[JOB_DETAIL_ALT]) * 15
                            file_estimation += len(v[JOB_DETAIL_ALL])
                            
                            file_estimation += len(v[JOB_SPRITE])
                            file_estimation += len(v[JOB_PHIT])
                            file_estimation += len(v[JOB_SP])
                            file_estimation += len(v[JOB_UNLOCK])
                            file_estimation += len(v[JOB_MYPAGE])
                        case "enemies":
                            if v is None or v == 0: continue
                            file_estimation += len(v[BOSS_GENERAL])
                            file_estimation += len(v[BOSS_SPRITE])
                            file_estimation += len(v[BOSS_APPEAR])
                            file_estimation += len(v[BOSS_HIT])
                            file_estimation += len(v[BOSS_SP])
                            file_estimation += len(v[BOSS_SP_ALL])
                        case 'events':
                            if v is None or v == 0: continue
                            if v[EVENT_THUMB] is not None: file_estimation += 1
                            for i in range(EVENT_OP, EVENT_SKY+1):
                                file_estimation += len(v[i])
                        case "story":
                            if v is None or v == 0: continue
                            file_estimation += len(v[STORY_CONTENT])
                        case "fate":
                            if v is None or v == 0: continue
                            file_estimation += len(v[FATE_CONTENT])
                            file_estimation += len(v[FATE_UNCAP_CONTENT])
                            file_estimation += len(v[FATE_TRANSCENDENCE_CONTENT])
                            file_estimation += len(v[FATE_OTHER_CONTENT])
                        case "npcs":
                            if v is None or v == 0: continue
                            if v[NPC_JOURNAL]: file_estimation += 1
                            file_estimation += len(v[NPC_SCENE])
                            file_estimation += len(v[NPC_SOUND])
                            
                            scene_count += len(v[NPC_SCENE])
                            sound_count += len(v[NPC_SOUND])
                        case "buffs":
                            if v is None or v == 0: continue
                            file_estimation += len(v[1])
                        case "background":
                            if v is None or v == 0: continue
                            file_estimation += len(v[0])
                        case "mypage_bg":
                            file_estimation += 1
                        case "title"|"sky_title":
                            file_estimation += 1
                        case _:
                            file_estimation += 2
            self.stat_string = "{:,} indexed elements, for ~{:.1f}K files".format(entity_count, file_estimation / 1000).replace(".0K", "K")
        except Exception as e:
            self.tasks.print("An unexpected error occured, can't update stats")
            self.tasks.print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    # load resume file
    def load_resume(self : Updater, name : str) -> None:
        try:
            if not self.use_resume:
                raise Exception()
            with open("resume", mode="r", encoding="utf-8") as f:
                self.resume = json.load(f)
                if name != self.resume['name'] or not isinstance(self.resume, dict):
                    raise Exception()
                self.flags.add("resume_loaded")
        except:
            self.resume = {}

    # save resume file
    def save_resume(self : Updater) -> None:
        try:
            if not self.use_resume:
                return
            if "use_resume" in self.flags:
                with open("resume", mode="w", encoding="utf-8") as f:
                    json.dump(self.resume, f)
                self.tasks.print("The resume file has been updated")
        except:
            pass

    # clear resume file
    def clear_resume(self : Updater) -> None:
        try:
            if not self.use_resume:
                return
            if "resume_loaded" in self.flags:
                with open("resume", mode="r", encoding="utf-8") as f:
                    json.dump({}, f)
        except:
            pass

    # called by TaskManager, check raised flags and start tasks accordingly
    async def process_flags(self : Updater) -> None:
        if "run_process" in self.flags:
            if "found_character" in self.flags and "checking_event" not in self.flags:
                self.flags.add("checking_event")
                self.tasks.print("Adding tasks to check for new events and fate episodes...")
                self.tasks.add(self.check_new_event)
                self.tasks.add(self.update_all_fate, parameters=('last',))
            if "found_event" in self.flags and "checking_event_related" not in self.flags:
                self.flags.add("checking_event_related")
                self.tasks.add(self.maintenance_npc_thumbnail, priority=0)
                self.tasks.add(self.maintenance_raid_appear, priority=0)
                self.tasks.add(self.maintenance_event_skycompass, priority=0)
                self.tasks.add(self.maintenance_compare_wiki_buff, priority=0)

    # return True if the file name passes the  filters
    def file_is_matching(self : Updater, name : str, filters : list[str]) -> bool:
        if len(filters) == 0:
            return True
        f : str
        for f in filters:
            if f in name:
                return True
        return False

    # count file in data container
    def count_file(self : Updater, data : list[Any]) -> Any:
        c : int = 0
        for sub in data:
            if isinstance(sub, list):
                c += len(sub)
        return c

    def load_uncap_queue(self : Updater) -> None:
        if len(self.data['uncap_queue']) > 0:
            for k in self.data['uncap_queue']:
                self.tasks.add(self.update_element, parameters=(k, None))
            self.tasks.print("Note:", len(self.data['uncap_queue']), "element(s) set to be updated, from the Uncap Queue")

    def remove_from_uncap_queue(self : Updater, element_id : str) -> None:
        i : int = 0
        while i < len(self.data['uncap_queue']):
            if self.data['uncap_queue'][i] == element_id:
                self.data['uncap_queue'].pop(i)
            else:
                i += 1

    def import_gbfdaio(self : Updater, path : str) -> None:
        if not path.endswith('index.json'):
            if not path.endswith('/'):
                path += '/'
            path += 'index.json'
        try:
            with open(path, mode="r", encoding="utf-8") as f:
                data : dict[str, Any] = json.load(f)
            i : int
            fi : str
            s : str
            a : int
            b : int
            count : int = 0
            for s in data['classes']:
                if s not in self.data['job']:
                    self.data['job'][s] = 0
                    count += 1
            for i in data['npc']:
                fi = "399{}000".format(str(i).zfill(4))
                if fi not in self.data['npcs']:
                    self.data['npcs'][fi] = 0
                    count += 1
            for a in range(1, 10):
                for b in range(1, 4):
                    k : str = 'enemy'+str(a)+str(b)
                    for i in data[k]:
                        fi = str(a)+str(b)+str(i).zfill(5)
                        if fi not in self.data['enemies']:
                            self.data['enemies'][fi] = 0
                            count += 1
            for e in (('r', '2'), ('sr', '3'), ('ssr', '4')):
                k : str = e[0]+'char'
                if k in data:
                    for i in data[k]:
                        fi = "30"+e[1]+str(i).zfill(4)+"000"
                        if fi not in self.data['characters']:
                            self.data['characters'][fi] = 0
                            count += 1
                k : str = e[0]+'sumn'
                if k in data:
                    for i in data[k]:
                        fi = "20"+e[1]+str(i).zfill(4)+"000"
                        if fi not in self.data['summons']:
                            self.data['summons'][fi] = 0
                            count += 1
            for i in data['skin']:
                fi = "371"+str(i).zfill(4)+"000"
                if fi not in self.data['skins']:
                    self.data['skins'][fi] = 0
                    count += 1
            for b in data:
                if len(b) == 6 and b.startswith('icon'):
                    for i in data[b]:
                        fi = str(i).zfill(4)
                        if fi not in self.data['buffs']:
                            self.data['buffs'][fi] = 0
                            count += 1
            if count > 0:
                print(count, "element(s) imported from GBFDAIO. Use -r/--run to update them")
                self.modified = True
        except Exception as e:
            print("Couldn't import GBFDAIO index.json, verify the path is correct")
            print("Exception:", e)

    async def test_fate(self, k):
        for i in range(0, FATE_LINK):
            for e in self.data["fate"][k][i]:
                s = e + "a"
                if s not in self.data["events"][k][i]:
                    try:
                        await self.head(IMG + "sp/quest/scene/character/body/" + s + ".png")
                        self.tasks.print("fate", k, "found", s)
                        self.data["fate"][k][i].append(s)
                        #self.modified = True
                    except:
                        pass

    ### Entry Point #################################################################################################################

    # To be called before running anything
    async def init_updater(self : Updater, *, wiki : bool = False, job : bool = False) -> None:
        if wiki and not self.use_wiki:
            # test wiki
            self.use_wiki = await self.test_wiki()
            if not self.use_wiki:
                self.tasks.print("WARNING: Use of gbf.wiki is currently impossible")
        if job:
            # update job list
            await self.init_job_list()

    # Start function
    async def start(self : Updater) -> None:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=50)) as self.client:
            self.tasks.print("GBFAL Updater v{}".format(VERSION))
            # set Ctrl+C
            try: # unix
                asyncio.get_event_loop().add_signal_handler(signal.SIGINT, self.tasks.interrupt)
            except: # windows fallback
                signal.signal(signal.SIGINT, self.tasks.interrupt)
            # parse parameters
            prog_name : str
            try: prog_name = sys.argv[0].replace('\\', '/').split('/')[-1]
            except: prog_name = "updater.py" # fallback to default
            # Set Argument Parser
            parser : argparse.ArgumentParser = argparse.ArgumentParser(prog=prog_name, description="Asset Updater v{} for GBFAL https://mizagbf.github.io/GBFAL/".format(VERSION))
            primary = parser.add_argument_group('primary', 'main commands to update the data.')
            primary.add_argument('-r', '--run', help="search for new content.", action='store_const', const=True, default=False, metavar='')
            primary.add_argument('-u', '--update', help="update given elements.", nargs='+', default=None)
            primary.add_argument('-j', '--job', help="detailed job search. Add 'full' to trigger a full search.", action='store', nargs='?', default=False, metavar='FULL')
            primary.add_argument('-jq', '--jobquick', help="search for unused job secondary IDs. Can specify mainhand keys.", action='store', nargs='*', default=False, metavar='FULL')
            
            secondary = parser.add_argument_group('secondary', 'commands to update some specific data.')
            secondary.add_argument('-si', '--sceneid', help="update scene content for given IDs.", nargs='+', default=None)
            secondary.add_argument('-sc', '--scene', help="update scene content. Add optional strings to match.", nargs='*', default=None)
            secondary.add_argument('-sd', '--sound', help="update sound content. Add optional strings to match.", nargs='*', default=None)
            secondary.add_argument('-ev', '--event', help="update event content. Add optional event IDs to update specific events.", nargs='*', default=None)
            secondary.add_argument('-fe', '--forceevent', help="force update event content for given event IDs.", nargs='+', default=None)
            secondary.add_argument('-ne', '--newevent', help="check new event content.", action='store_const', const=True, default=False, metavar='')
            secondary.add_argument('-st', '--story', help="update story content. Add an optional chapter to stop at.", action='store', nargs='?', type=int, default=0, metavar='LIMIT')
            secondary.add_argument('-ft', '--fate', help="update fate content. Add an optional fate ID to update or a range (START-END) or 'last' to update the latest.", action='store', nargs='?', default="", metavar='FATES')
            secondary.add_argument('-pt', '--partner', help="update all parner content. Time consuming.", action='store_const', const=True, default=False, metavar='')
            secondary.add_argument('-mn', '--missingnpc', help="search for missing NPCs. Time consuming.", action='store_const', const=True, default=False, metavar='')
            
            maintenance = parser.add_argument_group('maintenance', 'commands to perform specific maintenance tasks.')
            maintenance.add_argument('-ij', '--importjob', help="import data from job_data_export.json.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-ej', '--exportjob', help="export data to job_data_export.json.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-lk', '--lookup', help="import and update manual_lookup.json and fetch the wiki to update the lookup table.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-fj', '--fatejson', help="import and update manual_fate.json.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-it', '--importthumb', help="import data from manual_event_thumbnail.json.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-et', '--exportthumb', help="export data to manual_event_thumbnail.json.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-mt', '--maintenance', help="run all existing maintenance tasks.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-mb', '--maintenancebuff', help="maintenance task to check existing buffs for new icons.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-ms', '--maintenancesky', help="maintenance task to check sky compass arts for existing events.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-mu', '--maintenancenpcthumbnail', help="maintenance task to check NPC thumbnails for existing NPCs.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-mr', '--maintenanceraidappear', help="maintenance task to check Enemy Raid Appear spritesheets.", action='store_const', const=True, default=False, metavar='')
            maintenance.add_argument('-js', '--json', help="import all manual JSON files.", action='store_const', const=True, default=False, metavar='')
            
            settings = parser.add_argument_group('settings', 'commands to alter the updater behavior.')
            settings.add_argument('-au', '--adduncap', help="add elements to be updated during the next run.", nargs='*', default=None)
            settings.add_argument('-nc', '--nochange', help="disable update of the New category of changelog.json.", action='store_const', const=True, default=False, metavar='')
            settings.add_argument('-nr', '--noresume', help="disable the use of the resume file.", action='store_const', const=True, default=False, metavar='')
            settings.add_argument('-if', '--ignorefilecount', help="ignore known file count when updating elements.", action='store_const', const=True, default=False, metavar='')
            settings.add_argument('-da', '--gbfdaio', help="import index.json from GBFDAIO.", action='store', nargs=1, type=str, metavar='PATH')
            settings.add_argument('-dg', '--debug', help="enable the debug infos in the progress string.", action='store_const', const=True, default=False, metavar='')
            args : argparse.Namespace = parser.parse_args()
            # settings
            run_help : bool = True
            if args.nochange:
                self.update_changelog = False
            if args.noresume:
                self.use_resume = False
            if args.ignorefilecount:
                self.ignore_file_count = True
            if args.adduncap is not None:
                for k in args.adduncap:
                    self.data['uncap_queue'].append(k)
                    self.modified = True
                run_help = False
            if args.debug:
                self.tasks.debug = True
            if args.gbfdaio is not None:
                self.import_gbfdaio(args.gbfdaio[0])
                run_help = False
            # run
            if args.run:
                self.tasks.print("Searching for new elements...")
                await self.init_updater(wiki=True, job=True)
                self.load_uncap_queue()
                await self.run()
            elif args.update is not None and len(args.update) > 0:
                self.tasks.print("Updating", len(args.update)+len(self.data['uncap_queue']), "element(s)...")
                await self.init_updater(wiki=True)
                self.load_uncap_queue()
                await self.update_all(list(set(args.update)))
            elif args.job is not False:
                self.tasks.print("Searching detailed job data...")
                await self.init_updater(wiki=False, job=True)
                await self.search_job_detail(args.job == "full")
            elif args.jobquick is not False:
                self.tasks.print("Searching job secondary ID...")
                await self.init_updater(wiki=False, job=True)
                await self.search_job_second_id(args.jobquick)
            elif args.sceneid is not None and len(args.sceneid) > 0:
                self.tasks.print("Updating scene data...")
                await self.update_all_scene_for_ids(list(set(args.sceneid)))
            elif args.scene is not None:
                self.tasks.print("Updating scene data...")
                await self.update_all_scene(list(set(args.scene)))
            elif args.sound is not None:
                self.tasks.print("Updating sound data...")
                await self.update_all_sound(list(set(args.sound)))
            elif args.event is not None:
                self.tasks.print("Updating event data...")
                await self.init_updater(wiki=True)
                await self.update_all_event(args.event)
            elif args.forceevent is not None and len(args.forceevent) > 0:
                self.tasks.print("Updating event data...")
                await self.init_updater(wiki=True)
                await self.update_all_event(list(set(args.forceevent)), True)
            elif args.newevent:
                self.tasks.print("Searching new event data...")
                await self.init_updater(wiki=True)
                await self.check_new_event()
            elif args.story is None or args.story > 0:
                self.tasks.print("Searching new story data...")
                await self.init_updater(wiki=True)
                await self.update_all_story(args.story)
            elif args.fate is None or args.fate != "":
                self.tasks.print("Searching fate episode data...")
                await self.update_all_fate(args.fate)
            elif args.partner:
                self.tasks.print("Updating all partner data...")
                await self.update_all_partner()
            elif args.missingnpc:
                self.tasks.print("Searching for missing NPC data...")
                await self.search_missing_npc()
            elif args.importjob:
                await self.importjob()
            elif args.exportjob:
                await self.exportjob()
            elif args.lookup:
                await self.init_updater(wiki=True)
                await self.lookup()
            elif args.fatejson:
                self.update_manual_fate()
            elif args.importthumb:
                self.update_manual_event_thumbnail(True)
            elif args.exportthumb:
                self.update_manual_event_thumbnail(False)
            elif args.maintenance:
                await self.init_updater(wiki=True)
                self.tasks.print("Performing maintenance...")
                self.tasks.add(self.maintenance_buff)
                self.tasks.add(self.maintenance_npc_thumbnail)
                self.tasks.add(self.maintenance_raid_appear)
                self.tasks.add(self.maintenance_event_skycompass)
                await self.tasks.start()
            elif args.maintenancebuff:
                await self.init_updater(wiki=True)
                self.tasks.print("Performing maintenance...")
                await self.maintenance_buff()
            elif args.maintenancesky:
                self.tasks.print("Performing maintenance...")
                await self.maintenance_event_skycompass()
            elif args.maintenancenpcthumbnail:
                self.tasks.print("Performing maintenance...")
                await self.maintenance_npc_thumbnail()
            elif args.maintenanceraidappear:
                self.tasks.print("Performing maintenance...")
                await self.maintenance_raid_appear()
            elif args.json:
                await self.lookup()
                self.update_manual_fate()
                self.update_manual_event_thumbnail(True)
            elif run_help:
                parser.print_help()
            # post process
            if len(self.addition) > 0: # we found stuff
                await self.lookup() # update the lookup
                # update other manual json files if needed
                if "found_event" in self.flags:
                    self.update_manual_event_thumbnail(True)
                    self.update_manual_event_thumbnail(False)
                if "found_fate" in self.flags:
                    self.update_manual_fate()
            if self.modified:
                self.make_stats()
                self.save()

if __name__ == "__main__":
    asyncio.run(Updater().start())