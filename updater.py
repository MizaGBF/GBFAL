import asyncio
import aiohttp
import sys
import re
import json
import time
import string
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import traceback
from typing import Optional

# progress bar class
class Progress():
    def __init__(self, *, total : int = 9999999999999, silent : bool = True): # set to silent with a high total by default
        self.silent = silent
        self.total = total
        self.current = -1
        self.start_time = time.time()
        self.update()

    def set(self, *, total : int = 0, silent = False): # to initialize it after a task start, once we know the total
        if total > 0:
            self.total = total
        self.silent = silent
        if not self.silent or self.total <= 0:
            sys.stdout.write("\rProgress: {:.2f}%      ".format(100 * self.current / float(self.total)).replace('.00', ''))
            sys.stdout.flush()

    def update(self): # to call to update the progress text (if not silent and not done)
        if self.current < self.total:
            self.current += 1
            if not self.silent:
                sys.stdout.write("\rProgress: {:.2f}%      ".format(100 * self.current / float(self.total)).replace('.00', ''))
                sys.stdout.flush()
                if self.current >= self.total:
                    diff = time.time() - self.start_time # elapsed time
                    # format to H:M:S
                    x = int((diff - int(diff)) * 100)
                    diff = int(diff)
                    h = diff // 3600
                    m = (diff % 3600) // 60
                    s = diff % 60
                    p = ""
                    if h > 0: p += str(h).zfill(2) + "h"
                    if m > 0 or p != "": p += str(m).zfill(2) + "m"
                    p += str(s).zfill(2)
                    if x > 0: p += "." + str(x).zfill(2)
                    p += "s"
                    print("\nRun time: {}".format(p))

    def __enter__(self): # to use 'WITH'
        pass

    def __exit__(self, type, value, traceback):
        self.update() # updated on exit

