import asyncio
import aiohttp
import sys
import re
import json
import time
import string
import html
import os
import signal
from datetime import datetime, timezone, timedelta
import traceback
from typing import Optional, Callable, Collection, AsyncIterator, Iterator, Any, Union

# progress bar class
class Progress():
    def __init__(self, parent : 'Updater', *, total : int = 9999999999999, silent : bool = True, current : int = 0) -> None: # set to silent with a high total by default
        self.silent = silent
        self.total = total
        self.current = current - 1
        self.start_time = time.time()
        self.elapsed = self.start_time
        self.parent = parent
        if self.total > 0: self.update()

    def set(self, *, total : int = 0, silent : bool = False) -> None: # to initialize it after a task start, once we know the total
        if total >= 0:
            self.total = total
        self.silent = silent
        if not self.silent and self.total > 0:
            sys.stdout.write("\rProgress: {:.2f}%      ".format(100 * self.current / float(self.total)).replace('.00', ''))
            sys.stdout.flush()

    def update(self) -> None: # to call to update the progress text (if not silent and not done)
        if self.current < self.total:
            self.current += 1
            if self.parent is not None and time.time() - self.elapsed >= 3600: # 1h passed, autosave (if set)
                if self.silent:
                    sys.stdout.write("\r")
                else:
                    print("\rState: {}/{} - Autosaving...".format(self.current, self.total))
                self.elapsed = time.time()
                self.parent.save()
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
    MAX_NEW = 80
    MAX_UPDATE = 80
    MAX_HTTP = 90
    MAX_UPDATEALL = MAX_HTTP+10
    MAX_HTTP_WIKI = 20
    MAX_SCENE_CONCURRENT = 10
    SOUND_CONCURRENT_PER_STEP = 4
    LOOKUP_TYPES = ['characters', 'summons', 'weapons', 'job', 'skins', 'npcs']
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
    PREEMPTIVE_ADD = set(["characters", "enemies", "summons", "skins", "weapons", "partners", "npcs", "background"])
    ADD_SINGLE_ASSET = ["title", "subskills", "suptix"]
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
    # MC update
    JOB_ID = 0
    JOB_ALT = 1
    JOB_DETAIL = 2
    JOB_DETAIL_ALT = 3
    JOB_DETAIl_ALL = 4
    JOB_SD = 5
    JOB_MH = 6
    JOB_SPRITE = 7
    JOB_PHIT = 8
    JOB_SP = 9
    # summon update
    SUM_GENERAL = 0
    SUM_CALL = 1
    SUM_DAMAGE = 2
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
    EVENT_UPDATE_COUNT = 20
    # story update
    STORY_CONTENT = 0
    STORY_UPDATE_COUNT = 10
    # common to story, event
    SCENE_UPDATE_STEP = 5
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
    CHAPTER_REGEX = re.compile("Chapter (\d+)(-(\d+))?")
    # others
    SAVE_VERSION = 1
    LOAD_EXCLUSION = ['version']
    QUEUE_KEY = ['scene_queue', 'sound_queue']
    STRING_CHAR = string.ascii_lowercase + string.digits
    MISSING_EVENTS = ["201017", "211017", "221017", "231017", "241017", "200214", "210214", "220214", "230214", "240214", "200314", "210316", "220304", "220313", "230303", "230314", "240305", "240312", "201216", "211216", "221216", "231216", "241216", "200101", "210101", "220101", "230101", "240101"] + ["131201", "140330", "160430", "161031", "161227", "170501", "170801", "171129", "180301", "180310", "180403", "180428", "180503", "180603", "180623", "180801", "180813", "181214", "190310", "190427", "190801", "191004", "191222", "200222", "200331", "200801", "201209", "201215", "201222", "210222", "210303", "210310", "210331", "210801", "210824", "210917", "220105", "220222", "220520", "220813", "230105", "230209", "230222", "230331", "230429", "230616", "230813", "220307", "210303", "190307", "231215", "231224", "240107", "240222", "240331", "200304"]
    CUT_CONTENT = ["2040145000","2040146000","2040147000","2040148000","2040149000","2040150000","2040151000","2040152000","2040153000","2040154000","2040200000","2020001000"] # beta arcarum ids
    SHARED_NAMES = [["2030081000", "2030082000", "2030083000", "2030084000"], ["2030085000", "2030086000", "2030087000", "2030088000"], ["2030089000", "2030090000", "2030091000", "2030092000"], ["2030093000", "2030094000", "2030095000", "2030096000"], ["2030097000", "2030098000", "2030099000", "2030100000"], ["2030101000", "2030102000", "2030103000", "2030104000"], ["2030105000", "2030106000", "2030107000", "2030108000"], ["2030109000", "2030110000", "2030111000", "2030112000"], ["2030113000", "2030114000", "2030115000", "2030116000"], ["2030117000", "2030118000", "2030119000", "2030120000"], ["2040236000", "2040313000", "2040145000"], ["2040237000", "2040314000", "2040146000"], ["2040238000", "2040315000", "2040147000"], ["2040239000", "2040316000", "2040148000"], ["2040240000", "2040317000", "2040149000"], ["2040241000", "2040318000", "2040150000"], ["2040242000", "2040319000", "2040151000"], ["2040243000", "2040320000", "2040152000"], ["2040244000", "2040321000", "2040153000"], ["2040245000", "2040322000", "2040154000"], ["1040019500", '1040008000', '1040008100', '1040008200', '1040008300', '1040008400'], ["1040112400", '1040107300', '1040107400', '1040107500', '1040107600', '1040107700'], ["1040213500", '1040206000', '1040206100', '1040206200', '1040206300', '1040206400'], ["1040311500", '1040304900', '1040305000', '1040305100', '1040305200', '1040305300'], ["1040416400", '1040407600', '1040407700', '1040407800', '1040407900', '1040408000'], ["1040511800", '1040505100', '1040505200', '1040505300', '1040505400', '1040505500'], ["1040612300", '1040605000', '1040605100', '1040605200', '1040605300', '1040605400'], ["1040709500", '1040704300', '1040704400', '1040704500', '1040704600', '1040704700'], ["1040811500", '1040804400', '1040804500', '1040804600', '1040804700', '1040804800'], ["1040911800", '1040905000', '1040905100', '1040905200', '1040905300', '1040905400'], ["2040306000","2040200000"]]
    SPECIAL_LOOKUP = { # special elements
        "3020065000": "R brown poppet trial",
        "3030158000": "SR blue poppet trial",
        "3040097000": "SSR sierokarte trial",
        "2030004000": "fire SR cut-content",
        "2030014000": "dark SR cut-content",
        "2020001000": "earth SR goblin cut-content",
        "3040114000": "SSR cut-content",
        # missing skins
        "3710196000": "cassius parasol and hakama of prosperity",
        "3710117000": "meteon a comet's calm",
        "3710183000": "young cat black with golden eyes",
        "3710184000": "young cat ginger tabby",
        "3710182000": "young cat milky white shorthair",
        "3710015000": "lina"
    }
    MALINDA = "3030093000"
    PARTNER_STEP = 10
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
    # scene string
    SCENE_MC_ID = set(["3990219000", "3990220000"])
    SCENE_BASE = ["", "_a", "_b", "_c", "_m", "_nalhe", "_school", "_astral", "_battle", "_knife", "_off", "_race", "_guardian", "_cook", "_orange", "_muffler", "_cigarette", "_face", "_mask", "_halfmask", "_girl", "_town", "_two", "_three", "_2022", "_2023", "_2024"]
    SCENE_BASE_MC = SCENE_BASE + ["_monk", "_dancer", "_mechanic", "_lumberjack", "_robinhood", "_horse", "_cavalry", "_manadiver", "_eternals", "_eternals2"]
    SCENE_EXPRESSIONS = ["", "_a", "_b", "_c", "_d", "_e", "_f", "_g", "_1", "_2", "_3", "_4", "_5", "_6", "_up", "_laugh", "_laugh2", "_laugh3", "_laugh4", "_laugh5", "_laugh6", "_laugh7", "_laugh8", "_laugh9", "_wink", "_wink2", "_shout", "_shout2", "_shout3", "_leer", "_sad", "_sad2",  "_sad3","_angry", "_angry2", "_angry3", "_angry4", "_fear", "_fear2", "_cry", "_cry2", "_painful", "_painful2", "_shadow", "_shadow2", "_shadow3", "_light", "_close", "_serious", "_serious2", "_serious3", "_serious4", "_serious5", "_serious6", "_serious7", "_serious8", "_serious9", "_serious10", "_serious11", "_surprise", "_surprise2", "_surprise3", "_surprise4", "_think", "_think2", "_think3", "_think4", "_think5", "_serious", "_serious2", "_mood", "_mood2", "_mood3", "_badmood", "_badmood2", "_ecstasy", "_ecstasy2", "_suddenly", "_suddenly2", "_speed2", "_shy", "_shy2", "_weak", "_weak2", "_sleep", "_sleepy", "_open", "_bad", "_bad2", "_amaze", "_amaze2", "_amezed", "_joy", "_joy2", "_pride", "_pride2", "_intrigue", "_intrigue2", "_pray", "_motivation", "_melancholy", "_concentration", "_mortifying", "_hot", "_cold", "_cold2", "_cold3", "_cold4", "_weapon", "_hood", "_letter", "_child1", "_child2", "_gesu", "_gesu2", "_stump", "_stump2", "_doya", "_chara", "_fight", "_2022", "_2023", "_2024", "_all", "_all2", "_pinya", "_ef", "_ef_left", "_ef_right", "_ef2", "_body", "_front", "_head", "_up_head", "_foot", "_back", "_left", "_right", "_move", "_move2", "_small", "_big", "_pair_1", "_pair_2", "_break", "_break2", "_break3", "_ghost", "_two", "_three", "_beppo", "_beppo_jiji", "_jiji", "_foogee", "_foogee_nicola", "_nicola", "_momo", "_all2", "_eyeline"]
    SCENE_VARIATIONS = ["", "_a", "_b", "_b1", "_b2", "_b3", "_speed", "_line", "_up", "_up_speed", "_up_line", "_up2", "_up3", "_up4", "_down", "_shadow", "_shadow2", "_shadow3", "_light", "_up_light", "_vanish", "_vanish1", "_vanish2", "_blood", "_up_blood"]
    SCENE_CHECK = list(set(SCENE_BASE_MC + SCENE_EXPRESSIONS + SCENE_VARIATIONS))
    SCENE_VARIATIONS_SET = set(SCENE_VARIATIONS)
    SCENE_SPECIAL = ["_light_heart", "_jewel", "_jewel2", "_thug", "_uncontroll", "_narrator", "_birthday", "_birthday1", "_birthday2", "_birthday3", "_birthday4", "_birthday5", "_valentine", "_valentine2", "_valentine3", "_white", "_whiteday", "_whiteday1", "_whiteday2", "_whiteday3"]
    SCENE_BUBBLE_FILTER = set(["b1", "b2", "b3", "speed", "line", "up", "up2", "up3", "up4", "down", "shadow", "shadow2", "shadow3", "light", "vanish", "vanish1", "vanish2", "blood"])
    def __init__(self) -> None:
        # main variables
        self.update_changelog = True # flag to enable or disable the generation of changelog.json
        self.debug_wpn = False # for testing
        self.debug_npc_detail = False # set to true for better detection
        self.data = { # data structure
            "version":self.SAVE_VERSION,
            "scene_queue":[],
            "sound_queue":[],
            "valentines":[],
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
            "eventthumb":{},
            "story":{}
        }
        self.load() # load self.data NOW
        self.modified = False # if set to true, data.json will be written on the next call of save()
        self.new_elements = [] # new indexed element
        self.addition = {} # new elements for changelog.json
        self.job_list = None
        self.scene_strings = None # contains list of suffix
        self.scene_strings_special = None # contains list of suffix
        self.force_partner = False # set to True by -partner
        
        # asyncio semaphores
        self.sem = asyncio.Semaphore(self.MAX_UPDATE) # update semaphore
        self.http_sem = asyncio.Semaphore(self.MAX_HTTP) # http semaphore
        self.wiki_sem = asyncio.Semaphore(self.MAX_HTTP_WIKI) # wiki request semaphor
        
        # others
        self.run_count = 0
        self.progress = Progress(self) # initialized with a silent progress bar
        self.use_wiki = True # if True, use wiki features
        
        self.client = None # will contain the aiohttp client. Is initialized at startup or must be initialized by a third party.
        # CTRL+C signal
        try: # unix
            self.loop.add_signal_handler(signal.SIGINT, self.interrupt)
        except: # windows
            signal.signal(signal.SIGINT, self.interrupt)

    def interrupt(self, signum : int, frame) -> None:
        print("")
        print("Process PAUSED")
        if self.progress is not None and self.progress.total != 9999999999999:
            print("State: {}/{}".format(self.progress.current, self.progress.total))
        print("Type 'save' to save, type 'exit' to force an exit, anything else to continue")
        while True:
            s = input(":").lower()
            match s:
                case 'save':
                    if not self.modified:
                        print("No changes waiting to be saved")
                    else:
                        self.save()
                case 'exit':
                    print("Exiting...")
                    os._exit(0)
                case _:
                    print("Process RESUMING...")
                    break

    ### Utility #################################################################################################################

    # Load data.json
    def load(self) -> None:
        try:
            with open('json/data.json', mode='r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict): return
            data = self.retrocompatibility(data)
            for k in self.data:
                if k in self.LOAD_EXCLUSION: continue
                elif k in data: self.data[k] = data[k]
        except Exception as e:
            if not str(e).startswith("[Errno 2] No such file or directory"):
                print("The following error occured while loading data.json:")
                print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
                print(e)
                os._exit(0)

    # make older data.json compatible with newer versions
    def retrocompatibility(self, data : dict) -> dict:
        #version = data.get("version", 0)
        # Does nothing for now
        return data

    # Save data.json and changelog.json (only if self.modified is True)
    def save(self) -> None:
        try:
            if self.modified:
                self.modified = False
                # data.json
                for k in self.QUEUE_KEY:
                    self.data[k] = list(set(self.data[k]))
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
                # changelog.json
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
                if self.update_changelog:
                    for k, v in self.addition.items(): # merge but put updated elements last
                        if k in existing: existing.pop(k)
                        existing[k] = v
                    self.addition = {} # clear self.addition
                new = []
                for k, v in existing.items(): # convert back to list. NOTE: maybe make a cleaner way later
                    new.append([k, v])
                if len(new) > self.MAX_NEW: new = new[len(new)-self.MAX_NEW:]
                with open('json/changelog.json', mode='w', encoding='utf-8') as outfile:
                    json.dump({'timestamp':int(datetime.now(timezone.utc).timestamp()*1000), 'new':new, 'issues':issues}, outfile)
                if self.update_changelog: print("data.json and changelog.json updated")
                else: print("data.json updated")
        except Exception as e:
            print(e)
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    # Generic GET request function
    async def get(self, url : str, headers : dict = {}, timeout : Optional[int] = None, get_json : bool = False):
        async with self.http_sem:
            response = await self.client.get(url, headers={'connection':'keep-alive'} | headers, timeout=timeout)
            async with response:
                if response.status != 200: raise Exception("HTTP error {}".format(response.status))
                if get_json: return await response.json()
                return await response.content.read()
    
    # Generic HEAD request function
    async def head(self, url : str, headers : dict = {}):
        async with self.http_sem:
            response = await self.client.head(url, headers={'connection':'keep-alive'} | headers)
            async with response:
                if response.status != 200: raise Exception("HTTP error {}".format(response.status))
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

    # test if the wiki is usable
    async def test_wiki(self) -> bool:
        try:
            t = (await self.get("https://gbf.wiki", headers={'User-Agent':self.USER_AGENT}, timeout=5)).decode('utf-8')
            if "<p id='status'>50" in t or 'gbf.wiki unavailable' in t: return False
            return True
        except:
            return False

    # Create a shared container for tasks.
    def newShared(self, errs : list) -> list:
        errs.append([0, True, 0])
        return errs[-1]

    # Extract json data from a manifest file
    async def processManifest(self, file : str, verify_file : bool = False) -> list:
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

    # for limited queued asyncio concurrency
    async def map_unordered(self, func : Callable, iterable : Union[Iterator,Collection,AsyncIterator], limit : int) -> asyncio.Task:
        aws = iter(map(func, iterable))

        aws_ended = False
        pending = set()

        while pending or not aws_ended:
            while len(pending) < limit and not aws_ended:
                try:
                    aw = next(aws)
                except StopIteration:
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
    async def run(self, ids : list = []) -> None:
        self.new_elements = ids
        self.run_count = 0
        categories = []
        errs = []
        job_task = 10
        skill_task = 10
        buff_series_task = 12
        # job keys to check
        jkeys = []
        if self.job_list is None:
            self.job_list = await self.init_job_list()
        if self.job_list is None:
            print("Couldn't retrieve job list from the game")
            return
        for k in list(self.job_list.keys()):
            if k not in self.data['job']:
                jkeys.append(k)
        if len(jkeys) > 0:
            job_task == 0
        # jobs
        categories.append([])
        self.newShared(errs)
        for i in range(job_task):
            categories[-1].append(self.search_job(i, job_task, jkeys, errs[-1]))
        # skills
        for i in range(skill_task):
            categories.append([self.search_skill(i, skill_task)])
        # buffs
        for i in range(10):
            for j in range(buff_series_task):
                categories.append([self.search_buff(1000*i+j, buff_series_task)])
        # npc
        categories.append([])
        self.newShared(errs)
        for i in range(10): # assets
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "img/sp/quest/scene/character/body/", ".png",  70))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # assets
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "img/sp/raid/navi_face/", ".png",  50))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # assets
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "img/sp/quest/scene/character/body/", "_a.png",  50))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # assets
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "img/sp/assets/npc/b/", "_01.png",  70))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # sounds
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "sound/voice/", "_v_001.mp3",  50))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # boss sounds
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "sound/voice/", "_boss_v_1.mp3",  50))
        # special
        categories.append([])
        categories[-1].append(self.search_generic('npcs', 0, 1, self.newShared(errs), "305{}000", 4, "img/sp/quest/scene/character/body/", ".png",  2))
        #rarity of various stuff
        for r in range(1, 5):
            # weapons
            for j in range(10):
                categories.append([])
                self.newShared(errs)
                for i in range(5):
                    categories[-1].append(self.search_generic('weapons', i, 5, errs[-1], "10"+str(r)+"0{}".format(j) + "{}00", 3, "img/sp/assets/weapon/m/", ".jpg",  20))
            # summons
            categories.append([])
            self.newShared(errs)
            for i in range(5):
                categories[-1].append(self.search_generic('summons', i, 5, errs[-1], "20"+str(r)+"0{}000", 3, "js/model/manifest/summon_", "_01_damage.js",  20))
            if r > 1:
                # characters
                categories.append([])
                self.newShared(errs)
                for i in range(5):
                    categories[-1].append(self.search_generic('characters', i, 5, errs[-1], "30"+str(r)+"0{}000", 3, "img/sp/assets/npc/m/", "_01.jpg", 20))
                # partners
                categories.append([])
                self.newShared(errs)
                for i in range(5):
                    categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "img/sp/assets/npc/raid_normal/", "_01.jpg",  20))
                categories.append([])
                self.newShared(errs)
                for i in range(5):
                    categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/phit_", ".js",  20))
                categories.append([])
                self.newShared(errs)
                for i in range(5):
                    categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/nsp_", "_01.js",  20))
        # other partners
        for r in range(8, 10):
            categories.append([])
            self.newShared(errs)
            for i in range(5):
                categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "img/sp/assets/npc/raid_normal/", "_01.jpg",  20))
            categories.append([])
            self.newShared(errs)
            for i in range(5):
                categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/phit_", ".js",  20))
            categories.append([])
            self.newShared(errs)
            for i in range(5):
                categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/nsp_", "_01.js",  20))
        # skins
        categories.append([])
        self.newShared(errs)
        for i in range(5):
            categories[-1].append(self.search_generic('skins', i, 5, errs[-1], "3710{}000", 3, "js/model/manifest/npc_", "_01.js",  20))
        # enemies
        for a in range(1, 10):
            for b in range(1, 4):
                for d in [1, 2, 3]:
                    categories.append([])
                    self.newShared(errs)
                    for i in range(5):
                        categories[-1].append(self.search_generic('enemies', i, 5, errs[-1], str(a) + str(b) + "{}" + str(d), 4, "img/sp/assets/enemy/s/", ".png",  50))
        # backgrounds
        # event & common
        for i in ["event_{}", "common_{}"]:
            categories.append([])
            self.newShared(errs)
            for j in range(5):
                categories[-1].append(self.search_generic('background', j, 5, errs[-1], i, 3 if i.startswith("common_") else 1, "img/sp/raid/bg/", ".jpg",  10))
        # main
        categories.append([])
        self.newShared(errs)
        for j in range(5):
            categories[-1].append(self.search_generic('background', j, 5, errs[-1], "main_{}", 1, "img/sp/guild/custom/bg/", ".png",  10))
        # others
        for i in ["ra", "rb", "rc"]:
            categories.append([])
            self.newShared(errs)
            for j in range(5):
                categories[-1].append(self.search_generic('background', j, 5, errs[-1], "{}"+i, 1, "img/sp/raid/bg/", "_1.jpg",  50))
            break
        for i in [("e", ""), ("e", "r"), ("f", ""), ("f", "r"), ("f", "ra"), ("f", "rb"), ("f", "rc"), ("e", "r_3_a"), ("e", "r_4_a")]:
            categories.append([])
            self.newShared(errs)
            for j in range(5):
                categories[-1].append(self.search_generic('background', j, 5, errs[-1], i[0]+"{}"+i[1], 3, "img/sp/raid/bg/", "_1.jpg",  50))
        # titles
        categories.append([])
        self.newShared(errs)
        for i in range(3):
            categories[-1].append(self.search_generic('title', i, 3, errs[-1], "{}", 1, "img/sp/top/bg/bg_", ".jpg",  5))
        # subskills
        categories.append([])
        self.newShared(errs)
        for i in range(3):
            categories[-1].append(self.search_generic('subskills', i, 3, errs[-1], "{}", 1, "img/sp/assets/item/ability/s/", "_1.jpg",  5))
        # suptix
        categories.append([])
        self.newShared(errs)
        for i in range(3):
            categories[-1].append(self.search_generic('suptix', i, 3, errs[-1], "{}", 1, "img/sp/gacha/campaign/surprise/top_", ".jpg",  15))
        print("Starting process...")
        self.progress = Progress(self, total=len(categories), silent=False)
        async with asyncio.TaskGroup() as tg:
            tasks = []
            for c in categories:
                tasks.append(tg.create_task(self.run_category(c)))
        for t in tasks:
            t.result()
        self.save()
        if len(self.new_elements) > 0:
            await self.manualUpdate(self.new_elements)
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            if today.month != tomorrow.month: # check missing npcs monthly
                await self.missing_npcs()
            await self.check_msq()
            await self.check_new_event()
            await self.update_npc_thumb()
        else:
            if len(self.data['scene_queue']) > 0:
                await self.update_all_scene(update_pending=True)
            if len(self.data['sound_queue']) > 0:
                await self.update_all_sound(update_pending=True)

    # run subroutine, process a category batch
    async def run_category(self, coroutines : list) -> None:
        with self.progress:
            while True:
                if self.run_count + len(coroutines) <= self.MAX_HTTP:
                    self.run_count += len(coroutines)
                    break
                await asyncio.sleep(1)
            try:
                tasks = []
                async with asyncio.TaskGroup() as tg:
                    for i in range(len(coroutines)): # run the coroutines
                        tasks.append(tg.create_task(coroutines[i]))
                for t in tasks:
                    t.result()
            except Exception as e:
                print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            self.run_count -= len(coroutines)

    # generic asset search
    async def search_generic(self, index : str, start : int, step : int, err : list, file : str, zfill : int, path : str, ext : str, maxerr : int) -> None:
        i = start
        is_js = ext.endswith('.js')
        while err[0] < maxerr and err[1]:
            f = file.format(str(i).zfill(zfill))
            if f in self.data[index]:
                if self.data[index][f] == 0 and (is_js or index in self.PREEMPTIVE_ADD):
                    self.new_elements.append(f)
                err[0] = 0
                await asyncio.sleep(0.02)
            else:
                if len(f) == 10 and f.startswith("20"):
                    replaces = [None, ("_damage", "_a_damage")]
                else:
                    replaces = [None]
                for r in replaces:
                    try:
                        if r is not None: await self.head(self.ENDPOINT + path + f + ext.replace(r[0], r[1]))
                        else: await self.head(self.ENDPOINT + path + f + ext)
                        err[0] = 0
                        self.data[index][f] = 0
                        if index in self.ADD_SINGLE_ASSET:
                            self.addition[index+":"+f] = index
                        self.modified = True
                        self.new_elements.append(f)
                        break
                    except:
                        if r is replaces[-1]:
                            err[0] += 1
                            if err[0] >= maxerr:
                                err[1] = False
                                return
            i += step

    # -run subroutine to search for new skills
    async def search_skill(self, start : int, step : int) -> None: # skill search
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
    async def search_buff(self, start : int, step : int, full : bool = False) -> None: # buff search
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
        # suffix list
        slist = ["_1", "_10", "_11", "_101", "_110", "_111", "_30"] + (["1"] if start >= 1000 else []) + ["_1_1", "_2_1", "_0_10", "_1_10" "_1_20", "_2_10"]
        known = set()
        while err < 10 and i < end:
            fi = str(i).zfill(4)
            data = [[], []]
            if not full:
                if fi in self.data["buffs"]:
                    i += step
                    err = 0
                    continue
            else:
                try:
                    data[0] = self.data["buffs"][fi][0].copy()
                    data[1] = self.data["buffs"][fi][1].copy()
                    known = set(data[1])
                    if '_' not in data[0] and len(data[0]) < 5:
                        known.add("")
                except:
                    known = set()
            found = False
            modified = False
            # check no suffix
            try:
                if len(data[0]) == 0 or (len(data[0]) > 0 and data[0][0] != str(i)):
                    headers = await self.head(self.IMG + "sp/ui/icon/status/x64/status_" + str(i) + ".png")
                    if 'content-length' in headers and int(headers['content-length']) < 150: raise Exception()
                    data[0] = [str(i)]
                    modified = True
                found = True
            except:
                pass
            # check suffixes
            for s in slist:
                try:
                    if s not in known:
                        headers = await self.head(self.IMG + "sp/ui/icon/status/x64/status_" + str(i) + s + ".png")
                        if 'content-length' in headers and int(headers['content-length']) < 150: raise Exception()
                        if len(data[0]) == 0:
                            data[0] = [str(i)+s]
                        if s != "":
                            data[1].append(s)
                        modified = True
                    found = True
                except:
                    pass
            if not found:
                if i > highest:
                    err += 1
            else:
                err = 0
                if modified:
                    try:
                        if len(data[1]) != len(self.data["buffs"][fi][1]):
                            self.addition[fi] = self.ADD_BUFF
                    except:
                        self.addition[fi] = self.ADD_BUFF
                    self.data["buffs"][fi] = data
                    self.modified = True
            i += step

    ### Job #####################################################################################################################
    
    # To be called once when needed
    async def init_job_list(self) -> dict:
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
                job_list[r] = self.STRING_CHAR
        print("Done")
        return job_list

    # Subroutine for init_job_list
    async def init_job_list_sub(self, id : str) -> Optional[str]:
        try:
            await self.head(self.IMG + "sp/assets/leader/m/{}_01.jpg".format(id))
            return id
        except:
            return None

    # run subroutine to search for new jobs
    async def search_job(self, start : int, step : int, keys : list, shared : list) -> None:
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
                    data[self.JOB_ALT].append(keys[i][:-2]+str(j).zfill(2)+"_01")
                for k in range(2):
                    data[self.JOB_DETAIL].append(keys[i]+"_"+cmh[0]+"_"+str(k)+"_01")
                for j in [1]+alts:
                    for k in range(2):
                        data[self.JOB_DETAIL_ALT].append(keys[i][:-2]+str(j).zfill(2)+"_"+cmh[0]+"_"+str(k)+"_01")
                for j in colors:
                    for k in range(2):
                        data[self.JOB_DETAIl_ALL].append(keys[i][:-2]+str(j).zfill(2)+"_"+cmh[0]+"_"+str(k)+"_01")
                for j in colors:
                    data[self.JOB_SD].append(keys[i][:-2]+str(j).zfill(2))

                self.data['job'][keys[i]] = data
                self.modified = True
                self.addition[keys[i]] = self.ADD_JOB
            i += step
        if shared[1]:
            shared[1] = False

    # Used by -job, more specific but also slower job detection system
    async def search_job_detail(self, params : list) -> None:
        if self.job_list is None:
            self.job_list = await self.init_job_list()
        if self.job_list is None:
            print("Couldn't retrieve job list from the game")
            return
        print("Searching additional job data...")
        to_search = []
        full_key_search = len(params) > 0
        # key search
        for k, v in self.data['job'].items():
            if len(v[self.JOB_SPRITE]) == 0:
                if self.job_list[k] != self.STRING_CHAR:
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
        tasks = []
        for v in to_search:
            if v[0] == 0:
                tasks.append(self.detail_job_search(v[1], v[2]))
            elif v[0] == 1:
                tasks.append(self.detail_job_weapon_search(v[1]))
        # full key search
        if full_key_search:
            for a in self.STRING_CHAR:
                for b in self.STRING_CHAR:
                    for c in self.STRING_CHAR:
                        d = a+b+c
                        if d in self.data["job_key"]: continue
                        tasks.append(self.detail_job_search_single(d))
        self.progress = Progress(self, total=len(tasks), silent=False)
        async for result in self.map_unordered(self.search_job_detail_task, tasks, self.MAX_UPDATEALL):
            pass
        print("Done")
        self.save()

    # search_job_detail() subroutine
    async def search_job_detail_task(self, task) -> None:
        await task

    # search_job_detail() subroutine
    async def detail_job_search(self, key : str, job : str) -> None:
        with self.progress:
            cmh = self.data['job'][job][self.JOB_MH]
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
                        print("\nSet", job, "to", d)

    # search_job_detail() subroutine
    async def detail_job_weapon_search(self, wid : str) -> None:
        with self.progress:
            try:
                await self.head(self.IMG + '_low/sp/assets/weapon/m/' + wid + ".jpg")
                return
            except:
                pass
            for k in [["phit_", ""], ["phit_", "_2"], ["phit_", "_3"], ["sp_", "_s2"], ["sp_", ""]]:
                for g in ["", "_0"]:
                    try:
                        await self.head(self.MANIFEST + k[0] + wid + g + k[1] + ".js")
                        self.data["job_wpn"][wid] = None
                        self.modified = True
                        print("\nPossible job skin related weapon:", wid)
                        return
                    except:
                        pass

    # search_job_detail() subroutine
    async def detail_job_search_single(self, key : str) -> None:
        with self.progress:
            for mh in self.MAINHAND:
                try:
                    await self.processManifest("{}_{}_0_01".format(key, mh))
                    self.data["job_key"][key] = None
                    self.modified = True
                    print("\nUnknown job key", key, "for mh", mh)
                    break
                except:
                    pass

    # -jobedit CLI
    async def edit_job(self) -> None:
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
                                    for v in self.data['job'][jid][self.JOB_DETAIl_ALL]:
                                        try:
                                            sheets += await self.processManifest(s + "_" + '_'.join(v.split('_')[1:3]) + "_" + v.split('_')[0][-2:])
                                        except:
                                            pass
                                    self.data['job'][jid][self.JOB_SPRITE] = list(dict.fromkeys(sheets))
                                    self.data['job_key'][s] = jid
                                    self.modified = True
                                    print(len(sheets),"sprites set to job", jid)
                                elif s in self.data['job_wpn']:
                                    # phit
                                    sheets = []
                                    for u in ["", "_1", "_2", "_3"]:
                                        for g in ["", "_0", "_1"]:
                                            try:
                                                sheets += await self.processManifest("phit_{}{}{}".format(s, u, g))
                                            except:
                                                if g == "_0":
                                                    break
                                    sheets = list(set(sheets))
                                    sheets.sort()
                                    self.data['job'][jid][self.JOB_PHIT] = sheets
                                    # ougi
                                    sheets = []
                                    for u in ["", "_0", "_1", "_0_s2", "_1_s2", "_0_s3", "_1_s3"]:
                                        try:
                                            sheets += await self.processManifest("sp_{}{}".format(s, u))
                                        except:
                                            pass
                                    sheets = list(set(sheets))
                                    sheets.sort()
                                    self.data['job'][jid][self.JOB_SP] = sheets
                                    print(len(self.data['job'][jid][self.JOB_PHIT]),"attack sprites and",len(self.data['job'][jid][self.JOB_SP]),"ougi sprites set to job", jid)
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
                        if len(v[self.JOB_MH]) == 0:
                            print(k, "has no sprites")
                            tmp += 1
                        elif len(v[self.JOB_PHIT]) + len(v[self.JOB_SP]) == 0 and 4100 > int(k[:4]) > 3100:
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
                            tasks = []
                            for jid, s in tmp["lookup"].items():
                                # add job if needed
                                if jid not in self.data['job']:
                                    await self.search_job(0, 1, [jid], self.newShared([]))
                                if s is not None:
                                    tasks.append(self.edit_job_import_task(jid, s, 0))
                            for jid, s in tmp["weapon"].items():
                                if s is not None:
                                    tasks.append(self.edit_job_import_task(jid, s, 1))
                            res = True
                            for l in await asyncio.gather(*tasks):
                                res = res and l
                            if not res:
                                raise Exception("Check the log for details")
                            print("Job Data Import finished with success")
                        except Exception as e:
                            print("An error occured during the import")
                            print(e)
                            return
                case _:
                    break
            self.save()

    async def edit_job_import_task(self, jid : str, s : Any, mode : int) -> None:
        try:
            match mode:
                case 0:
                    # set key
                    sheets = []
                    for v in self.data['job'][jid][self.JOB_DETAIl_ALL]:
                        try:
                            sheets += await self.processManifest(s + "_" + '_'.join(v.split('_')[1:3]) + "_" + v.split('_')[0][-2:])
                        except:
                            pass
                    self.data['job'][jid][self.JOB_SPRITE] = list(dict.fromkeys(sheets))
                    self.data['job_key'][s] = jid
                    self.modified = True
                    print(len(sheets),"sprites set to job", jid)
                case 1:
                    # phit
                    sheets = []
                    for u in ["", "_1", "_2", "_3"]:
                        for g in ["", "_0", "_1"]:
                            try:
                                sheets += await self.processManifest("phit_{}{}{}".format(s, u, g))
                            except:
                                if g == "_0":
                                    break
                    sheets = list(set(sheets))
                    sheets.sort()
                    self.data['job'][jid][self.JOB_PHIT] = sheets
                    # ougi
                    sheets = []
                    for u in ["", "_0", "_1", "_0_s2", "_1_s2", "_0_s3", "_1_s3"]:
                        try:
                            sheets += await self.processManifest("sp_{}{}".format(s, u))
                        except:
                            pass
                    sheets = list(set(sheets))
                    sheets.sort()
                    self.data['job'][jid][self.JOB_SP] = sheets
                    print(len(self.data['job'][jid][self.JOB_PHIT]),"attack sprites and",len(self.data['job'][jid][self.JOB_SP]),"ougi sprites set to job", jid)
                    self.data['job_wpn'][s] = jid
                    self.modified = True
            return True
        except:
            return False

    ### Update ##################################################################################################################

    # Called by -update or other function when new content is detected
    async def manualUpdate(self, ids : list, skip : int = 0) -> None: # skip is only used for the -partner resume feature
        if len(ids) == 0:
            return
        ids = list(set(ids)) # remove dupes
        start_index = skip
        async with asyncio.TaskGroup() as tg:
            tasks = []
            remaining = 0
            self.progress = Progress(self, current=start_index)
            for id in ids:
                if id in self.data.get('background', {}):
                    if skip > 0: skip -= 1
                    else: tasks.append(tg.create_task(self.bgUpdate(id)))
                    remaining += 1
                elif len(id) >= 10:
                    if id.startswith('2'):
                        if skip > 0: skip -= 1
                        else: tasks.append(tg.create_task(self.sumUpdate(id)))
                    elif id.startswith('10'):
                        if skip > 0: skip -= 1
                        else: tasks.append(tg.create_task(self.weapUpdate(id)))
                    elif id.startswith('39') or id.startswith('305'):
                        if skip > 0: skip -= 1
                        else: tasks.append(tg.create_task(self.npcUpdate(id)))
                    elif id.startswith('38'):
                        try:
                            pid = int(id)
                            for i in range(self.PARTNER_STEP):
                                if skip > 0: skip -= 1
                                else: tasks.append(tg.create_task(self.partnerUpdate(str(pid+i), self.PARTNER_STEP))) # separate in multiple threads to speed up
                        except:
                            continue
                    elif id.startswith('3'):
                        if id == "3040114000": continue # cut content
                        if skip > 0: skip -= 1
                        else: tasks.append(tg.create_task(self.charaUpdate(id)))
                    else:
                        continue
                    remaining += 1
                elif len(id) == 7:
                    if skip > 0: skip -= 1
                    else: tasks.append(tg.create_task(self.mobUpdate(id)))
                    remaining += 1
            print("Attempting to update", remaining, "element(s)")
            self.progress.set(total=len(tasks)+start_index, silent=False)
        tsuccess = 0
        for t in tasks:
            if t.result():
                tsuccess += 1
        print(tsuccess, "positive result(s)")
        self.save()
        if len(self.data['scene_queue']) > 0:
            await self.update_all_scene(update_pending=True)
        if len(self.data['sound_queue']) > 0:
            await self.update_all_sound(update_pending=True)

    # Art check system for characters. Detect gendered arts, etc...
    async def artCheck(self, id : str, style : str, uncaps : list) -> dict:
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
    async def charaUpdate(self, id : str) -> bool:
        with self.progress:
            async with self.sem:
                index = "skins" if id.startswith("371") else "characters"
                data = [[], [], [], [], [], [], [], [], []] # sprite, phit, sp, aoe, single, general, sd, scene, sound
                if id in self.data[index] and self.data[index][id] != 0:
                    data[self.CHARA_SCENE] = self.data[index][id][self.CHARA_SCENE]
                    data[self.CHARA_SOUND] = self.data[index][id][self.CHARA_SOUND]
                for style in ["", "_st2"]:
                    uncaps = []
                    sheets = []
                    altForm = False
                    if index == "skins" and style != "": # skin & style check
                        break
                    # # # Main sheets
                    tid = self.CHARA_SPECIAL_REUSE.get(id, id) # special substitution (mostly for bobobo)
                    for uncap in ["01", "02", "03", "04"]:
                        for gender in ["", "_0", "_1"]:
                            for ftype in ["", "_s2", "_0", "_1"]:
                                for form in ["", "_f", "_f1", "_f2"]:
                                    try:
                                        fn = "npc_{}_{}{}{}{}{}".format(tid, uncap, style, gender, form, ftype)
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
                                    for af in (["", "_f", "_f1", "_f2"] if altForm else [""]):
                                        targets.append(base_fn + af + g + m + n)
                        # sprites
                        sd.append(base_fn)
                    data[self.CHARA_GENERAL] += targets
                    data[self.CHARA_SD] += sd
                    if len(targets) == 0:
                        if style == "": return False
                        continue
                    # # # Other sheets
                    # attack
                    targets = [""]
                    for i in range(1, len(uncaps)):
                        targets.append("_" + uncaps[i])
                    attacks = []
                    if tid == self.MALINDA:
                        for i in range(0, 7):
                            mid = tid[:-1] + str(i)
                            for t in targets:
                                for u in ["", "_2", "_3", "_4"]:
                                    for form in (["", "_f", "_f1", "_f2"] if altForm else [""]):
                                        try:
                                            fn = "phit_{}{}{}{}{}".format(mid, t, style, u, form)
                                            attacks += await self.processManifest(fn)
                                        except:
                                            pass
                    else:
                        for t in targets:
                            for u in ["", "_2", "_3", "_4"]:
                                for form in (["", "_f", "_f1", "_f2"] if altForm else [""]):
                                    try:
                                        fn = "phit_{}{}{}{}{}".format(tid, t, style, u, form)
                                        attacks += await self.processManifest(fn)
                                    except:
                                        pass
                    data[self.CHARA_PHIT] += attacks
                    # ougi
                    attacks = []
                    for uncap in uncaps:
                        if uncap not in flags:
                            print("")
                            print("Warning: Missing uncap art", uncap, "for character:", id)
                            continue
                        uf = flags[uncap]
                        found = False
                        for g in (["", "_0", "_1"] if (uf[0] is True) else [""]):
                            for form in (["", "_f", "_f1", "_f2"] if altForm else [""]):
                                for catype in ["", "_s2", "_s3"]:
                                    for sub in ([""] if tid == self.MALINDA else ["", "_a", "_b", "_c", "_d", "_e", "_f", "_g", "_h", "_i", "_j"]):
                                        for ex in (["", "_1", "_2", "_3", "_4", "_5", "_6"] if tid == self.MALINDA else [""]):
                                            try:
                                                fn = "nsp_{}_{}{}{}{}{}{}{}".format(tid, uncap, style, g, form, catype, sub, ex)
                                                attacks += await self.processManifest(fn)
                                                found = True
                                            except:
                                                pass
                                    if found: break
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
                self.modified = True
                self.data[index][id] = data
                self.data['scene_queue'].append(id)
                self.data['sound_queue'].append(id)
                self.addition[id] = self.ADD_CHAR
            return True

    # Update partner data. Note: It's based on charaUpdate and is terribly inefficient
    async def partnerUpdate(self, id : str, step : int) -> bool:
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
                    if not self.force_partner and tid in lookup:
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
                                        for af in (["", "_f", "_f1", "_f2"] if altForm else [""]):
                                            targets.append(base_fn + af + g + m + n)
                        tmp[self.CHARA_GENERAL] = targets
                        # # # Main sheets
                        for uncap in (["0_01", "1_01", "0_02", "1_02"] if is_mc else ["01", "02", "03", "04"]):
                            for gender in ["", "_0", "_1"]:
                                for ftype in ["", "_s2", "_0", "_1"]:
                                    for form in ["", "_f", "_f1", "_f2"]:
                                        try:
                                            fn = "npc_{}_{}{}{}{}{}".format(tid, uncap, style, gender, form, ftype)
                                            if fn not in lookup: sheets += await self.processManifest(fn, True)
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
                                for form in (["", "_f", "_f1", "_f2"] if altForm else [""]):
                                    try:
                                        fn = "phit_{}{}{}{}{}".format(tid, t, style, u, form)
                                        if fn not in lookup: attacks += await self.processManifest(fn, True)
                                    except:
                                        pass
                        tmp[self.CHARA_PHIT] = attacks
                        # ougi
                        attacks = []
                        for uncap in uncaps:
                            try: uf = flags[uncap.split('_')[-1]]
                            except: uf = [False]
                            found = False
                            for g in (["", "_0", "_1"] if (uf[0] is True) else [""]):
                                for form in (["", "_f", "_f1", "_f2"] if altForm else [""]):
                                    for catype in ["", "_s2", "_s3"]:
                                        for sub in ["", "_a", "_b", "_c", "_d", "_e", "_f", "_g", "_h", "_i", "_j"]:
                                            try:
                                                fn = "nsp_{}_{}{}{}{}{}{}".format(tid, uncap, style, g, form, catype, sub)
                                                if fn not in lookup: attacks += await self.processManifest(fn, True)
                                                found = True
                                            except:
                                                pass
                                        if found: break
                        tmp[self.CHARA_SP] = attacks
                        # skills
                        attacks = []
                        for el in ["01", "02", "03", "04", "05", "06", "07", "08"]:
                            try:
                                fn = "ab_all_{}{}_{}".format(tid, style, el)
                                if fn not in lookup: attacks += await self.processManifest(fn, True)
                            except:
                                pass
                        tmp[self.CHARA_AB_ALL] = attacks
                        attacks = []
                        for el in ["01", "02", "03", "04", "05", "06", "07", "08"]:
                            try:
                                fn = "ab_{}{}_{}".format(tid, style, el)
                                if fn not in lookup: attacks += await self.processManifest(fn, True)
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
    async def npcUpdate(self, id : str) -> bool:
        with self.progress:
            async with self.sem:
                data = [False, [], []] # journal flag, npc, voice
                if id in self.data["npcs"] and self.data["npcs"][id] != 0:
                    data[self.NPC_SCENE] = self.data["npcs"][id][self.NPC_SCENE]
                    data[self.NPC_SOUND] = self.data["npcs"][id][self.NPC_SOUND]
                exist = False
                try:
                    await self.head(self.IMG + "sp/assets/npc/m/{}_01.jpg".format(id))
                    data[self.NPC_JOURNAL] = True
                    exist = True
                except:
                    if id.startswith("305"): return False # don't continue for special npcs
                if not exist:
                    # base scene
                    if self.debug_npc_detail: base_target = self.SCENE_CHECK
                    elif id in self.SCENE_MC_ID: base_target = self.SCENE_BASE_MC
                    else: base_target = self.SCENE_BASE
                    for u in ["", "_03"]:
                        for f in base_target:
                            try:
                                if f not in data[self.NPC_SCENE]:
                                    if (await self.multi_head_nx([self.IMG + "sp/quest/scene/character/body/{}{}{}.png".format(id, u, f), self.IMG + "sp/raid/navi_face/{}{}.png".format(id, f)])) is not None:
                                        data[self.NPC_SCENE].append(f)
                                        exist = True
                                        break
                                else:
                                    exist = True
                                    break
                            except:
                                pass
                    # base sound
                    if not exist:
                        for k in ["_v_001", "_boss_v_1"]:
                            try:
                                f = "{}{}".format(id, k)
                                if f not in data[self.NPC_SCENE]:
                                    await self.head(self.SOUND + "voice/" + f + ".mp3")
                                    data[self.NPC_SOUND].append(k)
                                    exist = True
                                else:
                                    exist = True
                            except:
                                pass
                if exist:
                    self.modified = True
                    self.data['npcs'][id] = data
                    self.data['scene_queue'].append(id)
                    self.data['sound_queue'].append(id)
                    self.addition[id] = self.ADD_NPC
                return exist

    # Update Summon data
    async def sumUpdate(self, id : str) -> bool:
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
                if len(data[self.SUM_GENERAL]) == 0 and id in self.CUT_CONTENT:
                    data[self.SUM_GENERAL].append(id)
                    uncaps = ["01"]
                # attack
                for u in uncaps:
                    for m in ["", "_a", "_b", "_c", "_d", "_e"]:
                        try:
                            fn = "summon_{}_{}{}_attack".format(id, u, m)
                            data[self.SUM_CALL] += await self.processManifest(fn)
                        except:
                            pass
                # damage
                try:
                    data[self.SUM_DAMAGE] += await self.processManifest("summon_{}".format(id)) # old summons
                except:
                    pass
                for u in uncaps:
                    for m in ["", "_a", "_b", "_c", "_d", "_e"]:
                        try:
                            fn = "summon_{}_{}{}_damage".format(id, u, m)
                            data[self.SUM_DAMAGE] += await self.processManifest(fn)
                        except:
                            pass
                self.modified = True
                self.data['summons'][id] = data
                self.addition[id] = self.ADD_SUMM
            return True

    # Update Weapon data
    async def weapUpdate(self, id : str) -> bool:
        with self.progress:
            async with self.sem:
                data = [[], [], []] # general, phit, sp
                for s in ["", "_02", "_03"]:
                    # art
                    try:
                        await self.head(self.IMG + "sp/assets/weapon/m/{}{}.jpg".format(id, s))
                        data[self.WEAP_GENERAL].append("{}{}".format(id, s))
                    except:
                        if s == "":
                            if self.debug_wpn: data[self.WEAP_GENERAL].append("{}{}".format(id, s))
                            else: return False
                        else:
                            break
                    # attack
                    for u in ["", "_2", "_3", "_4"]:
                        for g in ["", "_0", "_1"]:
                            try:
                                fn = "phit_{}{}{}{}".format(id, s, g, u)
                                data[self.WEAP_PHIT] += await self.processManifest(fn)
                            except:
                                if g == '_0':
                                    break
                    # ougi
                    for u in ["", "_0", "_1", "_2", "_3"]:
                        for t in ["", "_s2", "_s3"]:
                            for g in ["", "_0", "_1"]:
                                try:
                                    fn = "sp_{}{}{}{}{}".format(id, s, g, u, t)
                                    data[self.WEAP_SP] += await self.processManifest(fn)
                                except:
                                    if g == '_0':
                                        break
                if self.debug_wpn and len(data[self.WEAP_PHIT]) == 0 and len(data[self.WEAP_SP]) == 0:
                    return False
                data[self.WEAP_PHIT] = list(set(data[self.WEAP_PHIT]))
                data[self.WEAP_PHIT].sort()
                data[self.WEAP_SP] = list(set(data[self.WEAP_SP]))
                data[self.WEAP_SP].sort()
                self.modified = True
                self.data['weapons'][id] = data
                self.addition[id] = self.ADD_WEAP
            return True

    # Update Enemy data
    async def mobUpdate(self, id : str) -> bool:
        with self.progress:
            async with self.sem:
                data = [[], [], [], [], [], []] # general, sprite, appear, ehit, esp, esp_all
                # icon
                try:
                    await self.head(self.IMG + "sp/assets/enemy/s/{}.png".format(id))
                    data[self.BOSS_GENERAL].append("{}".format(id))
                except:
                    try:
                        await self.head(self.IMG + "sp/assets/enemy/m/{}.png".format(id))
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
                for k in ["", "_2", "_3", "_shade"]:
                    try:
                        fn = "raid_appear_{}{}".format(id, k)
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

    # Update Background data
    async def bgUpdate(self, id : str) -> bool:
        with self.progress:
            async with self.sem:
                modified = False
                try:
                    if isinstance(self.data['background'][id], list):
                        data = self.data['background'][id]
                    else:
                        data = [[]]
                except:
                    data = [[]]
                if id.startswith("event_") or id.startswith("main_") or id.startswith("common_"):
                    if id.startswith("main_"): path = "sp/guild/custom/bg/{}.png"
                    else: path = "sp/raid/bg/{}.jpg"
                    for s in ["", "_a", "_b", "_c"]:
                        f = id + s
                        if f in data[0]:
                            continue
                        elif s == "":
                            data[0].append(f)
                            modified = True
                            self.addition[f] = self.ADD_BG
                        else:
                            try:
                                await self.head(self.IMG + path.format(f))
                                data[0].append(f)
                                modified = True
                                self.addition[f] = self.ADD_BG
                            except:
                                break
                else:
                    if len(data[0]) != 3:
                        data[0] = [id+"_1",id+"_2",id+"_3"]
                        modified = True
                        for f in data[0]:
                            self.addition[f] = self.ADD_BG
                if modified:
                    data[0].sort()
                    self.modified = True
                    self.data['background'][id] = data
                return modified

    ### Scene ###################################################################################################################

    # list known scene strings along with errors encountered along the way
    def list_known_scene_strings(self) -> tuple:
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
    async def debug_output_scene_strings(self, out_return : bool = False, recur : bool = False) -> None:
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
                await self.debug_output_scene_strings(out_return, True)
                self.update_changelog = tmp
        else:
            if out_return:
                return keys
            else:
                with open("json/debug_scene_strings.json", mode="w", encoding="utf-8") as f:
                    json.dump(keys, f)
                print("Data exported to 'json/debug_scene_strings.json'")

    # set self.scene_strings and self.scene_strings_special if needed and return them
    def generate_scene_file_list(self) -> tuple:
        if self.scene_strings is None:
            self.scene_strings = []
            self.scene_strings_special = []
            added = set()
            for ex in self.SCENE_EXPRESSIONS:
                for v in self.SCENE_VARIATIONS:
                    if ex == v and ex != "": continue
                    f = ex+v
                    if f not in added:
                        added.add(f)
                        self.scene_strings.append(f)
                        self.scene_strings_special.append(f)
            for ex in self.SCENE_SPECIAL:
                for v in self.SCENE_VARIATIONS:
                    if ex == v and ex != "": continue
                    f = ex+v
                    if f not in added:
                        added.add(f)
                        self.scene_strings_special.append(f)
        return self.scene_strings, self.scene_strings_special

    # Called by -scene, update all npc and character scene datas. parameters can be a specific index to start from (in case you are resuming an aborted operation) or a list of string suffix or both (with the index first)
    async def update_all_scene(self, target_index : Optional[str] = None, params : list = [], update_pending : bool = False) -> None:
        target_list = []
        if update_pending:
            for k in self.data['scene_queue']:
                if k not in target_list:
                    target_list.append(k)
        else:
            if target_index is None:
                target_index = ["characters", "skins", "npcs"]
            elif not isinstance(target_index, list):
                target_index = [target_index]
            for k in target_index:
                target_list += list(self.data[k].keys())
        if len(target_list) == 0:
            return
        print("Updating scene data for {} element(s)".format(len(target_list)))
        start_index = 0
        filter = None
        if len(params) > 0:
            try:
                start_index = int(params[0])
                params = params[1:]
            except:
                pass
            finally:
                if len(params) > 0:
                    filter = params
                    print("The process will only check matches with", len(filter), "filter(s)")
        sk = start_index
        elements = []
        for id in target_list:
            if id[:3] in ['399', '305']:
                uncaps = ["", "03"]
                idx = self.NPC_SCENE
                k = 'npcs'
            else:
                uncaps = []
                idx = self.CHARA_SCENE
                k = 'characters' if id.startswith('30') else 'skins'
                for u in self.data[k][id][self.CHARA_GENERAL]:
                    uu = u.replace(id+"_", "")
                    if "_" not in uu and uu.startswith("0"):
                        uncaps.append(uu)
            for u in uncaps: # split per uncap
                if sk > 0:
                    sk -= 1
                    continue
                elements.append((k, id, idx, u, filter))
        if start_index > 0:
            print("(Skipping the first {} tasks(s) )".format(start_index))
        # start
        if len(elements) > 0:
            self.progress = Progress(self, total=len(elements)+start_index, silent=False, current=start_index)
            async for result in self.map_unordered(self.update_all_scene_sub, elements, self.MAX_SCENE_CONCURRENT):
                pass
            if update_pending: self.data['scene_queue'] = []
            print("Done")
            self.sort_all_scene()
            self.save()

    # used in update_all_scene_sub
    def scene_suffix_is_matching(self, name : str, filters : list) -> bool:
        for f in filters:
            if f in name:
                return True
        return False

    # update_all_scene() subroutine
    async def update_all_scene_sub(self, tup : tuple) -> None:
        with self.progress:
            k, id, idx, uncap, filter = tup
            try: existing = set(self.data[k][id][idx])
            except: return
            us = "" if uncap in ["", "01"] else "_"+uncap
            base_target = (self.SCENE_BASE_MC if id in self.SCENE_MC_ID else self.SCENE_BASE)
            
            # search bare base suffix
            if us not in existing:
                await self.update_all_scene_sub_req(k, id, idx, us, False)
                existing.add(us)
            
            # opti for npcs: quit if no base _03 file
            if k == "npcs" and us != "" and us not in existing: return
            print(">>>", id, us)
            
            # search other base suffixes
            tasks = []
            for s in base_target:
                f = us+s
                if f in existing or s == "": continue
                tasks.append(self.update_all_scene_sub_req(k, id, idx, f, False))
            if len(tasks) > 0: await asyncio.gather(*tasks)
            existing = set(self.data[k][id][idx])
            # search variations
            tasks = []
            for s in base_target:
                f = us+s
                if (s != "" and f not in existing): continue
                for ss in self.generate_scene_file_list()[1 if us == "" else 0]:
                    g = f + ss
                    if ss == "" or g in existing or (filter is not None and not self.scene_suffix_is_matching(g, filter)): continue
                    no_bubble = (g != "" and g.split("_")[-1] in self.SCENE_BUBBLE_FILTER)
                    tasks.append(self.update_all_scene_sub_req(k, id, idx, g, no_bubble))
                    if len(tasks) >= self.MAX_HTTP:
                        await asyncio.gather(*tasks)
                        tasks = []
            if len(tasks) > 0: await asyncio.gather(*tasks)

    # request used just above
    async def update_all_scene_sub_req(self, k : str, id : str, idx : int, g : str, no_bubble : bool) -> None:
        if (await self.multi_head_nx([self.IMG + "sp/quest/scene/character/body/{}{}.png".format(id, g)] if no_bubble else [self.IMG + "sp/quest/scene/character/body/{}{}.png".format(id, g), self.IMG + "sp/raid/navi_face/{}{}.png".format(id, g)])) is not None:
            self.data[k][id][idx].append(g)
            self.modified = True

    # Sort scene data by string suffix order, to keep some sort of coherency on the web page
    def sort_all_scene(self) -> None:
        print("Sorting scene data...")
        valentines = {}
        suffixes = []
        tmp = set()
        for u in ["", "_02", "_03", "_04"]:
            for s in self.SCENE_BASE_MC:
                for ss in self.generate_scene_file_list()[1 if u == "" else 0]:
                    f = u+s+ss
                    if f not in tmp:
                        suffixes.append(f)
                        tmp.add(f)
        tmp = None
        
        for t in ["characters", "skins", "npcs"]:
            if t == "npcs": idx = self.NPC_SCENE
            else: idx = self.CHARA_SCENE
            for id, v in self.data[t].items():
                if not isinstance(v, list): continue
                new = []
                before = str(v[idx])
                d = set(v[idx])
                for s in suffixes:
                    if s in d:
                        new.append(s)
                snew = str(new)
                if snew != before:
                    if len(new) == len(d): # should be the same length
                        self.modified = True
                        self.data[t][id][idx] = new
                    else: # just in case...
                        print(before)
                        print(snew)
                        print("Error sorting scene for ID:", id)
                        print("Interrupting...")
                        return
                if "_white" in snew or "_valentine" in snew:
                    valentines[id] = 0
        if str(valentines) != str(self.data['valentines']):
            self.data['valentines'] = valentines
            self.modified = True
        print("Done")
        self.save()

    ### Sound ###################################################################################################################

    # Called by -sound, update all npc and character sound datas
    async def update_all_sound(self, parameters : list = [], update_pending : bool = False) -> None:
        if update_pending:
            target_list = list(set(self.data['sound_queue']))
        else:
            target_list = []
            for k in ["characters", "skins", "npcs"]:
                target_list += list(self.data[k].keys())
            target_list = set(list(target_list))
        if len(target_list) == 0:
            return
        print("Updating sound data for {} element(s)".format(len(target_list)))
        start_index = 0
        if len(parameters) > 0:
            try:
                start_index = int(parameters[0])
            except:
                pass
        if start_index > 0: print("(Skipping the first {} tasks(s) )".format(start_index))
        elements = []
        for id in target_list:
            if id[:3] in ['399', '305']:
                uncaps = ["01"]
                idx = self.NPC_SOUND
                k = "npcs"
            else:
                uncaps = []
                idx = self.CHARA_SOUND
                k = 'characters' if id.startswith('30') else 'skins'
                for u in self.data[k][id][self.CHARA_GENERAL]:
                    uu = u.replace(id+"_", "")
                    if "_" not in uu and uu.startswith("0") and uu != "02":
                        uncaps.append(uu)
            try: voices = set(self.data[k][id][idx])
            except: voices = set()
            prep = self.update_chara_sound_file_prep(id, uncaps, voices)
            for i in range(0, len(prep), self.SOUND_CONCURRENT_PER_STEP):
                prep_split = []
                if i == 0: prep_split.append(None) # banter
                for kk in prep[i:i + self.SOUND_CONCURRENT_PER_STEP]:
                    prep_split.append(kk)
                if start_index > 0:
                    start_index -= 1
                else:
                    elements.append((k, id, idx, voices, prep_split))
        # memory cleaning
        prep = None
        prep_split = None
        # start
        self.progress = Progress(self, total=len(elements), silent=False)
        async for result in self.map_unordered(self.update_all_sound_sub, elements, self.MAX_UPDATEALL):
            pass
        print("Done")
        if update_pending and len(self.data['sound_queue']) > 0:
            self.data['sound_queue'] = []
            self.modified = True
        self.save()

    # update_all_sound() subroutine
    async def update_all_sound_sub(self, tup : tuple) -> None:
        with self.progress:
            index, id, idx, existing, elements = tup
            for t in elements:
                if t is None:
                    res = await self.update_chara_sound_file_sub_banter(id, existing)
                else:
                    res =  await self.update_chara_sound_file_sub(*t)
                if len(res) > 0:
                    m = False
                    for r in res:
                        if r not in existing:
                            self.data[index][id][idx].append(r)
                            m = True
                    if m:
                        self.data[index][id][idx] = list(set(self.data[index][id][idx]))
                        self.data[index][id][idx].sort()
                        self.modified = True

    # prep work for update_chara_sound_file
    def update_chara_sound_file_prep(self, id : str, uncaps : Optional[list] = None, existing : set = set()) -> list:
        elements = []
        # standard stuff
        for uncap in uncaps:
            if uncap == "01": uncap = ""
            elif uncap == "02": continue # seems unused
            elif uncap != "": uncap = "_" + uncap
            for mid, Z in [("_", 3), ("_introduce", 1), ("_mypage", 1), ("_formation", 2), ("_evolution", 2), ("_archive", 2), ("_zenith_up", 2), ("_kill", 2), ("_ready", 2), ("_damage", 2), ("_healed", 2), ("_dying", 2), ("_power_down", 2), ("_cutin", 1), ("_attack", 1), ("_attack", 2), ("_ability_them", 1), ("_ability_us", 1), ("_mortal", 1), ("_win", 1), ("_lose", 1), ("_to_player", 1), ("_boss_v_", 1)]:
                match mid: # opti
                    case "_":
                        suffixes = ["", "a", "b"]
                        A = 1
                        max_err = 1
                    case _:
                        suffixes = ["", "a", "_a", "_1", "b", "_b", "_2", "_mix"]
                        A = 0 if mid == "_cutin" else 1
                        max_err = 1
                elements.append((id, existing, uncap + mid + "{}", suffixes, A, Z, max_err))
            for i in range(0, 65): # break down _v_ for speed, up to 650
                elements.append((id, existing, uncap + "_v_" + str(i).zfill(2) + "{}", ["", "a", "_a", "_1", "b", "_b", "_2"], 1, 1, 6))
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

    # generic sound subroutine
    async def update_chara_sound_file_sub(self, id : str, existing : set, suffix : str, post : list, index : Optional[int], zfill : Optional[int], max_err : Optional[int]) -> list:
        result = []
        if len(post) == 0: post = [""]
        if index is None: # single mode
            for p in post:
                f = suffix + p
                if f in existing or (await self.head_nx(self.VOICE + "{}{}.mp3".format(id, f))) is not None:
                    result.append(f)
        else:
            err = 0
            while len(str(index)) <= zfill:
                found = False
                for p in post: # check if already processed in the past
                    f = suffix.format(str(index).zfill(zfill)) + p
                    if f in existing:
                        found = True
                        err = 0
                        break
                if not found: # if not
                    tasks = []
                    for p in post:
                        f = suffix.format(str(index).zfill(zfill)) + p
                        if f not in existing:
                            tasks.append(self.update_chara_sound_file_sub_req(id, f))
                        else:
                            found = True
                    if len(tasks) > 0:
                        for r in await asyncio.gather(*tasks):
                            if r is not None:
                                result.append(r)
                                found = True
                    if not found:
                        err += 1
                        if err >= max_err and index > 0:
                            break
                    else:
                        err = 0
                index += 1
        return result

    async def update_chara_sound_file_sub_req(self, id : str, f : str) -> Optional[str]: # used above for asyncio gather
        if (await self.head_nx(self.VOICE + "{}{}.mp3".format(id, f))) is not None:
            return f
        return None

    # banter sound subroutine
    async def update_chara_sound_file_sub_banter(self, id : str, existing : set) -> list:
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

    # Check for new elements to lookup on the wiki, to update the lookup list
    async def buildLookup(self) -> None:
        if not self.use_wiki: return
        modified = set()
        # manual npcs
        try:
            print("Importing name_data.json ...")
            with open("json/name_data.json", mode="r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    try:
                        if v is None:
                            if k not in self.data["lookup"]:
                                self.data["lookup"][k] = "missing-help-wanted"
                                modified.add(k)
                            continue
                        elif v == "":
                            continue
                        if "$$" not in v and "$" in v: print("Missing $ Warning for", k, "in name_data.json")
                        match len(k):
                            case 10: # npc
                                if "@@" in self.data["lookup"].get(k, ""): continue
                                if "$$" in v:
                                    v = " ".join(v.split("$$")[0])
                                append = ""
                            case 7: # enemy
                                if "$$" in v:
                                    vs = v.split("$$")
                                    if vs[1] not in ["fire", "water", "earth", "wind", "light", "dark", "null"]: print("Element Warning for", k, "in name_data.json")
                                    v = vs[1] + " " + vs[0]
                                else:
                                    print("Element Warning for", k, "in name_data.json")
                                match k[:2]:
                                    case "11":
                                        append = " flying-boss"
                                    case "12"|"13":
                                        append = " beast-boss"
                                    case "21":
                                        append = " plant-boss"
                                    case "22":
                                        append = " insect-boss"
                                    case "31":
                                        append = " fish-boss"
                                    case "41"|"42":
                                        append = " golem-boss"
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
                                    case "71"|"73":
                                        append = " dragon-boss"
                                    case "72":
                                        append = " reptile-boss"
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
                        if vs[0] in ["/", "N", "R", "SR", "SSR", "n", "r", "sr", "ssr"]: vs = vs[1:]
                        l = (" ".join(vs) + append).lower().strip().replace('(', ' ').replace(')', ' ').replace('（', ' ').replace('）', ' ').replace(',', ' ').replace('、', ' ').replace('  ', ' ').replace('  ', ' ')
                        if l != self.data["lookup"].get(k, ""):
                            self.data["lookup"][k] = l
                            modified.add(k)
                    except:
                        pass
        except Exception as e:
            print("An error occured while reading name_data.json:", e)
        # first pass
        tables = {'job':['classes', 'mc_outfits'], 'skins':['character_outfits'], 'npcs':['npc_characters']}
        fields = {'characters':'id,element,rarity,name,series,race,gender,type,weapon,jpname,va,jpva', 'weapons':'id,element,type,rarity,name,series,jpname', 'summons':'id,element,rarity,name,series,jpname', 'classes':'id,name,jpname', 'mc_outfits':'outfit_id,outfit_name', 'character_outfits':'outfit_id,outfit_name,character_name', 'npc_characters':'id,name,series,race,gender,jpname,va,jpva'}
        for t in self.LOOKUP_TYPES:
            for table in tables.get(t, [t]):
                try:
                    print("Checking", table, "wiki cargo table for", t, "lookup...")
                    data = (await self.get("https://gbf.wiki/index.php?title=Special:CargoExport&tables={}&fields=_pageName,{}&format=json&limit=20000".format(table, fields.get(table)), headers={'User-Agent':self.USER_AGENT}, get_json=True))
                    for item in data:
                        match table:
                            case "classes"|"mc_outfits":
                                looks = ["gran", "djeeta"]
                            case _:
                                looks = []
                        if item.get('element', '') == 'any':
                            continue
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
                                            for c in v:
                                                looks.append({"o":"other", "m":"male", "f":"female"}.get(v, ""))
                                        case "_pageName":
                                            wiki = "@@" + v.replace(' ', '_') + " "
                                        case "rarity":
                                            looks.append(v.lower())
                                        case "race":
                                            if v == "Other":
                                                looks.append("unknown")
                                            else:
                                                looks.append(v.lower())
                                        case "series":
                                            looks.append(v.lower().replace(';', ' '))
                                        case _:
                                            looks.append(v.lower())
                                case list():
                                    for e in v:
                                        if k == "race" and e == "Other":
                                            looks.append("unknown")
                                        elif e != "-":
                                            looks.append(e.lower())
                                case _:
                                    pass
                        try:
                            id = str(item['id']).split('_', 1)[0]
                        except:
                            id = str(item['outfit id']).split('_', 1)[0]
                        looks = wiki + html.unescape(html.unescape(" ".join(looks))).replace('(', ' ').replace(')', ' ').replace('（', ' ').replace('）', ' ').replace(',', ' ').replace('、', ' ').replace('<br />', ' ').replace('<br />', ' ').replace('  ', ' ').replace('  ', ' ')
                        if id not in self.data['lookup'] or self.data['lookup'][id] != looks:
                            self.data['lookup'][id] = looks
                            modified.add(id)
                except Exception as e:
                    print(e)
                    pass

        # second pass
        if len(modified) > 0:
            print(len(modified), "element lookup(s) added/updated")
            self.modified = True
            count = 0
            # second pass
            for t in self.LOOKUP_TYPES:
                for k in self.data[t]:
                    check_shared = False
                    if k not in self.data['lookup'] or self.data['lookup'][k] is None:
                        if k in self.SPECIAL_LOOKUP:
                            self.data['lookup'][k] = self.SPECIAL_LOOKUP[k]
                        else:
                            check_shared = True
                    else:
                        if k not in modified and k in self.SPECIAL_LOOKUP and self.data['lookup'][k] != self.SPECIAL_LOOKUP[k]:
                            self.data['lookup'][k] = self.SPECIAL_LOOKUP[k]
                        check_shared = True
                    if check_shared:
                        for l in self.SHARED_NAMES:
                            if k not in l: continue
                            for m in l:
                                if m != k and m in self.data['lookup'] and m is not None and self.data['lookup'][m] is not None:
                                    self.data['lookup'][k] = self.data['lookup'][m].replace(m, k)
                                    break
                                break
                    if not check_shared:
                        count += 1
            print(count, "element(s) remaining without lookup data")
        self.save()
        print("Done")

    # called by -lookupfix, to manually edit missing data in case of system failure
    async def manualLookup(self) -> None:
        print("Checking the lookup...")
        count = 0
        for t in self.LOOKUP_TYPES:
            for k in self.data[t]:
                if k not in self.data['lookup'] or self.data['lookup'][k] is None:
                    if k in self.SPECIAL_LOOKUP:
                        self.data['lookup'][k] = self.SPECIAL_LOOKUP[k]
                        self.modified = True
                    else:
                        print("Input the lookup string for", k, "(leave blank to skip")
                        s = input()
                        if s == "":
                            count += 1
                        else:
                            self.data['lookup'][k] = s
                            self.modified = True
                elif k in self.SPECIAL_LOOKUP and self.data['lookup'][k] != self.SPECIAL_LOOKUP[k]:
                    self.data['lookup'][k] = self.SPECIAL_LOOKUP[k]
                    self.modified = True
        print(count, "element(s) remaining without lookup data")
        self.save()
        print("Done")

    ### Thumbnail ###############################################################################################################

    # Check the NPC list for npc with new thumbnails.
    async def update_npc_thumb(self) -> None:
        print("Updating NPC thumbnail data...")
        tasks = []
        async with asyncio.TaskGroup() as tg:
            self.progress = Progress(self)
            for id in self.data["npcs"]:
                if not isinstance(self.data["npcs"][id], int) and not self.data["npcs"][id][self.NPC_JOURNAL]:
                    tasks.append(tg.create_task(self.update_npc_thumb_sub(id)))
            self.progress.set(total=len(tasks), silent=False)
        for t in tasks:
            t.result()
        print("Done")
        self.save()

    # update_npc_thumb() subroutine
    async def update_npc_thumb_sub(self, id : str) -> None: # subroutine
        with self.progress:
            try:
                await self.head(self.IMG + "sp/assets/npc/m/{}_01.jpg".format(id))
                self.data["npcs"][id][self.NPC_JOURNAL] = True
                self.modified = True
            except:
                pass

    ### Events ##################################################################################################################

    # Ask the wiki to build a list of existing events with their start date. Note: It needs to be updated for something more efficient
    async def get_event_list(self) -> list:
        try:
            l = self.MISSING_EVENTS
            if not self.use_wiki: raise Exception()
            data = await self.get("https://gbf.wiki/index.php?title=Special:CargoExport&tables=event_history&fields=time_start,name&format=json&limit=20000", headers={'User-Agent':self.USER_AGENT}, get_json=True)
            for e in data:
                t = e['time start'].split(' ', 1)[0].split('-')
                t = t[0][2:] + t[1] + t[2]
                l.append(t)
        except:
            pass
        l = list(set(l))
        l.sort()
        return l

    # convert event id string to day count integer
    def ev2daycount(self, ev : str) -> int:
        return (int(ev[:2]) * 12 + int(ev[2:4])) * 31 + int(ev[4:6])

    # Call get_event_list() and check the current time to determine if new events have been added. If so, check if they got voice lines to determine if they got chapters, and then call update_event()
    async def check_new_event(self, init_list : Optional[list] = None) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=32400)
        nyear = now.year
        nmonth = now.month
        nday = now.day
        now = int(str(nyear)[2:] + str(nmonth).zfill(2) + str(nday).zfill(2))
        now_day = self.ev2daycount(str(now))
        if init_list is None:
            known_events = await self.get_event_list()
        else:
            init_list = list(set(init_list))
            known_events = init_list
        # check
        print("Checking for new events...")
        thumbnail_check = []
        tasks = []
        async with asyncio.TaskGroup() as tg:
            check = {}
            self.progress = Progress(self)
            for ev in known_events:
                if ev in self.data["events"]: # event already registered
                    if now >= int(ev) and now_day - self.ev2daycount(ev) <= 14: # if event is recent (2 weeks)
                        check[ev] = self.data["events"][ev][self.EVENT_CHAPTER_COUNT] # add to check list
                        if self.data["events"][ev][self.EVENT_THUMB] is None: # if no thumbnail, force thumbnail check
                            thumbnail_check.append(ev)
                elif now >= int(ev): # new event
                    check[ev] = -1
                    for i in range(0, self.EVENT_MAX_CHAPTER):
                        for j in range(1, 2):
                            for k in range(1, 2):
                               tasks.append(tg.create_task(self.update_event_sub(ev, self.VOICE + "scene_evt{}_cp{}_q{}_s{}0".format(ev, i, j, k))))
                               thumbnail_check.append(ev)
            self.progress.set(total=len(tasks), silent=False)
        if len(tasks) > 0: # processing tasks
            print(len(check.keys()), "potential new event(s)")
            for t in tasks:
                r = t.result()
                ev = r[0]
                if r[1] is not None:
                    check[ev] = max(check[ev], int(r[1].split('_')[2][2:]))
            for ev in check:
                if ev not in self.data["events"]:
                    if check[ev] >= 0:
                        print("Event", ev, "has been added (", check[ev], "chapters )")
                    self.data["events"][ev] = [check[ev], None, [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []] # 15+3+sky
                    self.modified = True
        # check thumbnail
        if len(thumbnail_check) > 0:
            thumbnail_check.sort()
            await self.event_thumbnail_association(thumbnail_check)
        # update content
        if init_list is None:
            await self.update_event(list(check.keys()))
        else:
            await self.update_event(init_list, full=True)

    # check_new_event() subroutine to request sound files
    async def update_event_sub(self, ev : str, url : str) -> tuple:
        with self.progress:
            for m in range(1, 20):
                try:
                    await self.head(url + "_{}.mp3".format(m))
                    return ev, url.split('/')[-1]
                except:
                    pass
            return ev, None

    # Check the given event list for potential art pieces
    async def update_event(self, events : list, full : bool = False, skip : int = 0) -> None:
        # dig
        special_events = {
           "221121": "_arcarum_maria",
           "230322": "_arcarum_caim",
           "230515": "_arcarum_nier",
           "230607": "_arcarum_estarriola",
           "230723": "_arcarum_fraux",
           "230816": "_arcarum_lobelia",
           "231007": "_arcarum_geisenborger",
           "231114": "_arcarum_haaselia",
           "240122": "_arcarum_alanaan",
           "240322": "_arcarum_katzelia"
        }
        
        print("Checking for content of", len(events), "event(s)")
        if skip > 0:
            print("(Skipping the first {} tasks(s) )".format(skip))
        tasks = []
        ec = 0
        self.progress = Progress(self)
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
                for j in range(self.EVENT_UPDATE_COUNT):
                    if ev not in special_events:
                        for i in range(1, ch_count+1):
                            fn = "scene_evt{}_cp{}".format(ev, str(i).zfill(2))
                            tasks.append((ev, self.IMG + "sp/quest/scene/character/body/"+fn, known_assets, j*self.SCENE_UPDATE_STEP))
                            if i < 10:
                                fn = "scene_evt{}_cp{}".format(ev, i)
                                tasks.append((ev, self.IMG + "sp/quest/scene/character/body/"+fn, known_assets, j*self.SCENE_UPDATE_STEP))
                        for ch in ["op", "ed"]:
                            fn = "scene_evt{}_{}".format(ev, ch)
                            tasks.append((ev, self.IMG + "sp/quest/scene/character/body/"+fn, known_assets, j*self.SCENE_UPDATE_STEP))
                        fn = "evt{}".format(ev)
                        tasks.append((ev, self.IMG + "sp/quest/scene/character/body/"+fn, known_assets, j*self.SCENE_UPDATE_STEP))
                    fn = "scene_evt{}".format(ev) + special_events.get(ev, '')
                    tasks.append((ev, self.IMG + "sp/quest/scene/character/body/"+fn, known_assets, j*self.SCENE_UPDATE_STEP))
        self.progress = Progress(self, total=len(tasks), silent=False, current=skip)
        if skip > 0:
            tasks = tasks[skip:]
        modified = False
        if len(tasks) > 0:
            async for task in self.map_unordered(self.check_scene_art_list, tasks, self.MAX_UPDATEALL):
                r = task.result()
                if r is not None:
                    ev = r[0]
                    if len(r[1])  > 0:
                        for e in r[1]:
                            try:
                                x = e.split("_")[2]
                                match x:
                                    case "op":
                                        target = self.EVENT_OP
                                    case "ed":
                                        target = self.EVENT_ED
                                    case "osarai":
                                        target = self.EVENT_INT
                                    case _:
                                        if "_cp" in e:
                                            target = self.EVENT_CHAPTER_START-1+int(x[2:])
                                        else:
                                            target = self.EVENT_INT
                            except:
                                target = self.EVENT_INT
                            if e not in self.data["events"][ev][target]:
                                self.data["events"][ev][target].append(e)
                        if full and self.data["events"][ev][self.EVENT_CHAPTER_COUNT] == -1: self.data["events"][ev][self.EVENT_CHAPTER_COUNT] = 0
                        modified = True
                        self.modified = True
                        self.addition[ev] = self.ADD_EVENT
        if modified:
            print("Sorting event scene data...")
            for ev in self.data["events"]:
                for i in range(self.EVENT_OP , len(self.data["events"][ev])):
                    before = str(self.data["events"][ev][i])
                    self.data["events"][ev][i].sort()
                    if str(before) != str(self.data["events"][ev][i]):
                        self.modified = True
                        self.addition[ev] = self.ADD_EVENT
        print("Done")
        self.save()

    # update_event() and check_msq() subroutine to check for possible art pieces
    async def check_scene_art_list(self, tup : tuple) -> tuple:
        ev, base_url, known_assets, step = tup
        is_tuto = "tuto_scene" in base_url
        Z = 1 if is_tuto else 2 # zfill value, for msq tutorial
        l = []
        with self.progress:
            for j in range(step, step+self.SCENE_UPDATE_STEP):
                url = base_url + "_" + str(j).zfill(Z)
                flag = False
                # base check
                for k in ["", "_up", "_shadow"]:
                    try:
                        if url.split("/")[-1]+k not in known_assets:
                            await self.head(url + k + ".png")
                            l.append(url.split("/")[-1]+k)
                        flag = True
                    except:
                        pass
                for k in ["_a", "_b", "_c", "_d", "_e", "_f", "_g", "_h", "_i", "_j", "_k", "_l", "_m", "_n", "_o", "_p", "_q", "_r", "_s", "_t", "_u", "_v", "_w", "_x", "_y", "_z"]:
                    found = False
                    try:
                        if url.split("/")[-1]+k not in known_assets:
                            await self.head(url + k + ".png")
                            l.append(url.split("/")[-1]+k)
                        flag = True
                        found = True
                    except:
                        pass
                    for ss in [["a", "b", "c", "d", "e", "f"], ["1", "2", "3", "4", "5"]]:
                        for kkk in ss:
                            try:
                                if url.split("/")[-1]+k+kkk not in known_assets:
                                    await self.head(url + k + kkk + ".png")
                                    l.append(url.split("/")[-1]+k+kkk)
                                flag = True
                                found = True
                            except:
                                break
                    if not found:
                        break
                if not flag or is_tuto: # check for extras
                    try: # alternative filename format
                        if url.split("/")[-1]+"_00" not in known_assets:
                            await self.head(url + "_00.png")
                            l.append(url.split("/")[-1]+"_00")
                    except:
                        pass
                    for k in ["_up", "_shadow"]:
                        try:
                            if url.split("/")[-1]+"_00"+k not in known_assets:
                                await self.head(url + "_00" + k + ".png")
                                l.append(url.split("/")[-1]+"_00"+k)
                        except:
                            pass
                    err = 0
                    i = 1
                    while i < 100 and err < 10:
                        k = str(i).zfill(Z)
                        try:
                            if url.split("/")[-1]+"_"+k not in known_assets:
                                await self.head(url + "_" + k + ".png")
                                l.append(url.split("/")[-1]+"_"+k)
                            err = 0
                            for kk in ["_a", "_b", "_c", "_d", "_e", "_f", "_g", "_h", "_i", "_j", "_k", "_l", "_m", "_n", "_o", "_p", "_q", "_r", "_s", "_t", "_u", "_v", "_w", "_x", "_y", "_z"]:
                                found = False
                                try:
                                    if url.split("/")[-1]+"_"+k+kk not in known_assets:
                                        await self.head(url + "_" + k + kk + ".png")
                                        l.append(url.split("/")[-1]+"_"+k+kk)
                                    found = True
                                except:
                                    pass
                                for ss in [["a", "b", "c", "d", "e", "f"], ["1", "2", "3", "4", "5"]]:
                                    for kkk in ss:
                                        try:
                                            if url.split("/")[-1]+"_"+k+kk+kkk not in known_assets:
                                                await self.head(url + "_" + k + kk + kkk + ".png")
                                                l.append(url.split("/")[-1]+"_"+k+kk+kkk)
                                            found = True
                                        except:
                                            break
                                if not found:
                                    break
                        except:
                            err += 1
                        i += 1
        return ev, l

    # Check if an event got skycompass art. Note: The event must have a valid thumbnail ID set
    async def update_event_sky(self, ev : str) -> None:
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
    async def event_edit(self) -> None:
        while True:
            print("\n[EDIT EVENT MENU]")
            print("[0] Stats")
            print("[1] Set Thumbnails")
            print("[2] Update Events")
            print("[3] Update All Valid Events")
            print("[4] Update SkyCompass")
            print("[5] Add Events")
            print("[6] Check new thumbnails")
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
                                            self.data["eventthumb"][str(self.data["events"][ev][self.EVENT_THUMB])] = 1
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
                    try:
                        skip = int(input("Input a number to resume a previous update (Leave blank to ignore):"))
                    except:
                        skip = 0
                    await self.update_event(l, skip=skip)
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
                                self.data["events"][s][self.EVENT_THUMB] = th
                                self.modified = True
                            print("Event added")
                        else:
                            break
                    self.save()
                case "6":
                    s = input("Input a list of Event dates (Leave blank to cancel):")
                    if s != "":
                        await self.event_thumbnail_association(s.split(" "))
                case _:
                    break

    # Attempt to automatically associate new event thumbnails to events
    async def event_thumbnail_association(self, events : list) -> None:
        tmp = []
        for ev in events:
            if ev == "": continue
            if self.data["events"][ev][self.EVENT_THUMB] is None:
                tmp.append(ev)
        events = tmp
        print("Checking event thumbnails...")
        in_use = set()
        for eid, ev in self.data["events"].items():
            if ev[self.EVENT_THUMB] is not None: in_use.add(str(ev[self.EVENT_THUMB]))
        in_use = list(in_use)
        in_use.sort()
        for eid in in_use:
            if eid not in self.data["eventthumb"] or self.data["eventthumb"][eid] == 0:
                self.modified = True
                self.data["eventthumb"][eid] = 1
        tasks = []
        async with asyncio.TaskGroup() as tg:
            self.progress = Progress(self, total=40, silent=False)
            for i in range(20):
                tasks.append(tg.create_task(self.event_thumbnail_association_sub(7001+i, 9000, 20)))
                tasks.append(tg.create_task(self.event_thumbnail_association_sub(9001+i, 10000, 20)))
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
                    await self.update_event_sky(str(events[i]))
                    self.modified = True
                print("Please make sure they have been set to their correct events")
            else:
                print("Can't match new events to new thumbnails with certainty, -eventedit is required")
        self.save()

    # event_thumbnail_association subroutine()
    async def event_thumbnail_association_sub(self, start : int, end : int, step : int) -> None:
        with self.progress:
            err = 0
            i = start
            while err < 50 and i < end:
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

    ### MSQ ####################################################################################################################

    # check for new story chapter files
    async def check_msq(self, check_all : bool = False, max_chapter : Optional[str] = None) -> None:
        if not self.use_wiki: return
        try:
            max_chapter = int(max_chapter)
        except:
            try:
                # retrieve current last chapter from wiki
                m = self.CHAPTER_REGEX.findall((await self.get("https://gbf.wiki/Main_Quest", headers={'User-Agent':self.USER_AGENT})).decode('utf-8'))
                s = set()
                for i in m:
                    for j in i:
                        if j != "": s.add(int(j.replace('-', '')))
                max_chapter = max(s)
            except:
                print("An error occured while attempting to retrieve the MSQ Chapter count from gbf.wiki")
                return
        # make list to check
        tasks = []
        for i in range(0, max_chapter+1):
            id = str(i).zfill(3)
            if check_all or id not in self.data['story']:
                self.data['story'][id] = [[]]
                if i == 0: fn = "tuto_scene"
                else: fn = "scene_cp{}".format(i)
                for j in range(self.STORY_UPDATE_COUNT):
                    tasks.append((str(i), self.IMG + "sp/quest/scene/character/body/"+fn, set(self.data['story'].get(id, [[]])[0]), j*self.SCENE_UPDATE_STEP))
                for q in range(1, 6):
                    for j in range(self.STORY_UPDATE_COUNT):
                        tasks.append((str(i), self.IMG + "sp/quest/scene/character/body/"+fn+"_q"+str(q), set(self.data['story'].get(id, [[]])[0]), j*self.SCENE_UPDATE_STEP))
        # do and update
        if len(tasks) > 0:
            if check_all: print("Checking all chapters up to {} included...".format(max_chapter))
            else: print("Checking new story chapters up to {} included...".format(max_chapter))
            self.progress = Progress(self, total=len(tasks), silent=False)
            async for task in self.map_unordered(self.check_scene_art_list, tasks, self.MAX_UPDATEALL):
                r = task.result()
                if r is not None:
                    id = r[0].zfill(3)
                    if len(r[1]) > 0:
                        self.data['story'][id][self.STORY_CONTENT] += r[1]
                        self.data['story'][id][self.STORY_CONTENT].sort()
                        self.addition[id] = self.ADD_STORY
                        self.modified = True
            self.save()

    ### Partners ################################################################################################################

    # Called by -partner. Make a list of partners and potential partners to update. VERY slow.
    async def update_all_partner(self, parameters : list = []) -> None:
        self.force_partner = True
        start_index = 0
        if len(parameters) > 0:
            try:
                start_index = int(parameters[0])
            except:
                pass
        if start_index > 0: print("(Skipping the first {} tasks(s) )".format(start_index))
        t = self.update_changelog
        self.update_changelog = False
        ids = list(self.data.get('partners', {}).keys())
        for id in self.data.get('characters', {}):
            if 'st' in id: continue
            ids.append("38" + id[2:])
        await self.manualUpdate(ids, start_index)
        self.update_changelog = t
        self.force_partner = False

    ### Buffs ###################################################################################################################

    # Check buff data for new icons
    async def update_buff(self) -> None:
        tasks = []
        task_count = 20
        async with asyncio.TaskGroup() as tg:
            self.progress = Progress(self, total=10*task_count, silent=False)
            for i in range(10):
                for j in range(task_count):
                    tasks.append(tg.create_task(self.update_buff_sub(1000*i+j, task_count, True)))
        for t in tasks:
            t.result()
        print("Done")
        self.save()

    # search_buff() wrapper to track the progress
    async def update_buff_sub(self, start : int, step : int, full : bool = False) -> None:
        with self.progress:
            await self.search_buff(start, step, full)

    ### Others ##################################################################################################################

    async def missing_npcs(self) -> None: # check for missing npc
        try:
            keys = list(self.data['npcs'].keys())
            keys.sort()
            max_id = int(keys[-1][3:7])
            ids = []
            for i in range(0, max_id):
                id = "399" + str(i).zfill(4) + "000"
                if id not in self.data['npcs']:
                    ids.append(id)
            if len(ids) > 0:
                print("Checking for", len(ids), "missing NPCs...")
                self.debug_npc_detail = True
                await self.manualUpdate(ids)
                self.debug_npc_detail = False
        except:
            pass

    # Request the current GBF version or possible maintenance state
    async def gbfversion(self) -> Optional[int]:
        try:
            res = await self.get('https://game.granbluefantasy.jp/', headers={'User-Agent':self.USER_AGENT, 'Accept-Language':'en', 'Host':'game.granbluefantasy.jp', 'Connection':'keep-alive'})
            res = res.decode('utf-8')
            return int(self.VERSION_REGEX.findall(res)[0])
        except:
            try:
                if 'maintenance' in res.lower(): return "maintenance"
            except:
                pass
            return None

    # Wait for an update to occur
    async def wait(self) -> bool:
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
    def print_help(self) -> None:
        print("Usage: python updater.py [START] [MODE]")
        print("")
        print("START parameters (Optional):")
        print("-wait        : Wait an in-game update before running.")
        print("-nochange    : Disable the update of changelog.json.")
        print("")
        print("MODE parameters (One at a time):")
        print("-run         : Update the data with new content (Followed by IDs to check if needed).")
        print("-update      : Manual data update (Followed by IDs to check).")
        print("-job         : Search for MC jobs (Time consuming).")
        print("-jobedit     : Job CLI.")
        print("-lookup      : Force update the lookup table (Time Consuming).")
        print("-lookupfix   : Lookup CLI.")
        print("-scenenpc    : Update scene index for every npcs (Time consuming).")
        print("-scenechara  : Update scene index for every characters (Time consuming).")
        print("-sceneskin   : Update scene index for every skins (Time consuming).")
        print("-scenefull   : Update scene index for every characters/skins/npcs (Very time consuming).")
        print("-scenesort   : Sort indexed scene data  for every characters/npcs.")
        print("-thumb       : Update npc thumbnail data.")
        print("-sound       : Update sound index for characters (Very time consuming).")
        print("-partner     : Update data for partner characters (Very time consuming).")
        print("-addpending  : Add a list of character/skin/npc ID to the pending list for scene/sound updates.")
        print("-runpending  : Run scene/sound updates for the pending lists of character/skin/npc IDs (Time consuming).")
        print("-enemy       : Update data for enemies (Time consuming).")
        print("-missingnpc  : Update all missing npcs (Time consuming).")
        print("-story       : Update main story arts. Can add 'all' to update all or a number to specify the chapter.")
        print("-event       : Update unique event arts (Very time consuming).")
        print("-eventedit   : Edit event data")
        print("-buff        : Update buff data")
        print("-bg          : Update background data")

    async def boot(self, argv : list) -> None:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=50)) as self.client:
                print("GBFAL updater v2.34\n")
                self.use_wiki = await self.test_wiki()
                if not self.use_wiki: print("Use of gbf.wiki is currently impossible")
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
                    elif "-run" in flags:
                        await self.run(extras)
                        await self.buildLookup()
                    elif "-update" in flags:
                        await self.manualUpdate(extras)
                        await self.buildLookup()
                    elif "-job" in flags: await self.search_job_detail(extras)
                    elif "-jobedit" in flags: await self.edit_job()
                    elif "-lookup" in flags: await self.buildLookup()
                    elif "-lookupfix" in flags: await self.manualLookup()
                    elif "-scenenpc" in flags: await self.update_all_scene("npcs", extras)
                    elif "-scenechara" in flags: await self.update_all_scene("characters", extras)
                    elif "-sceneskin" in flags: await self.update_all_scene("skins", extras)
                    elif "-scenefull" in flags: await self.update_all_scene(None, extras)
                    elif "-scenesort" in flags: self.sort_all_scene()
                    elif "-thumb" in flags: await self.update_npc_thumb()
                    elif "-sound" in flags: await self.update_all_sound(extras)
                    elif "-partner" in flags: await self.update_all_partner(extras)
                    elif "-enemy" in flags: await self.manualUpdate(list(self.data['enemies'].keys()))
                    elif "-missingnpc" in flags:
                        await self.missing_npcs()
                    elif "-addpending" in flags:
                        for id in extras:
                            if len(id) == 10 and id.startswith('3'):
                                self.data['scene_queue'].append(id)
                                self.data['sound_queue'].append(id)
                                self.modified = True
                        self.save()
                    elif "-runpending" in flags:
                        if len(self.data['scene_queue']) > 0:
                            await self.update_all_scene(update_pending=True)
                        if len(self.data['sound_queue']) > 0:
                            await self.update_all_sound(update_pending=True)
                    elif "-story" in flags:
                        all = False
                        cp = None
                        for e in extras:
                            if e.lower() == "all": all = True
                            else:
                                try:
                                    e = int(e)
                                    if e >= 0: cp = e
                                except:
                                    pass
                        await self.check_msq(all, cp)
                    elif "-event" in flags: await self.check_new_event()
                    elif "-eventedit" in flags: await self.event_edit()
                    elif "-buff" in flags: await self.update_buff()
                    elif "-bg" in flags: await self.manualUpdate(list(self.data.get('background', {}).keys()))
                    elif not ran:
                        self.print_help()
                        print("")
                        print("Unknown parameter:", k)
                self.save()
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    def start(self, argv : list):
        asyncio.run(self.boot(argv))

if __name__ == "__main__":
    Updater().start(sys.argv[1:])