# main class
class Updater():
    ### CONSTANT
    # limit
    MAX_NEW = 100
    MAX_UPDATE = 50
    MAX_HTTP = 100
    MAX_HTTP_WIKI = 20
    MAX_SOUND_CONCURRENT = 10
    # addition type
    ADD_UNDEF = -1
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
    PREEMPTIVE_ADD = set(["characters", "enemies", "summons", "skins", "weapons", "partners", "npcs"])
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
    CHARA_SPECIAL_REUSE = {"3710171000":"3710167000","3710170000":"3710167000","3710169000":"3710167000","3710168000":"3710167000"} # bobobo skins reuse bobobo data
    # npc update
    NPC_JOURNAL = 0
    NPC_SCENE = 1
    NPC_SOUND = 2
    # summon update
    SUM_GENERAL = 0
    SUM_CALL = 1
    SUM_DAMAGE = 2
    SUM_MULTI = set(["2040414000"]) # summons with multiple calls
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
    EVENT_MAX_CHAPTER = 15
    EVENT_SKY = EVENT_CHAPTER_START+EVENT_MAX_CHAPTER
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
    ID_REGEX = re.compile("[123][07][1234]0\\d{4}00")
    VERSION_REGEX = re.compile("Game\.version = \"(\d+)\";")
    # others
    SAVE_VERSION = 0
    CUT_CONTENT = ["2040145000","2040147000","2040148000","2040150000","2040152000","2040153000","2040154000","2040200000"] # beta arcarum ids
    SHARED_NAMES = [["2030081000", "2030082000", "2030083000", "2030084000"], ["2030085000", "2030086000", "2030087000", "2030088000"], ["2030089000", "2030090000", "2030091000", "2030092000"], ["2030093000", "2030094000", "2030095000", "2030096000"], ["2030097000", "2030098000", "2030099000", "2030100000"], ["2030101000", "2030102000", "2030103000", "2030104000"], ["2030105000", "2030106000", "2030107000", "2030108000"], ["2030109000", "2030110000", "2030111000", "2030112000"], ["2030113000", "2030114000", "2030115000", "2030116000"], ["2030117000", "2030118000", "2030119000", "2030120000"], ["2040236000", "2040313000", "2040145000"], ["2040237000", "2040314000", "2040146000"], ["2040238000", "2040315000", "2040147000"], ["2040239000", "2040316000", "2040148000"], ["2040240000", "2040317000", "2040149000"], ["2040241000", "2040318000", "2040150000"], ["2040242000", "2040319000", "2040151000"], ["2040243000", "2040320000", "2040152000"], ["2040244000", "2040321000", "2040153000"], ["2040245000", "2040322000", "2040154000"], ["1040019500", '1040008000', '1040008100', '1040008200', '1040008300', '1040008400'], ["1040112400", '1040107300', '1040107400', '1040107500', '1040107600', '1040107700'], ["1040213500", '1040206000', '1040206100', '1040206200', '1040206300', '1040206400'], ["1040311500", '1040304900', '1040305000', '1040305100', '1040305200', '1040305300'], ["1040416400", '1040407600', '1040407700', '1040407800', '1040407900', '1040408000'], ["1040511800", '1040505100', '1040505200', '1040505300', '1040505400', '1040505500'], ["1040612300", '1040605000', '1040605100', '1040605200', '1040605300', '1040605400'], ["1040709500", '1040704300', '1040704400', '1040704500', '1040704600', '1040704700'], ["1040811500", '1040804400', '1040804500', '1040804600', '1040804700', '1040804800'], ["1040911800", '1040905000', '1040905100', '1040905200', '1040905300', '1040905400'], ["2040306000","2040200000"]]
    SPECIAL_LOOKUP = { # special elements
        "3020065000": "r character brown poppet trial",
        "3030158000": "sr character blue poppet trial",
        "3040097000": "ssr character sierokarte trial",
        "2030004000": "sr summon fire not-playable",
        "2030014000": "sr summon dark not-playable",
    }
    
    def __init__(self):
        # main variables
        self.update_changelog = True # flag to enable or disable the generation of changelog.json
        self.debug_wpn = False # for testing
        self.data = { # data structure
            "version":self.SAVE_VERSION,
            "characters":{},
            "partners":{},
            "summons":{},
            "weapons":{},
            "enemies":{},
            "skins":{},
            "job":{},
            "job_wpn":{},
            "job_key":{},
            "npcs":{},
            "background":{},
            "title":{},
            "suptix":{},
            "lookup":{},
            "events":{},
            "skills":{},
            "subskills":{},
            "buffs":{},
            "relations":{},
            "eventthumb":{}
        }
        self.load() # load self.data NOW
        self.modified = False # if set to true, data.json will be written on the next call of save()
        self.new_elements = [] # new indexed element
        self.addition = {} # new elements for changelog.json
        self.job_list = None
        self.name_table = {} # relation table
        self.name_table_modified = False # and its modified flag
        
        # asyncio semaphores
        self.sem = asyncio.Semaphore(self.MAX_UPDATE) # update semaphore
        self.http_sem = asyncio.Semaphore(self.MAX_HTTP) # http semaphore
        self.wiki_sem = asyncio.Semaphore(self.MAX_HTTP_WIKI) # wiki request semaphor
        
        # others
        self.scene_strings, self.scene_special_strings, self.scene_special_suffix = self.build_scene_strings()
        self.progress = Progress() # initialized with a silent progress bar
        
        self.client = None # will contain the aiohttp client. Is initialized at startup or must be initialized by a third party.

    ### Utility #################################################################################################################

    # Load data.json
    def load(self):
        try:
            with open('json/data.json', mode='r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict): return
            data = self.retrocompatibility(data)
            for k in self.data:
                if k == 'version': continue
                self.data[k] = data.get(k, {})
        except Exception as e:
            print(e)

    # make older data.json compatible with newer versions
    def retrocompatibility(self, data):
        #version = data.get("version", 0)
        # Does nothing for now
        return data

    # Save data.json and changelog.json (only if self.modified is True)
    def save(self):
        try:
            if self.modified:
                self.modified = False
                with open('json/data.json', mode='w', encoding='utf-8') as outfile:
                    # custom json indentation
                    outfile.write("{\n")
                    keys = list(self.data.keys())
                    for k, v in self.data.items():
                        outfile.write('"{}":\n'.format(k))
                        if isinstance(v, int): # INT
                            outfile.write('{}\n'.format(v))
                            if k != keys[-1]:
                                outfile.write(",")
                            outfile.write("\n")
                        elif isinstance(v, list): # LIST
                            outfile.write('[\n')
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
                            last = list(v.keys())
                            if len(last) > 0:
                                last = last[-1]
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
                print("data.json updated")
                if self.update_changelog:
                    try:
                        with open('json/changelog.json', mode='r', encoding='utf-8') as f:
                            data = json.load(f)
                            issues = data.get('issues', [])
                            existing = {}
                            for e in data.get('new', []): # convert content to dict
                                existing[e[0]] = e[1]
                    except:
                        existing = {}
                        issues = []
                    new = []
                    for k, v in self.addition.items(): # merge but put updated elements last
                        if k in existing: existing.pop(k)
                        existing[k] = v
                    self.addition = {} # clear self.addition
                    for k, v in existing.items(): # convert back to list. NOTE: maybe make a cleaner way later
                        new.append([k, v])
                    if len(new) > self.MAX_NEW: new = new[len(new)-self.MAX_NEW:]
                    with open('json/changelog.json', mode='w', encoding='utf-8') as outfile:
                        json.dump({'timestamp':int(datetime.now(timezone.utc).timestamp()*1000), 'new':new, 'issues':issues}, outfile)
                    print("changelog.json updated")
        except Exception as e:
            print(e)
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    # Generic GET request function
    async def get(self, url : str, headers : dict = {}):
        async with self.http_sem:
            response = await self.client.get(url, headers={'connection':'keep-alive'} | headers, timeout=50)
            async with response:
                if response.status != 200: raise Exception("HTTP error {}".format(response.status_code))
                return await response.content.read()
    
    # Generic HEAD request function
    async def head(self, url : str, headers : dict = {}):
        async with self.http_sem:
            response = await self.client.head(url, headers={'connection':'keep-alive'} | headers, timeout=50)
            async with response:
                if response.status != 200: raise Exception("HTTP error {}".format(response.status_code))
                return response.headers

    # wrapper of head() if the exception isn't needed (return None in case of error instead)
    async def head_nx(self, url : str, headers : dict = {}):
        try:
            return await self.head(url, headers)
        except:
            return None

    # another wrapper to chain requests
    async def multi_head_nx(self, urls : list, headers : dict = {}):
        for url in urls:
            r = await self.head_nx(url, headers)
            if r is not None:
                return r
        return None

    # Create a shared container for tasks.
    def newShared(self, errs : list):
        errs.append([0, True, 0])
        return errs[-1]

    # Extract json data from a manifest file
    async def processManifest(self, file : str, verify_file : bool = False):
        manifest = (await self.get(self.MANIFEST + file + ".js")).decode('utf-8')
        st = manifest.find('manifest:') + len('manifest:')
        ed = manifest.find(']', st) + 1
        data = json.loads(manifest[st:ed].replace('Game.imgUri+', '').replace('src:', '"src":').replace('type:', '"type":').replace('id:', '"id":'))
        res = []
        for l in data:
            src = l['src'].split('?')[0].split('/')[-1]
            res.append(src)
        if verify_file: # check if at least one file is visible
            for k in res:
                try:
                    await self.head(self.IMG + "sp/cjs/" + k)
                    return res
                except:
                    pass
            raise Exception("Invalid Spritesheets")
        return res

    # Remove extra from wiki name
    def cleanName(self, name : str):
        for k in ['(Grand)', '(Yukata)', '(Summer)', '(Valentine)', '(Holiday)', '(Halloween)', '(SSR)', '(Fire)', '(Water)', '(Earth)', '(Wind)', '(Light)', '(Dark)', '(Grand)', '(Event SSR)', '(Event)', '(Promo)']:
            name = name.replace(k, '')
        return name.strip().strip('_')

    # for limited queued asyncio concurrency
    def map_unordered(self, func, iterable, limit):
        aws = map(func, iterable)
        return self.limit_concurrency(aws, limit)

    async def limit_concurrency(self, aws, limit):
        try:
            aws = aiter(aws)
            is_async = True
        except TypeError:
            aws = iter(aws)
            is_async = False

        aws_ended = False
        pending = set()

        while pending or not aws_ended:
            while len(pending) < limit and not aws_ended:
                try:
                    aw = await anext(aws) if is_async else next(aws)
                except StopAsyncIteration if is_async else StopIteration:
                    aws_ended = True
                else:
                    pending.add(asyncio.ensure_future(aw))

            if not pending:
                return

            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            while done:
                yield done.pop()

    ### Run #####################################################################################################################
    
    # Called by -run, update the indexed content
    async def run(self):
        tasks = []
        errs = []
        job_task = 10
        skill_task = 10
        buff_series_task = 10
        # job keys to check
        jkeys = []
        if self.job_list is None:
            self.job_list = await self.init_job_list()
        for k in list(self.job_list.keys()):
            if k not in self.data['job']:
                jkeys.append(k)
        if len(jkeys) > 0:
            job_task == 0

        print("Starting process...")
        async with asyncio.TaskGroup() as tg:
            self.progress = Progress()
            self.newShared(errs)
            for i in range(job_task):
                tasks.append(tg.create_task(self.search_job(i, job_task, jkeys, errs[-1])))
            # skills
            for i in range(skill_task):
                tasks.append(tg.create_task(self.search_skill(i, skill_task)))
            # buffs
            for i in range(10):
                for j in range(buff_series_task):
                    tasks.append(tg.create_task(self.search_buff(1000*i+j, buff_series_task)))
            # npc
            self.newShared(errs)
            for i in range(10): # assets
                tasks.append(tg.create_task(self.run_sub('npcs', i, 10, errs[-1], "399{}000", 4, "img_low/sp/quest/scene/character/body/", ".png",  60)))
            self.newShared(errs)
            for i in range(10): # assets
                tasks.append(tg.create_task(self.run_sub('npcs', i, 10, errs[-1], "399{}000", 4, "img_low/sp/assets/npc/b/", "_01.png",  60)))
            self.newShared(errs)
            for i in range(10): # sounds
                tasks.append(tg.create_task(self.run_sub('npcs', i, 10, errs[-1], "399{}000", 4, "sound/voice/", "_v_001.mp3",  60)))
            # special
            tasks.append(tg.create_task(self.run_sub('npcs', 0, 1, self.newShared(errs), "305{}000", 4, "img_low/sp/quest/scene/character/body/", ".png",  2)))
            #rarity of various stuff
            for r in range(1, 5):
                # weapons
                for j in range(10):
                    self.newShared(errs)
                    for i in range(5):
                        tasks.append(tg.create_task(self.run_sub('weapons', i, 5, errs[-1], "10"+str(r)+"0{}".format(j) + "{}00", 3, "img_low/sp/assets/weapon/m/", ".jpg",  20)))
                # summons
                self.newShared(errs)
                for i in range(5):
                    tasks.append(tg.create_task(self.run_sub('summons', i, 5, errs[-1], "20"+str(r)+"0{}000", 3, "js/model/manifest/summon_", "_01_damage.js",  20)))
                if r > 1:
                    # characters
                    self.newShared(errs)
                    for i in range(5):
                        tasks.append(tg.create_task(self.run_sub('characters', i, 5, errs[-1], "30"+str(r)+"0{}000", 3, "img_low/sp/assets/npc/m/", "_01.jpg", 20)))
                    # partners
                    self.newShared(errs)
                    for i in range(5):
                        tasks.append(tg.create_task(self.run_sub('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "img_low/sp/assets/npc/raid_normal/", "_01.jpg",  20)))
                    self.newShared(errs)
                    for i in range(5):
                        tasks.append(tg.create_task(self.run_sub('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/phit_", ".js",  20)))
                    self.newShared(errs)
                    for i in range(5):
                        tasks.append(tg.create_task(self.run_sub('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/nsp_", "_01.js",  20)))
            # other partners
            for r in range(8, 10):
                self.newShared(errs)
                for i in range(5):
                    tasks.append(tg.create_task(self.run_sub('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "img_low/sp/assets/npc/raid_normal/", "_01.jpg",  20)))
                self.newShared(errs)
                for i in range(5):
                    tasks.append(tg.create_task(self.run_sub('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/phit_", ".js",  20)))
                self.newShared(errs)
                for i in range(5):
                    tasks.append(tg.create_task(self.run_sub('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/nsp_", "_01.js",  20)))
            # skins
            self.newShared(errs)
            for i in range(5):
                tasks.append(tg.create_task(self.run_sub('skins', i, 5, errs[-1], "3710{}000", 3, "js/model/manifest/npc_", "_01js",  20)))
            # enemies
            for a in range(1, 10):
                for b in range(1, 4):
                    for d in [1, 2, 3]:
                        self.newShared(errs)
                        for i in range(5):
                            tasks.append(tg.create_task(self.run_sub('enemies', i, 5, errs[-1], str(a) + str(b) + "{}" + str(d), 4, "img/sp/assets/enemy/s/", ".png",  50)))
            # backgrounds
            for i in ["event_{}", "common_{}", "main_{}"]:
                self.newShared(errs)
                for j in range(5):
                    tasks.append(tg.create_task(self.run_sub('background', j, 5, errs[-1], i, 1, "img_low/sp/raid/bg/", ".jpg",  10)))
            for i in ["ra", "rb", "rc"]:
                self.newShared(errs)
                for j in range(5):
                    tasks.append(tg.create_task(self.run_sub('background', j, 5, errs[-1], "{}"+i, 1, "img_low/sp/raid/bg/", "_1.jpg",  50)))
            for i in [("e", ""), ("e", "r"), ("f", ""), ("f", "r"), ("f", "ra"), ("f", "rb"), ("f", "rc"), ("e", "r_3_a"), ("e", "r_4_a")]:
                self.newShared(errs)
                for j in range(5):
                    tasks.append(tg.create_task(self.run_sub('background', j, 5, errs[-1], i[0]+"{}"+i[1], 3, "img_low/sp/raid/bg/", "_1.jpg",  50)))
            # titles
            self.newShared(errs)
            for i in range(3):
                tasks.append(tg.create_task(self.run_sub('title', i, 3, errs[-1], "{}", 1, "img_low/sp/top/bg/bg_", ".jpg",  5)))
            # subskills
            self.newShared(errs)
            for i in range(3):
                tasks.append(tg.create_task(self.run_sub('subskills', i, 3, errs[-1], "{}", 1, "img_low/sp/assets/item/ability/s/", "_1.jpg",  5)))
            # suptix
            self.newShared(errs)
            for i in range(3):
                tasks.append(tg.create_task(self.run_sub('suptix', i, 3, errs[-1], "{}", 1, "img_low/sp/gacha/campaign/surprise/top_", ".jpg",  15)))
            self.progress.set(total=len(tasks), silent=False)
        if len(self.new_elements) > 0:
            await self.manualUpdate(self.new_elements)
            await self.check_new_event()
            await self.update_npc_thumb()
        await self.build_relation()
        self.save()

    # standard run subroutine
    async def run_sub(self, index : str, start : int, step : int, err : list, file : str, zfill : int, path : str, ext : str, maxerr : int):
        with self.progress:
            i = start
            is_js = ext.endswith('.js')
            while err[0] < maxerr and err[1]:
                f = file.format(str(i).zfill(zfill))
                if f in self.data[index]:
                    if self.data[index][f] == 0 and (is_js or index in self.PREEMPTIVE_ADD):
                        self.new_elements.append(f)
                    err[0] = 0
                    await asyncio.sleep(0.001)
                else:
                    try:
                        if f in self.SUM_MULTI: await self.head(self.endpoint + path + f + ext.replace("_damage", "_a_damage"))
                        else: await self.head(self.endpoint + path + f + ext)
                        err[0] = 0
                        self.data[index][f] = 0
                        if index in ["background", "title", "subskills", "suptix"]:
                            self.addition[index+":"+f] = self.ADD_UNDEF
                        self.modified = True
                        self.new_elements.append(f)
                    except:
                        err[0] += 1
                        if err[0] >= maxerr:
                            err[1] = False
                            return
                i += step

    # -run subroutine to search for new skills
    async def search_skill(self, start : int, step : int): # skill search
        with self.progress:
            err = 0
            i = start
            tmp = []
            tmp_c = ("0" if start < 1000 else str(start)[0])
            for k in list(self.data["skills"].keys()):
                if k[0] == tmp_c:
                    tmp.append(k)
            tmp.sort()
            try:
                highest = int(tmp[-1])
            except:
                highest = i - 1
            tmp = None
            highest = start
            while err < 12:
                fi = str(i).zfill(4)
                if fi in self.data["skills"]:
                    i += step
                    err = 0
                    continue
                found = False
                for s in [".png", "_1.png", "_2.png", "_3.png", "_4.png", "_5.png"]:
                    try:
                        headers = await self.head(self.IMG + "sp/ui/icon/ability/m/" + str(i) + s)
                        if 'content-length' in headers and int(headers['content-length']) < 200: raise Exception()
                        found = True
                        err = 0
                        self.data["skills"][fi] = [[str(i) + s.split('.')[0]]]
                        self.addition[fi] = self.ADD_SKILL
                        self.modified = True
                        break
                    except:
                        pass
                i += step
                if not found and i > highest: err += 1

    # -run subroutine to search for new buffs
    async def search_buff(self, start : int, step : int, full : bool = False): # buff search
        with self.progress:
            err = 0
            i = start
            end = (start // 1000) * 1000 + 1000
            tmp = []
            tmp_c = ("0" if start < 1000 else str(start)[0])
            for k in list(self.data["buffs"].keys()):
                if k[0] == tmp_c:
                    tmp.append(k)
            tmp.sort()
            try:
                highest = int(tmp[-1])
            except:
                highest = i - 1
            tmp = None
            highest = start
            slist = ["", "_1", "_10"] + (["1"] if start >= 1000 else []) + ["_30", "_1_1", "_1_10"]
            known = set()
            while err < 10 and i < end:
                fi = str(i).zfill(4)
                if not full:
                    if fi in self.data["buffs"]:
                        i += step
                        err = 0
                        continue
                    data = [[], []]
                else:
                    try:
                        data = self.data["buffs"][fi]
                        known = set(data[1])
                        if '_' not in data[0] and len(data[0]) < 5:
                            known.add("")
                    except:
                        data = [[], []]
                        known = set()
                found = False
                modified = False
                for s in slist:
                    try:
                        if s not in known:
                            headers = await self.head(self.IMG + "sp/ui/icon/status/x64/status_" + str(i) + s + ".png")
                            if 'content-length' in headers and int(headers['content-length']) < 150: raise Exception()
                            if len(data[0]) == 0:
                                data[0].append(str(i) + s)
                            if s != "":
                                data[1].append(s)
                            modified = True
                        found = True
                    except:
                        if s == "1" and not found:
                            break
                if not found:
                    if i > highest:
                        err += 1
                else:
                    err = 0
                    if modified:
                        self.data["buffs"][fi] = data
                        self.addition[fi] = self.ADD_BUFF
                        self.modified = True
                i += step

    ### Job #####################################################################################################################
    
    # To be called once when needed
    async def init_job_list(self):
        print("Initializing job list...")
        # existing classes
        try: job_list = (await self.get(self.JS + "constant/job.js")).decode('utf-8') # contain a list of all classes. it misses the id of the outfits however.
        except Exception as ee:
            print(ee)
            return
        a = job_list.find("var a={")
        if a == -1: return
        a+=len("var a={")
        b = job_list.find("};", a)
        if b == -b: return
        job_list = job_list[a:b].split(',')
        temp = {}
        for j in job_list:
            e = j.split(':')
            temp[e[1]] = set()
            for c in e[0].replace('_', ''):
                temp[e[1]].add(c)
            temp[e[1]] = "".join(list(temp[e[1]])).lower()
        job_list = temp
        # old skins
        for e in [("125001","snt"), ("165001","stf"), ("185001", "idl")]:
            job_list[e[0]] = e[1]
        # new skins
        async with asyncio.TaskGroup() as tg:
            tasks = []
            for i in range(31, 41):
                for j in range(0, 20):
                    if str(i * 100 + j)+"01" in job_list: continue
                    tasks.append(tg.create_task(self.init_job_list_sub(str(i * 100 + j)+"01")))
        for t in tasks:
            r = t.result()
            if r is not None:
                job_list[r] = string.ascii_lowercase
        print("Done")
        return job_list

    # Subroutine for init_job_list
    async def init_job_list_sub(self, id : str):
        try:
            await self.head(self.IMG + "sp/assets/leader/m/{}_01.jpg".format(id))
            return id
        except:
            return None

    # run subroutine to search for new jobs
    async def search_job(self, start : int, step : int, keys : list, shared : list):
        with self.progress:
            i = start
            while i < len(keys):
                if keys[i] in self.data['job']: continue
                cmh = []
                colors = [1]
                alts = []
                # mh check
                for mh in self.MAINHAND:
                    try:
                        await self.head(self.IMG + "sp/assets/leader/raid_normal/{}_{}_0_01.jpg".format(keys[i], mh))
                        cmh.append(mh)
                    except:
                        continue
                if len(cmh) > 0:
                    # alt check
                    for j in [2, 3, 4, 5, 80]:
                        try:
                            await self.head(self.IMG + "sp/assets/leader/sd/{}_{}_0_01.png".format(keys[i][:-2]+str(j).zfill(2), cmh[0]))
                            colors.append(j)
                            if j >= 80:
                                alts.append(j)
                        except:
                            continue
                    # set data
                    data = [[keys[i]], [keys[i]+"_01"], [], [], [], [], cmh, [], [], []] # main id, alt id, detailed id (main), detailed id (alt), detailed id (all), sd, mainhand, sprites, phit, sp
                    for j in alts:
                        data[1].append(keys[i][:-2]+str(j).zfill(2)+"_01")
                    for k in range(2):
                        data[2].append(keys[i]+"_"+cmh[0]+"_"+str(k)+"_01")
                    for j in [1]+alts:
                        for k in range(2):
                            data[3].append(keys[i][:-2]+str(j).zfill(2)+"_"+cmh[0]+"_"+str(k)+"_01")
                    for j in colors:
                        for k in range(2):
                            data[4].append(keys[i][:-2]+str(j).zfill(2)+"_"+cmh[0]+"_"+str(k)+"_01")
                    for j in colors:
                        data[5].append(keys[i][:-2]+str(j).zfill(2))

                    self.data['job'][keys[i]] = data
                    self.modified = True
                    self.addition[keys[i]] = self.ADD_JOB
                i += step
            if shared[1]:
                shared[1] = False

    # Used by -job, more specific but also slower job detection system
    async def search_job_detail(self):
        if self.job_list is None:
            self.job_list = await self.init_job_list()
        print("Searching additional job data...")
        to_search = []
        full_key_search = False
        # key search
        for k, v in self.data['job'].items():
            if len(v[7]) == 0:
                if self.job_list[k] != string.ascii_lowercase:
                    to_search.append((0, self.job_list[k], k)) # keyword search type, letters, class id
                else:
                    full_key_search = True
        # class weapon search
        for i in range(0, 999):
            err = 0
            for j in range(10):
                wid = "1040{}{}00".format(j, i)
                if wid in self.data['weapons'] or wid in self.data["job_wpn"]:
                    err = 0
                    continue
                to_search.append((1, wid)) # skin weapon search, id
                err += 1
                if err > 15: break
        async with asyncio.TaskGroup() as tg:
            tasks = []
            for v in to_search:
                if v[0] == 0:
                    tasks.append(tg.create_task(self.detail_job_search(v[1], v[2])))
                elif v[0] == 1:
                    tasks.append(tg.create_task(self.detail_job_weapon_search(v[1])))
            # full key search
            if full_key_search:
                await asyncio.sleep(5) # delay to give time to detail_job_search
                for a in string.ascii_lowercase:
                    for b in string.ascii_lowercase:
                        for c in string.ascii_lowercase:
                            d = a+b+c
                            if d in self.data["job_key"]: continue
                            tasks.append(tg.create_task(self.detail_job_search_single(d)))
                            await asyncio.sleep(0.005) # delay to give time to detail_job_search
        for t in tasks:
            t.result()
        print("Done")
        self.save()

    # search_job_detail() subroutine
    async def detail_job_search(self, key : str, job : str):
        cmh = self.data['job'][job][6]
        a = key[0]
        for b in key:
            for c in key:
                d = a+b+c
                if d in self.data["job_key"] and self.data["job_key"][d] is not None: continue
                passed = True
                for mh in cmh:
                    try:
                        await self.processManifest("{}_{}_0_01".format(d, mh))
                    except:
                        passed = False
                        break
                if passed:
                    self.data["job_key"][d] = job
                    self.modified = True
                    print("Set", job, "to", d)

    # search_job_detail() subroutine
    async def detail_job_weapon_search(self, wid : str):
        try:
            await self.head(self.IMG + '_low/sp/assets/weapon/m/' + wid + ".jpg")
            return
        except:
            pass
        for k in [["phit_", ""], ["sp_", "_1_s2"]]:
            try:
                await self.head(self.MANIFEST + k[0] + wid + k[1] + ".js")
                self.data["job_wpn"][wid] = None
                self.modified = True
                print("Possible job skin related weapon:", wid)
                break
            except:
                pass

    # search_job_detail() subroutine
    async def detail_job_search_single(self, key : str):
        for mh in self.MAINHAND:
            try:
                await self.processManifest("{}_{}_0_01".format(key, mh))
                self.data["job_key"][key] = None
                self.modified = True
                print("Unknown job key", key, "for mh", mh)
                break
            except:
                pass

    # -jobedit CLI
    async def edit_job(self):
        while True:
            print("")
            print("[EDIT JOB MENU]")
            print("[0] Set job data")
            print("[1] List Unset Job Weapons")
            print("[2] List Unset Job Keys")
            print("[3] List Uncomplete Job")
            print("[4] Export Data")
            print("[5] Import Data")
            print("[Any] Exit")
            match input():
                case "0":
                    while True:
                        s = input("Input job ID (leave blank to cancel):")
                        if s == "":
                            break
                        elif s not in self.data['job']:
                            print("Unknown ID")
                        else:
                            jid = s
                            for k, v in self.data['job_wpn'].items():
                                if v == jid:
                                    print(jid,"is set to weapon",k)
                            for k, v in self.data['job_key'].items():
                                if v == jid:
                                    print(jid,"is set to key",k)
                            while True:
                                print("Input a valid weapon ID or a job key to set to this class (leave blank to cancel)")
                                s = input().lower()
                                if s in self.data['job_key']:
                                    sheets = []
                                    for v in self.data['job'][jid][4]:
                                        try:
                                            sheets += await self.processManifest(s + "_" + '_'.join(v.split('_')[1:3]) + "_" + v.split('_')[0][-2:])
                                        except:
                                            pass
                                    self.data['job'][jid][7] = list(dict.fromkeys(sheets))
                                    self.data['job_key'][s] = jid
                                    self.modified = True
                                    print(len(sheets),"sprites set to job", jid)
                                elif s in self.data['job_wpn']:
                                    # phit
                                    try:
                                        self.data['job'][jid][8] = list(dict.fromkeys(await self.processManifest("phit_{}".format(s))))
                                    except:
                                        pass
                                    # ougi
                                    sheets = []
                                    for u in ["", "_0", "_1", "_0_s2", "_1_s2", "_0_s3", "_1_s3"]:
                                        try:
                                            sheets += await self.processManifest("sp_{}{}".format(s, u))
                                        except:
                                            pass
                                    self.data['job'][jid][9] = list(dict.fromkeys(sheets))
                                    print(len(self.data['job'][jid][8]),"attack sprites and",len(self.data['job'][jid][9]),"ougi sprites set to job", jid)
                                    self.data['job_wpn'][s] = jid
                                    self.modified = True
                                elif s == "":
                                    break
                                else:
                                    print("Unknown element", s)
                case "1":
                    tmp = []
                    for k, v in self.data['job_wpn'].items():
                        if v is None: tmp.append(k)
                    if len(tmp) == 0:
                        print("No unset weapon in memory")
                    else:
                        print("\n".join(tmp))
                case "2":
                    tmp = []
                    for k, v in self.data['job_key'].items():
                        if v is None: tmp.append(k)
                    if len(tmp) == 0:
                        print("No free key in memory")
                    else:
                        print("\n".join(tmp))
                case "3":
                    tmp = 0
                    for k, v in self.data['job'].items():
                        if len(v[7]) == 0:
                            print(k, "has no sprites")
                            tmp += 1
                        elif len(v[8]) + len(v[9]) == 0 and 4100 > int(k[:4]) > 3100:
                            print(k, "might be an uncomplete skin")
                            tmp += 1
                        if v is None: tmp.append(k)
                    if tmp == 0:
                        print("Everything seems complete")
                case "4":
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
                        print("Data exported to json/job_data_export.json")
                case "5":
                    try:
                        with open("json/job_data_export.json", mode="r", encoding="ascii") as f:
                            tmp = json.load(f)
                            if 'lookup' not in tmp or 'weapon' not in tmp:
                                raise Exception()
                    except:
                        print("Couldn't find, open or load json/job_data_export.json")
                        tmp = None
                    if tmp is not None and input("Are you sure? Press 'y' to continue:").lower() == 'y':
                        print("Importing data...")
                        try:
                            for jid, s in tmp["lookup"].items():
                                # add job if needed
                                if jid not in self.data['job']:
                                    self.search_job(0, 1, [jid], self.newShared([]))
                                if s is not None:
                                    # set key
                                    sheets = []
                                    for v in self.data['job'][jid][4]:
                                        try:
                                            sheets += await self.processManifest(s + "_" + '_'.join(v.split('_')[1:3]) + "_" + v.split('_')[0][-2:])
                                        except:
                                            pass
                                    self.data['job'][jid][7] = list(dict.fromkeys(sheets))
                                    self.data['job_key'][s] = jid
                                    self.modified = True
                                    print(len(sheets),"sprites set to job", jid)
                            for jid, s in tmp["weapon"].items():
                                if s is not None:
                                    # phit
                                    self.data['job'][jid][8] = []
                                    for u in ["", "_2", "_3"]:
                                        try:
                                            self.data['job'][jid][8] += list(dict.fromkeys(await self.processManifest("phit_{}{}".format(s, u))))
                                        except:
                                            pass
                                    # ougi
                                    sheets = []
                                    for u in ["", "_0", "_1", "_0_s2", "_1_s2", "_0_s3", "_1_s3"]:
                                        try:
                                            sheets += await self.processManifest("sp_{}{}".format(s, u))
                                        except:
                                            pass
                                    self.data['job'][jid][9] = list(dict.fromkeys(sheets))
                                    print(len(self.data['job'][jid][8]),"attack sprites and",len(self.data['job'][jid][9]),"ougi sprites set to job", jid)
                                    self.data['job_wpn'][s] = jid
                                    self.modified = True
                            print("Job Data Import finished with success")
                        except Exception as e:
                            print("An error occured while processing ({}, {}), exiting to preserve data...".format(jid, s))
                            print(e)
                            exit(0)
                case _:
                    break
        self.save()

    ### Update ##################################################################################################################

    # Called by -update or other function when new content is detected
    async def manualUpdate(self, ids : list): 
        if len(ids) == 0:
            return
        ids = list(set(ids)) # remove dupes
        async with asyncio.TaskGroup() as tg:
            tasks = []
            remaining = 0
            self.progress = Progress()
            for id in ids:
                if len(id) >= 10:
                    if id.startswith('2'):
                        tasks.append(tg.create_task(self.sumUpdate(id)))
                    elif id.startswith('10'):
                        tasks.append(tg.create_task(self.weapUpdate(id)))
                    elif id.startswith('39') or id.startswith('305'):
                        tasks.append(tg.create_task(self.npcUpdate(id)))
                    elif id.startswith('38'):
                        try:
                            pid = int(id)
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid), 10))) # separate in multiple threads to speed up
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid+1), 10)))
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid+2), 10)))
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid+3), 10)))
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid+4), 10)))
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid+5), 10)))
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid+6), 10)))
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid+7), 10)))
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid+8), 10)))
                            tasks.append(tg.create_task(self.partnerUpdate(str(pid+9), 10)))
                        except:
                            continue
                    elif id.startswith('3'):
                        tasks.append(tg.create_task(self.charaUpdate(id)))
                    else:
                        continue
                    remaining += 1
                elif len(id) >= 6:
                    tasks.append(tg.create_task(self.mobUpdate(id)))
                    remaining += 1
            print("Attempting to update", remaining, "element(s)")
            self.progress.set(total=len(tasks), silent=False)
        tsuccess = 0
        for t in tasks:
            if t.result():
                tsuccess += 1
        print(tsuccess, "positive result(s)")
        if tsuccess > 0:
            self.sort_all_scene()
        self.save()

    # Art check system for characters. Detect gendered arts, etc...
    async def artCheck(self, id : str, style : str, uncaps : list):
        tasks = {}
        if id.startswith("38"):
            uncaps = ["01", "02", "03", "04"]
        else:
            uncaps = uncaps + ["81", "82", "83", "91", "92", "93"]
        async with asyncio.TaskGroup() as tg:
            for uncap in uncaps:
                for g in ["_1", ""]:
                    for m in ["_101", ""]:
                        for n in ["_01", ""]:
                            s = "_" + uncap + style + g + m + n
                            tasks[(uncap, g, m, n)] = tg.create_task(self.head_nx(self.IMG + "sp/assets/npc/raid_normal/{}{}.jpg".format(id, s)))
        flags = {}
        for s, t in tasks.items():
            if t.result() is not None:
                uncap, g, m, n = s
                if uncap not in flags:
                    flags[uncap] = [False, False, False]
                flags[uncap][0] = flags[uncap][0] or (g == "_1")
                flags[uncap][1] = flags[uncap][1] or (m == "_101")
                flags[uncap][2] = flags[uncap][2] or (n == "_01")
        return flags

    # Update character and skin data
    async def charaUpdate(self, id : str):
        with self.progress:
            async with self.sem:
                index = "skins" if id.startswith("371") else "characters"
                data = [[], [], [], [], [], [], [], [], []] # sprite, phit, sp, aoe, single, general, sd, scene, sound
                for style in ["", "_st2"]:
                    uncaps = []
                    sheets = []
                    altForm = False
                    if index == "skins" and style != "": # skin & style check
                        break
                    # # # Main sheets
                    tid = self.CHARA_SPECIAL_REUSE.get(id, id) # special substitution (mostly for bobobo)
                    for uncap in ["01", "02", "03", "04"]:
                        for ftype in ["", "_s2"]:
                            for form in ["", "_f", "_f1", "_f_01"]:
                                try:
                                    fn = "npc_{}_{}{}{}{}".format(tid, uncap, style, form, ftype)
                                    sheets += await self.processManifest(fn)
                                    if form == "": uncaps.append(uncap)
                                    else: altForm = True
                                except:
                                    if form == "":
                                        break
                    data[self.CHARA_SPRITE] += sheets
                    if len(uncaps) == 0:
                        if style == "": return False
                        continue
                    # # # Assets
                    # arts
                    flags = await self.artCheck(id, style, uncaps)
                    targets = []
                    sd = []
                    for uncap in flags:
                        # main
                        base_fn = "{}_{}{}".format(id, uncap, style)
                        uf = flags[uncap]
                        for g in (["", "_0", "_1"] if (uf[0] is True) else [""]):
                            for m in (["", "_101", "_102", "_103", "_104", "_105"] if (uf[1] is True) else [""]):
                                for n in (["", "_01", "_02", "_03", "_04", "_05", "_06"] if (uf[2] is True) else [""]):
                                    for af in (["", "_f", "_f1"] if altForm else [""]):
                                        targets.append(base_fn + af + g + m + n)
                        # sprites
                        sd.append(base_fn)
                    flags = None
                    data[self.CHARA_GENERAL] += targets
                    data[self.CHARA_SD] += sd
                    if len(targets) == 0:
                        if style == "": return False
                        continue
                    tasks = {'scenes':{}, 'sound':None}
                    async with asyncio.TaskGroup() as tg:
                        if style == "":
                            # scene
                            try: scenes = set(self.data[index][id][self.CHARA_SCENE])
                            except: scenes = set()
                            data[self.CHARA_SCENE] = scenes
                            self.group_scene_task(tg, tasks, id, uncaps, scenes)
                            # sound
                            try: voices = set(self.data[index][id][self.CHARA_SOUND])
                            except: voices = set()
                            tasks['sound'] = tg.create_task(self.update_chara_sound_file(id, uncaps, voices))
                        # # # Other sheets
                        # attack
                        targets = [""]
                        for i in range(1, len(uncaps)):
                            targets.append("_" + uncaps[i])
                        attacks = []
                        for t in targets:
                            for u in ["", "_2", "_3", "_4"]:
                                for form in (["", "_f", "_f1", "_f_01"] if altForm else [""]):
                                    try:
                                        fn = "phit_{}{}{}{}{}".format(tid, t, style, u, form)
                                        attacks += await self.processManifest(fn)
                                    except:
                                        pass
                        data[self.CHARA_PHIT] += attacks
                        # ougi
                        attacks = []
                        for uncap in uncaps:
                            for form in (["", "_f", "_f1", "_f_01"] if altForm else [""]):
                                for catype in ["", "_s2", "_s3"]:
                                    try:
                                        fn = "nsp_{}_{}{}{}{}".format(tid, uncap, style, form, catype)
                                        attacks += await self.processManifest(fn)
                                        break
                                    except:
                                        pass
                        data[self.CHARA_SP] += attacks
                        # skills
                        attacks = []
                        for el in ["01", "02", "03", "04", "05", "06", "07", "08"]:
                            try:
                                fn = "ab_all_{}{}_{}".format(tid, style, el)
                                attacks += await self.processManifest(fn)
                            except:
                                pass
                        data[self.CHARA_AB_ALL] += attacks
                        attacks = []
                        for el in ["01", "02", "03", "04", "05", "06", "07", "08"]:
                            try:
                                fn = "ab_{}{}_{}".format(tid, style, el)
                                attacks += await self.processManifest(fn)
                            except:
                                pass
                        data[self.CHARA_AB] += attacks
                    for s, t in tasks['scenes'].items():
                        if t is True or t.result() is not None:
                            data[self.CHARA_SCENE].add(s)
                    data[self.CHARA_SCENE] = list(data[self.CHARA_SCENE])
                    if tasks['sound'] is not None:
                        data[self.CHARA_SOUND] = tasks['sound'].result()
                    tasks = None
                self.modified = True
                self.data[index][id] = data
                self.addition[id] = self.ADD_CHAR
                await self.generateNameLookup(id)
            return True

    # Update partner data. Note: It's based on charaUpdate and is terribly inefficient
    async def partnerUpdate(self, id : str, step : int):
        with self.progress:
            async with self.sem:
                is_mc = id.startswith("389")
                try:
                    data = self.data['partners'][str((int(id) // 1000) * 1000)]
                    if data == 0: raise Exception()
                except:
                    data = [[], [], [], [], [], []] # sprite, phit, sp, aoe, single, general
                tid = id
                id = str((int(id) // 1000) * 1000)
                style = "" # placeholder
                max_err = 15 if id == "3890005000" else max(5, step // 3)  # placeholder
                # build set of existing element
                lookup = []
                for i in data[self.CHARA_SPRITE]:
                    if i.startswith("npc_"):
                        lookup.append(i.split('_')[1])
                for i in data[self.CHARA_PHIT]:
                    if i.startswith("phit_"):
                        lookup.append(i.split('_')[1])
                for i in data[self.CHARA_SP]:
                    if i.startswith("nsp_"):
                        lookup.append(i.split('_')[1])
                for i in data[self.CHARA_AB_ALL]:
                    if i.startswith("ab_all_"):
                        lookup.append(i.split('_')[2])
                for i in data[self.CHARA_AB]:
                    if i.startswith("ab_"):
                        lookup.append(i.split('_')[1])
                for i in data[self.CHARA_GENERAL]:
                    lookup.append(i.split('_')[0])
                lookup = set(lookup)
                edited = False
                err = 0
                # search loop
                while err < max_err:
                    if tid in lookup:
                        err = 0
                    else:
                        tmp = [[], [], [], [], [], []]
                        uncaps = []
                        sheets = []
                        altForm = False
                        # # # Assets
                        # arts
                        flags = await self.artCheck(tid, style, [])
                        targets = []
                        for uncap in flags:
                            # main
                            base_fn = "{}_{}{}".format(tid, uncap, style)
                            uf = flags[uncap]
                            for g in (["_0", "_1"] if (uf[0] is True) else [""]):
                                for m in (["_101", "_102", "_103", "_104", "_105"] if (uf[1] is True) else [""]):
                                    for n in (["_01", "_02", "_03", "_04", "_05", "_06"] if (uf[2] is True) else [""]):
                                        for af in (["", "_f", "_f1"] if altForm else [""]):
                                            targets.append(base_fn + af + g + m + n)
                        flags = None
                        tmp[self.CHARA_GENERAL] = targets
                        # # # Main sheets
                        for uncap in (["0_01", "1_01", "0_02", "1_02"] if is_mc else ["01", "02", "03", "04"]):
                            for ftype in ["", "_s2"]:
                                for form in ["", "_f", "_f1", "_f_01"]:
                                    try:
                                        fn = "npc_{}_{}{}{}{}".format(tid, uncap, style, form, ftype)
                                        sheets += await self.processManifest(fn, True)
                                        if form == "": uncaps.append(uncap)
                                        else: altForm = True
                                    except:
                                        if form == "":
                                            break
                        tmp[self.CHARA_SPRITE] = sheets
                        if is_mc: uncaps = ["01", "02"]
                        # # # Other sheets
                        # attack
                        targets = [""]
                        for i in range(2, len(uncaps)):
                            targets.append("_" + uncaps[i])
                        attacks = []
                        for t in targets:
                            for u in ["", "_2", "_3", "_4"]:
                                for form in (["", "_f", "_f1", "_f_01"] if altForm else [""]):
                                    try:
                                        fn = "phit_{}{}{}{}{}".format(tid, t, style, u, form)
                                        attacks += await self.processManifest(fn, True)
                                    except:
                                        pass
                        tmp[self.CHARA_PHIT] = attacks
                        # ougi
                        attacks = []
                        for uncap in uncaps:
                            for form in (["", "_f", "_f1", "_f_01"] if altForm else [""]):
                                for catype in ["", "_s2", "_s3", "_s2_b"]:
                                    try:
                                        fn = "nsp_{}_{}{}{}{}".format(tid, uncap, style, form, catype)
                                        attacks += await self.processManifest(fn, True)
                                        break
                                    except:
                                        pass
                        tmp[self.CHARA_SP] = attacks
                        # skills
                        attacks = []
                        for el in ["01", "02", "03", "04", "05", "06", "07", "08"]:
                            try:
                                fn = "ab_all_{}{}_{}".format(tid, style, el)
                                attacks += await self.processManifest(fn, True)
                            except:
                                pass
                        tmp[self.CHARA_AB_ALL] = attacks
                        attacks = []
                        for el in ["01", "02", "03", "04", "05", "06", "07", "08"]:
                            try:
                                fn = "ab_{}{}_{}".format(tid, style, el)
                                attacks += await self.processManifest(fn, True)
                            except:
                                pass
                        tmp[self.CHARA_AB] = attacks
                        # verification
                        l = 0
                        for i, e in enumerate(tmp):
                            if len(e) > 0:
                                l += len(e)
                                data[i] += e
                        if l == 0:
                            err += 1
                        else:
                            err = 0
                            edited = True
                    tid = str(int(tid) + step)
                    if tid[-4] != id[-4]: # end if we reached 1000 or more
                        break
                if not edited:
                    return False
                self.modified = True
                if id not in self.data['partners'] or self.data['partners'][id] == 0:
                    self.data['partners'][id] = data
                else:
                    for i, e in enumerate(data):
                        self.data['partners'][id][i] = list(set(self.data['partners'][id][i] + e))
                        self.data['partners'][id][i].sort()
                self.addition[id] = self.ADD_PARTNER
            return True

    # Update NPC data
    async def npcUpdate(self, id : str):
        with self.progress:
            async with self.sem:
                data = [False, [], []] # journal flag, npc, voice
                try:
                    await self.head(self.IMG + "sp/assets/npc/m/{}_01.jpg".format(id))
                    data[self.NPC_JOURNAL] = True
                except:
                    if id.startswith("305"): return False # don't continue for special npcs
                
                tasks = {'scenes':{}, 'sound':None}
                async with asyncio.TaskGroup() as tg:
                    # scene
                    try: scenes = set(self.data["npcs"][id][self.NPC_SCENE])
                    except: scenes = set()
                    data[self.NPC_SCENE] = scenes
                    self.group_scene_task(tg, tasks, id, [""], scenes)
                    # sound
                    try: voices = set(self.data['npcs'][id][self.NPC_SOUND])
                    except: voices = set()
                    tasks['sound'] = tg.create_task(self.update_chara_sound_file(id, None, voices))
                for s, t in tasks['scenes'].items():
                    if t is True or t.result() is not None:
                        data[self.NPC_SCENE].add(s)
                data[self.NPC_SCENE] = list(data[self.NPC_SCENE])
                if tasks['sound'] is not None:
                    data[self.NPC_SOUND] = tasks['sound'].result()
                tasks = None
                if not data[self.NPC_JOURNAL] and len(data[self.NPC_SCENE]) == 0:
                    if len(data[self.NPC_SOUND]) == 0: return False # nothing, quit
                    # check if proceed regardless
                    keys = list(self.data['npcs'].keys()) # get keys
                    keys = keys[max(0, len(keys)-100):] # last 100 (or less)
                    keys = [k for k in keys if self.data['npcs'][k] != 0] # remove unvalid ones
                    keys.sort() # sort so that the highest id is further right
                    if int(keys[-1]) <= int(id): # doesn't proceed with sound only if there is no valid npc further
                        return False
                self.modified = True
                self.data['npcs'][id] = data
                self.addition[id] = self.ADD_NPC
            return True

    # Update Summon data
    async def sumUpdate(self, id : str):
        with self.progress:
            async with self.sem:
                data = [[], [], []] # general, call, damage
                uncaps = []
                # main sheet
                for uncap in ["", "_02", "_03", "_04"]:
                    try:
                        fn = "{}_{}".format(id, uncap)
                        await self.head(self.IMG + "sp/assets/summon/m/{}{}.jpg".format(id, uncap))
                        data[self.SUM_GENERAL].append("{}{}".format(id, uncap))
                        uncaps.append("01" if uncap == "" else uncap[1:])
                    except:
                        break
                if len(uncaps) == 0 and id not in self.CUT_CONTENT:
                    return False
                multi = [""] if id not in self.SUM_MULTI else ["", "_a", "_b", "_c", "_d", "_e"]
                # attack
                for u in uncaps:
                    for m in multi:
                        try:
                            fn = "summon_{}_{}{}_attack".format(id, u, m)
                            data[self.SUM_CALL] += await self.processManifest(fn)
                        except:
                            pass
                # damage
                for u in uncaps:
                    for m in multi:
                        try:
                            fn = "summon_{}_{}{}_damage".format(id, u, m)
                            data[self.SUM_DAMAGE] += await self.processManifest(fn)
                        except:
                            pass
                self.modified = True
                self.data['summons'][id] = data
                self.addition[id] = self.ADD_SUMM
                await self.generateNameLookup(id)
            return True

    # Update Weapon data
    async def weapUpdate(self, id : str):
        with self.progress:
            async with self.sem:
                data = [[], [], []] # general, phit, sp
                # art
                try:
                    await self.head(self.IMG + "sp/assets/weapon/m/{}.jpg".format(id))
                    data[self.WEAP_GENERAL].append("{}".format(id))
                except:
                    if self.debug_wpn: data[self.WEAP_GENERAL].append("{}".format(id))
                    else: return False
                # attack
                for u in ["", "_2", "_3", "_4"]:
                    try:
                        fn = "phit_{}{}".format(id, u)
                        data[self.WEAP_PHIT] += await self.processManifest(fn)
                    except:
                        pass
                # ougi
                for u in ["", "_0", "_1", "_0_s2", "_1_s2", "_0_s3", "_1_s3"]:
                    try:
                        fn = "sp_{}{}".format(id, u)
                        data[self.WEAP_SP] += await self.processManifest(fn)
                    except:
                        pass
                if self.debug_wpn and len(data[self.WEAP_PHIT]) == 0 and len(data[self.WEAP_SP]) == 0:
                    return False
                self.modified = True
                self.data['weapons'][id] = data
                self.addition[id] = self.ADD_WEAP
                await self.generateNameLookup(id)
            return True

    # Update Enemy data
    async def mobUpdate(self, id : str):
        with self.progress:
            async with self.sem:
                data = [[], [], [], [], [], []] # general, sprite, appear, ehit, esp, esp_all
                # icon
                try:
                    await self.head(self.IMG + "sp/assets/enemy/s/{}.png".format(id))
                    data[self.BOSS_GENERAL].append("{}".format(id))
                except:
                    return False
                # sprite
                try:
                    fn = "enemy_{}".format(id)
                    data[self.BOSS_SPRITE] += await self.processManifest(fn)
                except:
                    pass
                # appear
                try:
                    fn = "raid_appear_{}".format(id)
                    data[self.BOSS_APPEAR] += await self.processManifest(fn)
                except:
                    pass
                # ehit
                try:
                    fn = "ehit_{}".format(id)
                    data[self.BOSS_HIT] += await self.processManifest(fn)
                except:
                    pass
                # esp
                for i in range(0, 20):
                    try:
                        fn = "esp_{}_{}".format(id, str(i).zfill(2))
                        data[self.BOSS_SP] += await self.processManifest(fn)
                    except:
                        pass
                    try:
                        fn = "esp_{}_{}_all".format(id, str(i).zfill(2))
                        data[self.BOSS_SP_ALL] += await self.processManifest(fn)
                    except:
                        pass
                self.modified = True
                self.data['enemies'][id] = data
                self.addition[id] = self.ADD_BOSS
            return True

    ### Scene ###################################################################################################################

    # Called once at boot. Generate a list of string to check for npc data
    def build_scene_strings(self, expressions : Optional[list] = None):
        if expressions is None or len(expressions) == 0:
            expressions = ["", "_up", "_laugh", "_laugh2", "_laugh3", "_wink", "_shout", "_shout2", "_sad", "_sad2", "_angry", "_angry2", "_school", "_shadow", "_shadow2", "_shadow3", "_light", "_close", "_serious", "_serious2", "_surprise", "_surprise2", "_think", "_think2", "_think3", "_think4", "_think5", "_serious", "_serious2", "_mood", "_mood2", "_ecstasy", "_ecstasy2", "_suddenly", "_suddenly2", "_ef", "_body", "_speed2", "_shy", "_shy2", "_weak", "_bad", "_amaze", "_joy", "_pride", "_eyeline"]
        variationsA = ["", "_a", "_b", "_c", "_battle"]
        variationsB = ["", "_speed", "_up", "_shadow", "_shadow2", "_shadow3", "_light"]
        scene_alts = []
        for A in variationsA:
            for ex in expressions:
                for B in variationsB:
                    if (A == "_battle" and B not in ["", "_speed", "_up", "_shadow"]) or (B != "" and (B == ex or (ex == "_speed2" and B == "_speed") or (ex.startswith("_shadow") and B.startswith("_shadow")))): continue
                    scene_alts.append(A+ex+B)
        specials = ["_light_heart", "_nalhe","_nalhe_up","_nalhe_speed", "_gesu", "_gesu2", "_stump", "_stump2", "_doya", "_2022_laugh", "_girl_laugh", "_girl_sad", "_girl_serious", "_girl_angry", "_girl_surprise", "_girl_think", "_town_thug", "_narrator", "_valentine", "_valentine_a", "_a_valentine", "_valentine2", "_valentine3", "_white", "_whiteday", "_whiteday2", "_whiteday3"]
        special_suffix = []
        for B in variationsB:
            if B != "":
                special_suffix.append(B.split("_")[-1])
        return scene_alts, specials, special_suffix

    # list known scene strings along with errors encountered along the way
    def list_known_scene_strings(self):
        keys = set()
        errs = []
        for x in ["characters", "skins"]:
            d = self.data[x]
            for k, v in d.items():
                try:
                    if isinstance(v, list) and isinstance(v[self.CHARA_SCENE], list):
                        for e in v[7]:
                            if e[:3] in ["_02", "_03", "_04", "_05"]: keys.add(e[3:])
                            else: keys.add(e)
                except:
                    errs.append(k)
        for x in ["npcs"]:
            for k, v in self.data[x].items():
                try:
                    if isinstance(v, list) and isinstance(v[self.NPC_SCENE], list):
                        for e in v[1]:
                            if e[:3] in ["_02", "_03", "_04", "_05"]: keys.add(e[3:])
                            else: keys.add(e)
                except:
                    errs.append(k)
        keys = list(keys)
        keys.sort()
        return keys, errs

    # output known scene strings in a JSON file. For debugging purpose
    async def debug_output_scene_strings(self, recur : bool = False):
        print("Exporting all scene file suffixes...")
        keys, errs = self.list_known_scene_strings()
        if len(errs) > 0: # refresh elements with errors
            if recur:
                print("Still", len(errs), "elements incorrectly formed, manual debugging is necessary")
            else:
                tmp = self.update_changelog
                self.update_changelog = False
                print(len(errs), "elements incorrectly formed, attempting to update")
                await self.manualUpdate(errs)
                await self.debug_output_scene_strings()
                self.update_changelog = tmp
        else:
            with open("json/debug_scene_strings.json", mode="w", encoding="utf-8") as f:
                json.dump(keys, f)
            print("Data exported to 'json/debug_scene_strings.json'")

    # Get suffix list for given uncap values
    def get_scene_string_list_for_uncaps(self, id : str, uncaps : list):
        scene_alts = []
        for uncap in uncaps:
            if uncap == "01": uncap = ""
            elif uncap[:1] in ['8', '9']: continue
            elif uncap != "": uncap = "_" + uncap
            for s in self.scene_strings:
                scene_alts.append(uncap+s)
        scene_alts += self.scene_special_strings
        if id.startswith("305"):
            i = 0
            while i < len(scene_alts):
                if scene_alts[i].endswith("_up"):
                    scene_alts = scene_alts[:i+1] + [scene_alts[i]+"2", scene_alts[i]+"3", scene_alts[i]+"4"] + scene_alts[i+1:]
                    i += 3
                i += 1
            scene_alts += ["_birthday", "_birthday2", "_birthday3", "_birthday3_a", "_birthday3_b"]
            scene_alts = list(set(scene_alts))
        return scene_alts

    # Function to populate the task group
    def group_scene_task(self, task_group : Optional[asyncio.TaskGroup], tasks : dict, id : str, uncaps : list, scenes : set):
        for s in self.get_scene_string_list_for_uncaps(id, uncaps):
            if s not in scenes:
                tmp = s.split("_")
                no_bubble = (s != "" and tmp[1].isdigit() and len(tmp[1]) == 2) # don't check raid bubbles for uncaps
                if not no_bubble:
                    for k in self.scene_special_suffix: # nor for those suffixes
                        if k in tmp[-1]:
                            no_bubble = True
                            break
                if task_group is None:
                    tasks['scenes'][s] = (no_bubble, s) # this behavior is only for update_all_scene()
                else:
                    if no_bubble:
                        tasks['scenes'][s] = task_group.create_task(self.head_nx(self.IMG + "sp/quest/scene/character/body/{}{}.png".format(id, s)))
                    else:
                        tasks['scenes'][s] = task_group.create_task(self.multi_head_nx([self.IMG + "sp/quest/scene/character/body/{}{}.png".format(id, s), self.IMG + "sp/raid/navi_face/{}{}.png".format(id, s)]))

    # Called by -scene, update all npc and character scene datas
    async def update_all_scene(self, target_index : Optional[str], targeted_strings : list = []):
        if target_index is None:
            target_index = ["characters", "skins", "npcs"]
        elif not isinstance(target_index, list):
            target_index = [target_index]
        if len(targeted_strings) > 0:
            self.scene_strings, self.scene_special_strings, self.scene_special_suffix = self.build_scene_strings(targeted_strings) # override
        print("Updating scene data for: {}...".format(" / ".join(target_index)))
        elements = []
        for k in target_index:
            for id in self.data[k]:
                if k == "npcs":
                    uncaps = [""]
                    idx = self.NPC_SCENE
                else:
                    uncaps = []
                    idx = self.CHARA_SCENE
                    for u in self.data[k][id][self.CHARA_GENERAL]:
                        uu = u.replace(id+"_", "")
                        if "_" not in uu and uu.startswith("0"):
                            uncaps.append(uu)
                tasks = {"scenes":{}}
                try: scenes = set(self.data[k][id][idx])
                except: scenes = set()
                self.group_scene_task(None, tasks, id, uncaps, scenes)
                keys = list(tasks["scenes"].keys())
                for i in range(0, len(keys), self.MAX_HTTP):
                    tup = {}
                    for kk in keys[i:i + self.MAX_HTTP]:
                        tup[kk] = tasks["scenes"][kk]
                    elements.append((k, id, idx, tup))
        try: # mem cleanup
            tasks = None
            keys = None
            uncaps = None
        except:
            pass
        self.progress = Progress(total=len(elements), silent=False)
        async for result in self.map_unordered(self.update_all_scene_sub, elements, self.MAX_HTTP):
            pass
        if len(targeted_strings) > 0:
            self.scene_strings, self.scene_special_strings, self.scene_special_suffix = self.build_scene_strings() # reset
        self.sort_all_scene()
        self.save()
        print("Done")

    # update_all_scene() subroutine
    async def update_all_scene_sub(self, tup : tuple):
        with self.progress:
            k, id, idx, tasks = tup
            for s, data in tasks.items():
                no_bubble, s = data
                if (await self.multi_head_nx([self.IMG + "sp/quest/scene/character/body/{}{}.png".format(id, s)] if no_bubble else [self.IMG + "sp/quest/scene/character/body/{}{}.png".format(id, s), self.IMG + "sp/raid/navi_face/{}{}.png".format(id, s)])) is not None:
                    self.data[k][id][idx].append(s)
                    self.modified = True

    # Sort scene data by string suffix order, to keep some sort of coherency on the web page
    def sort_all_scene(self):
        dummy_data = {s : False for s in self.scene_strings}
        for t in ["characters", "skins", "npcs"]:
            if t == "npcs": idx = self.NPC_SCENE
            else: idx = self.CHARA_SCENE
            for k, v in self.data[t].items():
                tmp = []
                for s in v[idx]:
                    if s not in tmp:
                        tmp.append(s)
                v[idx] = tmp
                before = str(v[idx])
                data = {"01":dummy_data.copy()}
                for s in v[idx]:
                    tmp = s.split("_")
                    if s != "" and tmp[1].isdigit() and len(tmp[1]) == 2:
                        if tmp[1] not in data:
                            data[tmp[1]] = dummy_data.copy()
                        data[tmp[1]][s[3:]] = True
                    else:
                        data["01"][s] = True
                new = []
                keys = list(data.keys())
                keys.sort()
                for dk in keys:
                    for ds, db in data[dk].items():
                        if db:
                            if dk == "01":
                                new.append(ds)
                            else:
                                new.append("_"+dk+ds)
                if str(new) != before:
                    self.modified = True
                    self.data[t][k][idx] = new
        print("Scene data sorted")
        self.save()

    ### Sound ###################################################################################################################

    # Called by -sound, update all npc and character sound datas
    async def update_all_sound(self):
        print("Updating sound data...")
        elements = []
        shared = []
        for k in ["characters", "skins", "npcs"]:
            for id in self.data[k]:
                if k == "npcs":
                    uncaps = ["01"]
                    idx = self.NPC_SOUND
                else:
                    uncaps = []
                    idx = self.CHARA_SOUND
                    for u in self.data[k][id][self.CHARA_GENERAL]:
                        uu = u.replace(id+"_", "")
                        if "_" not in uu and uu.startswith("0") and uu != "02":
                            uncaps.append(uu)
                try: voices = set(self.data[k][id][idx])
                except: voices = set()
                prep = self.update_chara_sound_file_prep(id, uncaps, voices)
                self.newShared(shared)
                shared[-1][1] = [] # change 2nd value to an array
                for i in range(0, len(prep), self.MAX_SOUND_CONCURRENT):
                    prep_split = []
                    if i == 0: prep_split.append(None)
                    for kk in prep[i:i + self.MAX_SOUND_CONCURRENT]:
                        prep_split.append(kk)
                    elements.append((k, id, idx, shared[-1], voices, prep_split))
                    shared[-1][2] += 1
        self.progress = Progress(total=len(elements), silent=False)
        async for result in self.map_unordered(self.update_all_sound_sub, elements, self.MAX_HTTP):
            pass
        self.save()
        print("Done")

    # update_all_sound() subroutine
    async def update_all_sound_sub(self, tup : tuple):
        with self.progress:
            index, id, idx, shared, existing, elements = tup
            for t in elements:
                if t is None:
                    shared[1] += await self.update_chara_sound_file_sub_banter(id, existing)
                else:
                    shared[1] += await self.update_chara_sound_file_sub(*t)
            shared[0] += 1
        if shared[0] >= shared[2]:
            if len(shared[1]) != len(self.data[index][id][idx]):
                self.data[index][id][idx] = shared[1]
                self.data[index][id][idx].sort()
                self.modified = True
                shared[1] = None

    # prep work for update_chara_sound_file
    def update_chara_sound_file_prep(self, id : str, uncaps : Optional[list] = None, existing : set = set()):
        elements = []
        # standard stuff
        for uncap in uncaps:
            if uncap == "01": uncap = ""
            elif uncap == "02": continue # seems unused
            elif uncap != "": uncap = "_" + uncap
            for mid, Z in [("_", 3), ("_v_", 3), ("_introduce", 1), ("_mypage", 1), ("_formation", 2), ("_evolution", 2), ("_archive", 2), ("_zenith_up", 2), ("_kill", 2), ("_ready", 2), ("_damage", 2), ("_healed", 2), ("_dying", 2), ("_power_down", 2), ("_cutin", 1), ("_attack", 1), ("_attack", 2), ("_ability_them", 1), ("_ability_us", 1), ("_mortal", 1), ("_win", 1), ("_lose", 1), ("_to_player", 1)]:
                match mid: # opti
                    case "_":
                        suffixes = ["", "a", "b"]
                        A = 1
                        max_err = 1
                    case "_v_":
                        suffixes = ["", "a", "_a", "_1", "b", "_b", "_2"]
                        A = 1
                        max_err = 6
                    case _:
                        suffixes = ["", "a", "_a", "_1", "b", "_b", "_2", "_mix"]
                        A = 0 if mid == "_cutin" else 1
                        max_err = 1
                elements.append((id, existing, uncap + mid + "{}", suffixes, A, Z, max_err))
            # chain burst
            elements.append((id, existing, "_chain_start", [], None, None, None))
            for A in range(2, 5):
                elements.append((id, existing, "_chain{}_"+str(A), [], 1, 1, 1))
            # seasonal A
            for mid, Z in [("_birthday", 1), ("_Birthday", 1), ("_birthday_mypage", 1), ("_newyear_mypage", 1), ("_newyear", 1), ("_Newyear", 1), ("_valentine_mypage", 1), ("_valentine", 1), ("_Valentine", 1), ("_white_mypage", 1), ("_whiteday", 1), ("_WhiteDay", 1), ("_halloween_mypage", 1), ("_halloween", 1), ("_Halloween", 1), ("_christmas_mypage", 1), ("_christmas", 1), ("_Christmas", 1), ("_xmas", 1), ("_Xmas", 1)]:
                elements.append((id, existing, mid + "{}", [], 1, Z, 5))
            for suffix in ["white","newyear","valentine","christmas","halloween","birthday"]:
                for s in range(1, 6):
                    elements.append((id, existing, "_s{}_{}".format(s, suffix) + "{}", [], 1, 1, 5))
        return elements

    # search sound files for a character/skin/npc
    async def update_chara_sound_file(self, id : str, base_uncaps : Optional[list] = None, existing : set = set()):
        if base_uncaps is None:
            base_uncaps = ["01"]
        uncaps = [u for u in base_uncaps if ("_" not in u and u.startswith("0"))]
        async with asyncio.TaskGroup() as tg:
            tasks = []
            for t in self.update_chara_sound_file_prep(id, uncaps, existing):
                tasks.append(tg.create_task(self.update_chara_sound_file_sub(*t)))
            # banter
            tasks.append(tg.create_task(self.update_chara_sound_file_sub_banter(id, existing)))
        result = []
        for t in tasks:
            result += t.result()
        # sorting
        A = []
        B = []
        for k in result:
            if k.split("_")[1] in ["02", "03", "04", "05"]:
                B.append(k)
            else:
                A.append(k)
        A.sort()
        B.sort()
        return A+B

    # generic sound subroutine
    async def update_chara_sound_file_sub(self, id : str, existing : set, suffix : str, post : list, index : Optional[int], zfill : Optional[int], max_err : Optional[int]):
        result = []
        if len(post) == 0: post = [""]
        if index is None: # single mode
            for p in post:
                f = suffix + p
                if f in existing or (await self.head_nx(self.VOICE + "{}{}.mp3".format(id, f))) is not None:
                    result.append(f)
        else:
            err = 0
            run = True
            while run:
                exists = False
                for p in post:
                    f = suffix.format(str(index).zfill(zfill)) + p
                    if f in existing:
                        exists = True
                        result.append(f)
                        err = 0
                if not exists:
                    found = True
                    for p in post:
                        f = suffix.format(str(index).zfill(zfill)) + p
                        if f in existing or (await self.head_nx(self.VOICE + "{}{}.mp3".format(id, f))) is not None:
                            result.append(f)
                            err = 0
                            found = True
                        elif p == post[-1] and not found:
                            err += 1
                            if err >= max_err and index > 0:
                                run = False
                index += 1
        return result

    # banter sound subroutine
    async def update_chara_sound_file_sub_banter(self, id : str, existing : set):
        result = []
        A = 1
        B = 1
        Z = None
        while True:
            success = False
            for i in range(1, 3):
                if Z is None or Z == i:
                    try:
                        f = "_pair_{}_{}".format(A, str(B).zfill(i))
                        if f not in existing: await self.head(self.VOICE + "{}{}.mp3".format(id, f))
                        result.append(f)
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
        return result

    ### Lookup ##################################################################################################################

    # Check the given id on the wiki to retrieve element details. Only for summons, weapons and characters.
    async def generateNameLookup(self, cid : str):
        with self.progress:
            if not cid.startswith("20") and not cid.startswith("10") and not cid.startswith("30"): return
            r = await self.get("https://gbf.wiki/index.php?search={}".format(cid))
            if r is not None:
                try: content = r.decode('utf-8')
                except: content = r.decode('iso-8859-1')
                soup = BeautifulSoup(content, 'html.parser')
                m = None
                try:
                    res = soup.find_all("ul", class_="mw-search-results")[0].findChildren("li", class_="mw-search-result", recursive=False) # recuperate the search results
                    for r in res: # for each, get the title
                        m = r.findChildren("div", class_="mw-search-result-heading", recursive=False)[0].findChildren("a", recursive=False)[0].attrs['title']
                        break
                except:
                    pass
                if m is not None:
                    await self.generateNameLookup_sub(cid, m)
                else: # CN wiki fallback
                    try:
                        r = await self.get("https://gbf.huijiwiki.com/wiki/{}/{}".format({"3":"Char","2":"Summon","1":"Weapon"}[cid[0]], cid))
                        if r is not None:
                            try: content = r.decode('utf-8')
                            except: content = r.decode('iso-8859-1')
                            soup = BeautifulSoup(content, 'html.parser')
                            res = soup.find_all("div", class_="gbf-infobox-section")
                            for r in res:
                                a = str(r).find("https://gbf.wiki/")
                                if a != -1:
                                    a+=len("https://gbf.wiki/")
                                    b = str(r).find('"', a)
                                    await self.generateNameLookup_sub(cid, str(r)[a:b])
                    except:
                        pass

    # generateNameLookup() subroutine. Read the wiki page to extract element details (element, etc...)
    async def generateNameLookup_sub(self, cid : str, wiki_lookup : str):
        data = {}
        if cid.startswith("20"):
            data["What"] = "Summon"
        elif cid.startswith("10"):
            data["What"] = "Weapon"
            match cid[4]:
                case '0': data['Proficiency'] = "Sword"
                case '1': data['Proficiency'] = "Dagger"
                case '2': data['Proficiency'] = "Spear"
                case '3': data['Proficiency'] = "Axe"
                case '4': data['Proficiency'] = "Staff"
                case '5': data['Proficiency'] = "Gun"
                case '6': data['Proficiency'] = "Melee"
                case '7': data['Proficiency'] = "Bow"
                case '8': data['Proficiency'] = "Harp"
                case '9': data['Proficiency'] = "Katana"
        elif cid.startswith("30"):
            data["What"] = "Character"
        else:
            return False
        match cid[2]:
            case '1': data['Rarity'] = 'N'
            case '2': data['Rarity'] = 'R'
            case '3': data['Rarity'] = 'SR'
            case '4': data['Rarity'] = 'SSR'
        try:
            r = await self.get("https://gbf.wiki/{}".format(wiki_lookup.replace(' ', '_')))
            try: content = r.decode('utf-8')
            except: content = r.decode('iso-8859-1')
            soup = BeautifulSoup(content, 'html.parser')
            tables = soup.find_all("table", class_='wikitable') # iterate all wikitable
            data['Name'] = self.cleanName(wiki_lookup)
            for t in tables:
                try:
                    body = t.findChildren("tbody", recursive=False)[0].findChildren("tr" , recursive=False) # check for tr tag
                    for tr in body:
                        for k in ["Race", "Element", "Gender", "JP"]:
                            if str(tr).find(k) != -1 and k not in data:
                                a = str(tr).find("/Category:")
                                if k == "Race":
                                    while a != -1:
                                        a += len("/Category:")
                                        b= str(tr).find("_", a)
                                        s = str(tr)[a:b]
                                        if s == "Other": s = "Unknown"
                                        if "Type" not in data: data["Type"] = []
                                        if s not in data["Type"]:
                                            data["Type"].append(s)
                                        a = str(tr).find("/Category:", b)
                                elif k == "Gender":
                                    if "Male" in str(tr): data[k] = "Male"
                                    elif "Female" in str(tr): data[k] = "Female"
                                    elif "Other" in str(tr): data[k] = "Other"
                                    break
                                elif k == "JP":
                                    try: data['JP'] = tr.findChildren("td" , recursive=False)[0].text
                                    except: pass
                                    break
                                elif a != -1:
                                    a += len("/Category:")
                                    b= str(tr).find("_", a)
                                    data[k] = str(tr)[a:b]
                                    break
                                elif data["What"] == "Weapon" and k == "Element":
                                    a += len("/Category:")
                                    while True:
                                        b= str(tr).find("Element_", a)
                                        if b == -1: break
                                        a = str(tr).find(".", b)
                                        if a == -1: break;
                                        if str(tr)[b+len("Element_"):a] in ["Fire", "Water", "Earth", "Wind", "Dark", "Light", "Special"]:
                                            data[k] = str(tr)[b+len("Element_"):a]
                                            break
                                    if k in data:
                                        break
                except:
                    pass
                # series
                try:
                    imgs = t.findChildren("img", recursive=True)
                    for img in imgs:
                        if img.has_attr('alt') and 'Series' in img.attrs['alt']:
                            if 'Series' not in data: data['Series'] = []
                            data['Series'].append(img.attrs['alt'].split(' ')[1])
                except:
                    pass
            # validity check
            is_valid = True
            match data["What"]:
                case "Weapon":
                    expected = ["Rarity", "Name", "Proficiency", "JP"]
                    s = " ".join(data.get("Series", "")).lower()
                    if s == "":
                        expected.append("Element")
                    else:
                        series_check = False
                        for k in ["ultima", "superlative", "class", "champion"]:
                            if k in s:
                                series_check = True
                                break
                        if not series_check:
                            expected.append("Element")
                case "Character":
                    expected = ["Rarity", "Name", "Gender", "JP", "Type"]
                    if data['Name'].lower() not in ["lyria", "blue poppet", "brown poppet", "young cat", "sierokarte"]:
                        expected.append("Element")
                case "Summon":
                    expected = ["Rarity", "Name", "Element"]
                case _:
                    return False
            for k in expected:
                if k not in data:
                    is_valid = False
                    break
            if cid in self.CUT_CONTENT: data["Cut-Content"] = "cut-content"
            elif not is_valid: return False
            data["ID"] = cid
            tmp = []
            for v in data.values():
                if isinstance(v, list): tmp += v
                else: tmp.append(v)
            self.data["lookup"][cid] = " ".join(tmp).lower().replace('  ', ' ')
            self.modified = True
            return True
        except:
            pass
        return False

    # Check for new elements to lookup on the wiki, to update the lookup list
    async def buildLookup(self):
        tasks = []
        async with asyncio.TaskGroup() as tg:
            print("Checking elements in need of update...")
            self.progress = Progress()
            for t in ['characters', 'summons', 'weapons']:
                for k in self.data[t]:
                    if k not in self.data['lookup'] or self.data['lookup'][k] is None:
                        if k in self.SPECIAL_LOOKUP:
                            self.data['lookup'][k] = self.SPECIAL_LOOKUP[k]
                            self.modified = True
                        else:
                            tasks.append(tg.create_task(self.generateNameLookup(k)))
            self.progress.set(total=len(tasks), silent=False)
        for t in tasks:
            t.result()
        # second pass
        for t in ['characters', 'summons', 'weapons']:
            for k in self.data[t]:
                if k not in self.data['lookup'] or self.data['lookup'][k] is None:
                    for l in self.SHARED_NAMES:
                        if k not in l: continue
                        for m in l:
                            if m != k and m in self.data['lookup'] and m is not None:
                                self.data['lookup'][k] = self.data['lookup'][m].replace(m, k)
                                self.modified = True
                                print(k,"and",m,"matched up")
                                break
                            break
                else:
                    if k not in self.data['lookup'][k]:
                        self.data['lookup'][k] = self.data['lookup'][k].strip() + " " + k
                        self.modified = True
        # print remaining
        count = 0
        for t in ['characters', 'summons', 'weapons']:
            for k in self.data[t]:
                if k not in self.data['lookup'] or self.data['lookup'][k] is None:
                    count += 1
        print(count, "element(s) remaining without data")
        self.save()
        print("Done")

    # called by -lookupfix, to manually edit missing data in case of system failure
    async def manualLookup(self):
        to_delete = []
        for k, v in self.data["lookup"].items():
            if 'cut-content' in v: continue
            x = v.split(" ")
            match k[0]:
                case '3':
                    check = False
                    for e in ["lyria", "blue poppet", "brown poppet", "young cat", "sierokarte"]:
                        if e in v:
                            check = True
                            break
                    if not check:
                        check = False
                        for e in ["fire", "water", "earth", "wind", "light", "dark"]:
                            if e in x:
                                check = True
                                break
                        if not check:
                            to_delete.append(k)
                            print(k[0], k, x[-5], "/", v)
                case '2':
                    check = False
                    for e in ["fire", "water", "earth", "wind", "light", "dark"]:
                        if e in x:
                            check = True
                            break
                    if not check:
                        to_delete.append(k)
                        print(k[0], k, x[-3], "/", v)
                case '1':
                    check = False
                    for e in ["ultima", "superlative", "class", "champion"]:
                        if e in v:
                            check = True
                            break
                    if not check:
                        check = False
                        for e in ["fire", "water", "earth", "wind", "light", "dark"]:
                            if e in x:
                                check = True
                                break
                        if not check:
                            to_delete.append(k)
                            print(k[0], k, x[-3], "/", v)
        if len(to_delete) > 0:
            print(len(to_delete), "entries with possibly incomplete lookup.")
            if input("Reset them? ('y' to confirm):").lower() == 'y':
                for k in to_delete:
                    self.data["lookup"].pop(k)
                self.modified = True
        for t in ['characters', 'summons', 'weapons']:
            for k in self.data[t]:
                if k not in self.data['lookup'] or self.data['lookup'][k] is None:
                    print("##########################################")
                    print("Input the Wiki URL string for ID", k, "(Leave blank to skip)")
                    while True:
                        s = input()
                        if s == "": break
                        s = s.replace("https://gbf.wiki/", "")
                        if not await self.generateNameLookup_sub(k, s):
                            print("Page not found, try again")
                        else:
                            break
        self.save()
        print("Done")

    ### Thumbnail ###############################################################################################################

    # Check the NPC list for npc with new thumbnails.
    async def update_npc_thumb(self):
        print("Updating NPC thumbnail data...")
        tasks = []
        async with asyncio.TaskGroup() as tg:
            self.progress = Progress()
            for id in self.data["npcs"]:
                if not isinstance(self.data["npcs"][id], int) and not self.data["npcs"][id][0]:
                    tasks.append(tg.create_task(self.update_npc_thumb_sub(id)))
            self.progress.set(total=len(tasks), silent=False)
        for t in tasks:
            t.result()
        print("Done")
        self.save()

    # update_npc_thumb() subroutine
    async def update_npc_thumb_sub(self, id : str): # subroutine
        with self.progress:
            try:
                await self.head(self.IMG + "sp/assets/npc/m/{}_01.jpg".format(id))
                self.data["npcs"][id][0] = True
                self.modified = True
            except:
                pass

    ### Relation ################################################################################################################

    # Make a list of elements to check on the wiki and update them
    async def build_relation(self, to_update : list = []):
        try:
            with open("json/relation_name.json", "r") as f:
                self.name_table = json.load(f)
            print("Element name table loaded")
        except:
            self.name_table = {}
        self.name_table_modified = False
        relation = self.data.get("relations", {})
        new = []
        tasks = []
        async with asyncio.TaskGroup() as tg:
            self.progress = Progress()
            if len(to_update) == 0:
                for eid in self.data['characters']:
                    if eid not in relation or len(relation[eid]) == 0:
                        tasks.append(tg.create_task(self.get_relation(eid)))
                for eid in self.data['summons']:
                    if eid not in relation:
                        tasks.append(tg.create_task(self.get_relation(eid)))
                for eid in self.data['weapons']:
                    if eid not in relation:
                        tasks.append(tg.create_task(self.get_relation(eid)))
            else:
                for eid in to_update:
                    tasks.append(tg.create_task(self.get_relation(eid)))
            self.progress.set(total=len(tasks), silent=False)
        if len(tasks) > 0:
            print("Checking for new relationships...")
            for t in tasks:
                r = t.result()
                try:
                    if r[0] is None or (r[0] not in self.data['characters'] and r[0] not in self.data['summons'] and r[0] not in self.data['weapons'] and r[0] not in self.data['skins']) or (r[0] in relation and len(r[1]) == len(relation[r[0]])): raise Exception()
                    relation[r[0]] = r[1]
                    new.append(r[0])
                except:
                    pass
            for n in new:
                for eid in relation[n]:
                    if eid not in relation:
                        relation[eid] = []
                        self.modified = True
                    if n not in relation[eid]:
                        relation[eid].append(n)
                        relation[eid].sort()
                        self.modified = True
                relation[n].sort()
            if len(new) > 0:
                print("Comparing with the name table...")
                for k in self.name_table:
                    ks = k.replace(',', '').split(' ')
                    for l in self.name_table:
                        ls = l.replace(',', '').split(' ')
                        if l != k and k in ls or l in ks and self.name_table[k] != self.name_table[l]:
                            for e in self.name_table[l]:
                                if e not in self.name_table[k]:
                                    self.name_table[k].append(e)
                            self.name_table[l] = self.name_table[k]
                for k in self.name_table:
                    for eid in self.name_table[k]:
                        if eid not in relation:
                            relation[eid] = []
                            self.modified = True
                        for oid in self.name_table[k]:
                            if oid == eid or oid in relation[eid]: continue
                            relation[eid].append(oid)
                            relation[eid].sort()
                            self.modified = True
                self.data['relations'] = relation
                self.save()
            if self.name_table_modified:
                try:
                    with open("json/relation_name.json", "w") as f:
                        json.dump(self.name_table, f, sort_keys=True, indent='\t', separators=(',', ':'))
                    print("Name table updated")
                except:
                    pass

    # build_relation() subroutine. Check an element wiki page for alternate version or corresponding weapons
    async def get_relation(self, eid : str):
        with self.progress:
            async with self.wiki_sem:
                try:
                    page = await self.get("https://gbf.wiki/index.php?search={}".format(eid))
                    try: page = page.decode('utf-8')
                    except: page = page.decode('iso-8859-1')
                    page = page[page.find('mw-content-text'):page.find('printfooter')]
                    links = []
                    b = 0
                    while True:
                        a = page.find('<a href="', b)
                        if a == -1: break
                        a += len('<a href="')
                        b = page.find('"', a)
                        link = page[a:b]
                        if 'index.php' not in link and '/' not in link[1:]:
                            links.append(link)
                except:
                    return None, []
                for link in links:
                    try:
                        page = await self.get("https://gbf.wiki" + link)
                        name = link[1:].split('(')[0].replace('_', ' ').strip().lower()
                        if not eid.startswith('10'):
                            with self.name_lock:
                                if name not in self.name_table:
                                    self.name_table[name] = []
                                if eid not in self.name_table[name] and not eid.startswith('399') and not eid.startswith('305'):
                                    self.name_table[name].append(eid)
                                    self.name_table_modified = True
                        try: page = page.decode('utf-8')
                        except: page = page.decode('iso-8859-1')
                        ids = set()
                        for sequence in [('multiple versions', '_details'), ('Recruitment Weapon', '</td>'), ('Outfits', 'References')]:
                            a = page.find(sequence[0])
                            if a == -1: continue
                            a += len(sequence[0])
                            b = page.find(sequence[1], a)
                            for sid in self.ID_REGEX.findall(page[a:b]):
                                if sid != eid:
                                    ids.add(sid)
                        b = 0
                        while True:
                            a = page.find("wikitable", b)
                            if a == -1: break
                            a += len("wikitable")
                            b = page.find("</table>", a)
                            for sid in self.ID_REGEX.findall(page[a:b]):
                                if sid != eid:
                                    ids.add(sid)
                        return eid, list(ids)
                    except:
                        return eid, []

    # Used to manually connect elements in A to B
    def connect_relation(self, As : list, B : str):
        try:
            with open("json/relation_name.json", "r") as f:
                self.name_table = json.load(f)
            print("Element name table loaded")
        except:
            self.name_table = {}
        self.name_table_modified = False
        relation = self.data.get("relations", {})
        print("Trying to add relation...")
        for A in As:
            if A not in self.data['characters'] and A not in self.data['summons'] and A not in self.data['weapons']:
                print("Unknown element:", A)
                continue
            if B not in self.data['characters'] and B not in self.data['summons'] and B not in self.data['weapons'] and B not in self.data['skins']:
                print("Unknown element:", B)
                continue
            if A not in relation:
                relation[A] = []
            if B in relation[A]:
                print("Relation already exists")
                continue
            relation[A].append(B)
            self.modified = True
            for eid in relation[A]:
                if eid not in relation:
                    relation[eid] = []
                if A not in relation[eid]:
                    relation[eid].append(A)
                    relation[eid].sort()
            relation[A].sort()
        if self.modified:
            for k in self.name_table:
                ks = k.replace(',', '').split(' ')
                for l in self.name_table:
                    ls = l.replace(',', '').split(' ')
                    if l != k and k in ls or l in ks and self.name_table[k] != self.name_table[l]:
                        for e in self.name_table[l]:
                            if e not in self.name_table[k]:
                                self.name_table[k].append(e)
                        self.name_table[l] = self.name_table[k]
            for k in self.name_table:
                for eid in self.name_table[k]:
                    if eid not in relation:
                        relation[eid] = []
                    for oid in self.name_table[k]:
                        if oid == eid or oid in relation[eid]: continue
                        relation[eid].append(oid)
                        relation[eid].sort()
            self.save()

    # CLI
    async def relation_edit(self):
        while True:
            print("[0] Redo Relationship")
            print("[1] Add Relationship")
            match input():
                case '0':
                    while True:
                        s = input("ID(s):")
                        if s == "":
                            break
                        else:
                            await self.build_relation([x for x in s.split(' ') if x != ''])
                            break
                case '1':
                    while True:
                        s = input("ID(s) to edit:")
                        if s == "":
                            break
                        else:
                            sid = [x for x in s.split(' ') if x != '']
                            while True:
                                s = input("Connect to which ID:")
                                if s == "":
                                    break
                                else:
                                    self.connect_relation(sid, s)
                                    break
                            break
                case _:
                    break
    ### Events ##################################################################################################################

    # Ask the wiki to build a list of existing events with their start date. Note: It needs to be updated for something more efficient
    async def get_event_list(self):
        r = await self.get('https://gbf.wiki/index.php?title=Special:Search&limit=500&offset=0&profile=default&search=%22Initial+Release%22')
        soup = BeautifulSoup(r.decode("utf-8"), 'html.parser')
        res = soup.find_all("div", class_="searchresult")
        l = ["201017", "211017", "221017", "231017", "200214", "210214", "220214", "230214", "200314", "210314", "220314", "230314", "201216", "211216", "221216", "231216", "210316", "230303", "220304", "220313"]
        for r in res:
            try:
                x = r.text.split(": ")[1].split(" Rerun")[0].split(" Added")[0].replace(",", "").split(" ")
                if len(x) != 3: raise Exception()
                x[0] = {"January":"01", "February":"02", "March":"03", "April":"04", "May":"05", "June":"06", "July":"07", "August":"08", "September":"09", "October":"10", "November":"11", "December":"12"}[x[0]]
                x[1] = str(x[1]).zfill(2)
                x[2] = x[2][2:]
                l.append(x[2]+x[0]+x[1])
            except:
                pass
        r = await self.get('https://gbf.wiki/index.php?title=Special:Search&limit=500&offset=0&profile=default&search=%22Event+duration%22')
        soup = BeautifulSoup(r.decode("utf-8"), 'html.parser')
        res = soup.find_all("div", class_="searchresult")
        for r in res:
            try:
                x = r.text.split("JST, ")[1].split(" - ")[0].split(" //")[0].replace(",", "").split(" ")
                if len(x) != 3: raise Exception()
                x[0] = {"January":"01", "February":"02", "March":"03", "April":"04", "May":"05", "June":"06", "July":"07", "August":"08", "September":"09", "October":"10", "November":"11", "December":"12"}[x[0]]
                x[1] = str(x[1]).zfill(2)
                x[2] = x[2][2:]
                l.append(x[2]+x[0]+x[1])
            except:
                pass
        l = list(set(l))
        l.sort()
        return l

    # Call get_event_list() and check the current time to determine if new events have been added. If so, check if they got voice lines to determine if they got chapters, and then call update_event()
    async def check_new_event(self, init_list : Optional[list] = None):
        now = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=32400) - timedelta(seconds=68430)
        now = int(str(now.year)[2:] + str(now.month).zfill(2) + str(now.day).zfill(2))
        if init_list is None:
            known_events = await self.get_event_list()
        else:
            init_list = list(set(init_list))
            known_events = init_list
        # check
        print("Checking for new events...")
        tasks = []
        async with asyncio.TaskGroup() as tg:
            check = {}
            self.progress = Progress()
            for ev in known_events:
                if ev not in self.data["events"] and now >= int(ev):
                    check[ev] = -1
                    for i in range(0, self.EVENT_MAX_CHAPTER):
                        for j in range(1, 2):
                            for k in range(1, 2):
                               tasks.append(tg.create_task(self.update_event_sub(ev, self.VOICE + "scene_evt{}_cp{}_q{}_s{}0".format(ev, i, j, k))))
            self.progress.set(total=len(tasks), silent=False)
        if len(tasks) > 0:
            print(len(check.keys()), "potential new event(s)")
            new_story_event = []
            for t in tasks:
                r = t.result()
                ev = r[0]
                if r[1] is not None:
                    check[ev] = max(check[ev], int(r[1].split('_')[2][2:]))
            for ev in check:
                if check[ev] >= 0:
                    print("Event", ev, "has", check[ev], "chapters")
                    new_story_event.append(ev)
                self.data["events"][ev] = [check[ev], None, [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []] # 15+3+sky
                self.modified = True
            if len(new_story_event) > 0:
                new_story_event.sort()
                await self.event_thumbnail_association(new_story_event)
        print("Done")
        self.save()
        if init_list is None:
            await self.update_event(list(check.keys()))
        else:
            await self.update_event(init_list, full=True)

    # check_new_event() subroutine to request sound files
    async def update_event_sub(self, ev : str, url : str):
        with self.progress:
            for m in range(1, 20):
                try:
                    await self.head(url + "_{}.mp3".format(m))
                    return ev, url.split('/')[-1]
                except:
                    pass
            return ev, None

    # Check the given event list for potential art pieces
    async def update_event(self, events : list, full : bool = False):
        # dig
        tasks = []
        async with asyncio.TaskGroup() as tg:
            modified = set()
            ec = 0
            self.progress = Progress()
            for ev in events:
                if full and ev not in self.data["events"]:
                    self.data["events"][ev] = [-1, None, [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []] # 15+3+sky
                if ev in self.data["events"] and (full or (not full and self.data["events"][ev][self.EVENT_CHAPTER_COUNT] >= 0)):
                    known_assets = set()
                    for i in range(self.EVENT_OP, len(self.data["events"][ev])):
                        for e in self.data["events"][ev][i]:
                            known_assets.add(e)
                    ec += 1
                    if full: ch_count = self.EVENT_MAX_CHAPTER
                    else: ch_count = self.data["events"][ev][self.EVENT_CHAPTER_COUNT]
                    for j in range(4):
                        for i in range(1, ch_count+1):
                            fn = "scene_evt{}_cp{}".format(ev, str(i).zfill(2))
                            tasks.append(tg.create_task(self.update_event_sub_big(ev, self.IMG + "sp/quest/scene/character/body/"+fn, known_assets, j*25)))
                        for ch in ["op", "ed"]:
                            fn = "scene_evt{}_{}".format(ev, ch)
                            tasks.append(tg.create_task(self.update_event_sub_big(ev, self.IMG + "sp/quest/scene/character/body/"+fn, known_assets, j*25)))
                        fn = "evt{}".format(ev)
                        tasks.append(tg.create_task(self.update_event_sub_big(ev, self.IMG + "sp/quest/scene/character/body/"+fn, known_assets, j*25)))
                        fn = "scene_evt{}".format(ev)
                        tasks.append(tg.create_task(self.update_event_sub_big(ev, self.IMG + "sp/quest/scene/character/body/"+fn, known_assets, j*25)))
            self.progress.set(total=len(tasks), silent=False)
        if len(tasks) > 0:
            print("Checking assets for", ec, "event(s)")
            for t in tasks:
                r = t.result()
                if r is not None:
                    ev = r[0]
                    if len(r[1])  > 0:
                        for e in r[1]:
                            try:
                                x = e.split("_")[2]
                                match x:
                                    case "op":
                                        self.data["events"][ev][self.EVENT_OP].append(e)
                                    case "ed":
                                        self.data["events"][ev][self.EVENT_ED].append(e)
                                    case "osarai":
                                        self.data["events"][ev][self.EVENT_INT].append(e)
                                    case _:
                                        if "_cp" in e:
                                            self.data["events"][ev][self.EVENT_CHAPTER_START-1+int(x[2:])].append(e)
                                        else:
                                            self.data["events"][ev][self.EVENT_INT].append(e)
                            except:
                                self.data["events"][ev][self.EVENT_INT].append(e)
                        modified.add(ev)
            for ev in modified:
                if full and self.data["events"][ev][self.EVENT_CHAPTER_COUNT] == -1: self.data["events"][ev][self.EVENT_CHAPTER_COUNT] = 0
                for i in range(self.EVENT_OP , len(self.data["events"][ev])):
                    self.data["events"][ev][i] = list(set(self.data["events"][ev][i]))
                    self.data["events"][ev][i].sort()
                    self.modified = True
                self.addition[ev] = self.ADD_EVENT
            print("Done")
        self.save()

    # update_event() subroutine to check an event possible art pieces
    async def update_event_sub_big(self, ev : str, base_url : str, known_assets : set, step : int):
        with self.progress:
            l = []
            for j in range(step, step+25):
                url = base_url + "_" + str(j).zfill(2)
                flag = False
                try: # base check
                    if url.split("/")[-1] not in known_assets:
                        self.head(url + ".png")
                        l.append(url.split("/")[-1])
                    flag = True
                except:
                    pass
                if flag: # check for extras
                    for k in ["_up", "_shadow"]:
                        try:
                            if url.split("/")[-1]+k not in known_assets:
                                self.head(url + k + ".png")
                                l.append(url.split("/")[-1]+k)
                        except:
                            pass
                    for k in ["_a", "_b", "_c", "_d", "_e", "_f", "_g", "_h", "_i", "_j", "_k", "_l", "_m", "_n", "_o", "_p", "_q", "_r", "_s", "_t", "_u", "_v", "_w", "_x", "_y", "_z"]:
                        try:
                            if url.split("/")[-1]+k not in known_assets:
                                self.head(url + k + ".png")
                                l.append(url.split("/")[-1]+k)
                        except:
                            break
                else:
                    try: # alternative filename format
                        if url.split("/")[-1]+"_00" not in known_assets:
                            self.head(url + "_00.png")
                            l.append(url.split("/")[-1]+"_00")
                        flag = True
                    except:
                        flag = False
                    for k in ["_up", "_shadow"]:
                        try:
                            if url.split("/")[-1]+"_00"+k not in known_assets:
                                self.head(url + "_00" + k + ".png")
                                l.append(url.split("/")[-1]+"_00"+k)
                        except:
                            pass
                    err = 0
                    i = 1
                    while i < 100 and err < 10:
                        k = str(i).zfill(2)
                        try:
                            if url.split("/")[-1]+"_"+k not in known_assets:
                                self.head(url + "_" + k + ".png")
                                l.append(url.split("/")[-1]+"_"+k)
                            err = 0
                            for kk in ["_a", "_b", "_c", "_d", "_e", "_f", "_g", "_h", "_i", "_j", "_k", "_l", "_m", "_n", "_o", "_p", "_q", "_r", "_s", "_t", "_u", "_v", "_w", "_x", "_y", "_z"]:
                                try:
                                    if url.split("/")[-1]+"_"+k+kk not in known_assets:
                                        self.head(url + "_" + k + kk + ".png")
                                        l.append(url.split("/")[-1]+"_"+k+kk)
                                except:
                                    break
                        except:
                            err += 1
                        i += 1
        return ev, l

    # Check if an event got skycompass art. Note: The event must have a valid thumbnail ID set
    async def update_event_sky(self, ev : str):
        known = set(self.data['events'][ev][self.EVENT_SKY])
        evid = self.data['events'][ev][self.EVENT_THUMB]
        try:
            i = max(self.data['events'][ev][self.EVENT_SKY]) + 1
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
            self.data['events'][ev][self.EVENT_SKY] = known

    # -eventedit CLI
    async def event_edit(self):
        while True:
            print("\n[EDIT EVENT MENU]")
            print("[0] Stats")
            print("[1] Set Thumbnails")
            print("[2] Update Events")
            print("[3] Update All Valid Events")
            print("[4] Update SkyCompass")
            print("[5] Add Events")
            print("[Any] Quit")
            s = input().lower()
            match s:
                case "0":
                    s = [0, 0, 0, 0]
                    for ev in self.data["events"]:
                        s[0] += 1
                        if self.data["events"][ev][self.EVENT_CHAPTER_COUNT] >= 0:
                            s[1] += 1
                            c = 0
                            for i in range(self.EVENT_OP, len(self.data["events"][ev])):
                                c += len(self.data["events"][ev][i])
                            if c > 0:
                                s[2] += 1
                                if self.data["events"][ev][self.EVENT_THUMB] is not None:
                                    s[3] += 1
                    print(s[0], "events in the data")
                    print(s[1], "are valid events")
                    print(s[2], "got exclusive arts")
                    print(s[3], "got thumbnail")
                case "1":
                    for ev in self.data["events"]:
                        if self.data["events"][ev][self.EVENT_CHAPTER_COUNT] >= 0:
                            if self.data["events"][ev][self.EVENT_THUMB] is None:
                                c = 0
                                for i in range(self.EVENT_OP, len(self.data["events"][ev])):
                                    c += len(self.data["events"][ev][i])
                                if c > 0:
                                    s = input("Input a thumbnail ID or URL for Event "+ev+" (Leave blank to skip):")
                                    if s != "":
                                        try:
                                            if s.startswith("http"):
                                                self.data["events"][ev][self.EVENT_THUMB] = int(s.split('/')[-1].split('.')[0])
                                            else:
                                                self.data["events"][ev][self.EVENT_THUMB] = int(s)
                                            self.modified = True
                                            await self.update_event_sky(ev)
                                        except:
                                            pass
                    self.save()
                case "2":
                    s = input("Input a list of Event date (Leave blank to cancel):")
                    if s != "":
                        await self.update_event(s.split(" "), full=True)
                case "3":
                    l = []
                    for ev in self.data["events"]:
                        if self.data["events"][ev][self.EVENT_CHAPTER_COUNT] >= 0:
                            l.append(ev)
                    await self.update_event(l)
                case "4":
                    tasks = []
                    async with asyncio.TaskGroup() as tg:
                        c = 0
                        for ev in self.data["events"]:
                            if self.data["events"][ev][self.EVENT_THUMB] is not None:
                                tasks.append(tg.create_task(self.update_event_sky(ev)))
                        print("Checking", len(tasks), "event(s)...")
                    for t in tasks: t.result()
                    print("\nDone.")
                    self.save()
                case "5":
                    while True:
                        s = input("Input a list of Event date or a combo date:thumbnail (Leave blank to cancel):")
                        if s != "":
                            th = None
                            if ":" in s:
                                s = s.split(':')
                                th = s[1]
                                s = s[0]
                            if s not in self.data["events"]:
                                self.data["events"][s] = [-1, th, [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
                                self.modified = True
                            elif th is not None:
                                self.data["events"][s][self.EVENT_THUMB ] = th
                                self.modified = True
                        else:
                            break
                    self.save()
                case _:
                    break

    # Attempt to automatically associate new event thumbnails to events
    async def event_thumbnail_association(self, events : list):
        print("Checking event thumbnails...")
        in_use = set()
        for eid, ev in self.data["events"].items():
            if ev[1] is not None: in_use.add(str(ev[1]))
        in_use = list(in_use)
        in_use.sort()
        for eid in in_use:
            if eid not in self.data["eventthumb"]:
                self.modified = True
                self.data["eventthumb"][eid] = 1
        tasks = []
        async with asyncio.TaskGroup() as tg:
            self.progress = Progress(total=40, silent=False)
            for i in range(20):
                tasks.append(tg.create_task(self.event_thumbnail_association_sub(7001, 9000, 20)))
                tasks.append(tg.create_task(self.event_thumbnail_association_sub(9001, 10000, 20)))
        for t in tasks:
            t.result()
        new = []
        for eid, ev in self.data["eventthumb"].items():
            if ev == 0: new.append(int(eid))
        new.sort()
        if len(new) > 0:
            print(len(new), "event thumbnails")
            if len(new) == len(events):
                print("Matching to new events...")
                for i in range(len(new)):
                    self.data["events"][str(events[i])][self.EVENT_THUMB] = new[i]
                    self.data["eventthumb"][str(new[i])] = 1
                    self.update_event_sky(str(events[i]))
                    self.modified = True
                print("Please make sure they have been set to their correct events")
            else:
                print("Can't match new events to new thumbnails with certainty, -eventedit is required")
        print("Done")
        self.save()

    # event_thumbnail_association subroutine()
    async def event_thumbnail_association_sub(self, start : int, end : int, step : int):
        with self.progress:
            err = 0
            i = start
            while err < 10 and i < end:
                try:
                    f = "{}0".format(i)
                    if f not in self.data["eventthumb"]:
                        await self.head(self.IMG + "sp/archive/assets/island_m2/{}.png".format(f))
                        self.data["eventthumb"][f] = 0
                        self.modified = True
                    err = 0
                except:
                    err += 1
                i += step

    ### Partners ################################################################################################################

    # Called by -partner. Make a list of partners and potential partners to update. VERY slow.
    async def update_all_partner(self):
        t = self.update_changelog
        self.update_changelog = False
        ids = list(self.data.get('partners', {}).keys())
        for id in self.data.get('characters', {}):
            if 'st' in id: continue
            ids.append("38" + id[2:])
        await self.manualUpdate(ids)
        self.update_changelog = t

    ### Buffs ###################################################################################################################

    # Check buff data for new icons
    async def update_buff(self):
        tmp = self.update_changelog
        self.update_changelog = False
        tasks = []
        async with asyncio.TaskGroup() as tg:
            self.progress = Progress(total=10*10, silent=False)
            for i in range(10):
                for j in range(10):
                    tasks.append(tg.create_task(self.search_buff(1000*i+j, 10, True)))
        for t in tasks:
            t.result()
        print("Done")
        self.save()
        self.update_changelog = tmp

    ### Others ##################################################################################################################

    # Request the current GBF version or possible maintenance state
    async def gbfversion(self):
        try:
            res = await self.get('https://game.granbluefantasy.jp/', headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36', 'Accept-Language':'en', 'Host':'game.granbluefantasy.jp', 'Connection':'keep-alive'})
            res = res.decode('utf-8')
            return int(self.VERSION_REGEX.findall(res)[0])
        except:
            try:
                if 'maintenance' in res.lower(): return "maintenance"
            except:
                pass
            return None

    # Wait for an update to occur
    async def wait(self):
        v = await self.gbfversion()
        if v is None:
            print("Impossible to currently access the game.\nWait and try again.")
            return False
        elif v == "maintenance":
            print("Game is in maintenance")
            return False
        print("Waiting an update, ctrl+C to cancel...")
        try:
            while True:
                t = int(datetime.now(timezone.utc).replace(tzinfo=None).timestamp()) % 300
                if 300 - t > 10:
                    await asyncio.sleep(10)
                else:
                    await asyncio.sleep(310 - t)
                    n = await self.gbfversion()
                    if isinstance(n, int) and n != v:
                        print("Update detected.")
                        return True
        except:
            print("Cancelled...")
            return False

    # Print the help
    def print_help(self):
        print("Usage: python updater.py [START] [MODE]")
        print("")
        print("START parameters (Optional):")
        print("-wait        : Wait an in-game update before running.")
        print("-nochange    : Disable the update of changelog.json.")
        print("")
        print("MODE parameters (One at a time):")
        print("-run         : Update the data with new content.")
        print("-update      : Manual data update (Followed by IDs to check).")
        print("-updaterun   : Like '-update' but also do '-run' after.")
        print("-job         : Search for MC jobs (Time consuming).")
        print("-jobedit     : Job CLI.")
        print("-lookup      : Force update the lookup table (Time Consuming).")
        print("-lookupfix   : Lookup CLI.")
        print("-relation    : Update the relationship index.")
        print("-relinput    : Relation CLI.")
        print("-scenenpc    : Update scene index for every npcs (Time consuming).")
        print("-scenechara  : Update scene index for every characters (Time consuming).")
        print("-sceneskin   : Update scene index for every skins (Time consuming).")
        print("-scenefull   : Update scene index for every characters/skins/npcs (Very time consuming).")
        print("-scenesort   : Sort indexed scene data  for every characters/npcs.")
        print("-thumb       : Update npc thumbnail data.")
        print("-sound       : Update sound index for characters (Very time consuming).")
        print("-partner     : Update data for partner characters (Very time consuming).")
        print("-event       : Update unique event arts (Very time consuming).")
        print("-eventedit   : Edit event data")
        print("-buff        : Update buff data")

    async def boot(self, argv : list):
        try:
            print("GBFAL updater v2.2\n")
            self.client = aiohttp.ClientSession()
            start_flags = set(["-debug_scene", "-debug_wpn", "-wait", "-nochange"])
            flags = set()
            extras = []
            for i, k in enumerate(argv):
                if k in start_flags:
                    flags.add(k) # continue...
                elif k.startswith("-"):
                    flags.add(k)
                    extras = argv[i+1:]
                    break
                else:
                    print("Unknown parameter:", k)
                    return
            ran = False
            forced_stop = False
            if "-debug_scene" in flags:
                ran = True
                await self.debug_output_scene_strings()
            if "-debug_wpn" in flags: self.debug_wpn = True
            if "-wait" in flags: forced_stop = not (await self.wait())
            if "-nochange" in flags: self.update_changelog = False
            
            if not forced_stop:
                if len(flags) == 0:
                    self.print_help()
                elif "-run" in flags: await self.run()
                elif "-updaterun" in flags:
                    await self.manualUpdate(extras)
                    await self.run()
                elif "-update" in flags: await self.manualUpdate(extras)
                elif "-job" in flags: await self.search_job_detail()
                elif "-jobedit" in flags: await self.edit_job()
                elif "-lookup" in flags: await self.buildLookup()
                elif "-lookupfix" in flags: await self.manualLookup()
                elif "-relation" in flags: await self.build_relation()
                elif "-relinput" in flags: await self.relation_edit()
                elif "-scenenpc" in flags: await self.update_all_scene("npcs", extras)
                elif "-scenechara" in flags: await self.update_all_scene("characters", extras)
                elif "-sceneskin" in flags: await self.update_all_scene("skins", extras)
                elif "-scenefull" in flags: await self.update_all_scene(None, extras)
                elif "-scenesort" in flags: self.sort_all_scene()
                elif "-thumb" in flags: await self.update_npc_thumb()
                elif "-sound" in flags: await self.update_all_sound()
                elif "-partner" in flags: await self.update_all_partner()
                elif "-event" in flags: await self.check_new_event()
                elif "-eventedit" in flags: await self.event_edit()
                elif "-buff" in flags: await self.update_buff()
                elif not ran:
                    self.print_help()
                    print("")
                    print("Unknown parameter:", k)
            await self.client.close()
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            try: await self.client.close()
            except: pass

    def start(self, argv : list):
        asyncio.run(self.boot(argv))

if __name__ == "__main__":
    Updater().start(sys.argv[1:])