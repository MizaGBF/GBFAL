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
        self._prev_percents_ = ("", "")
        if self.total > 0: self.update()

    def progress2str(self) -> str: # convert the percentage to a valid string
        s = "{:.2f}".format(100 * self.current / float(self.total))
        if s == self._prev_percents_[0]: # use cached result if same string
            return self._prev_percents_[1]
        l = len(s)
        while s[l-1] == '0' or s[l-1] == '.': # remove trailing 0 up to the dot (included)
            l -= 1
            if s[l] == '.':
                break
        self._prev_percents_ = (s, s[:l]) # cache the result
        return s[:l]

    def set(self, *, total : int = 0, silent : bool = False) -> None: # to initialize it after a task start, once we know the total
        if total >= 0:
            self.total = total
        self.silent = silent
        if not self.silent and self.total > 0:
            sys.stdout.write("\rProgress: {}%      ".format(self.progress2str()))
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
                sys.stdout.write("\rProgress: {}%      ".format(self.progress2str()))
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
    JOB_DETAIL_ALL = 4
    JOB_SD = 5
    JOB_MH = 6
    JOB_SPRITE = 7
    JOB_PHIT = 8
    JOB_SP = 9
    JOB_UNLOCK = 10
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
    QUEUE_KEY = ['uncap_queue', 'scene_queue', 'sound_queue']
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
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Rosetta/Dev'
    # scene string
    SCENE_SUFFIXES = {
        "default": {
            "base": ["", "_a", "_b", "_c", "_d", "_e", "_f", "_g", "_nalhe", "_school", "_astral", "_battle", "_off", "_race", "_guardian", "_cook", "_orange", "_blue", "_green", "_nude", "_mask", "_doll", "_girl", "_cow", "_two", "_three", "_2021", "_2022", "_2023", "_2024"],
            
            "main": ["", "_a", "_b", "_c", "_d", "_e", "_f", "_g", "_1", "_2", "_3", "_4", "_5", "_6", "_7", "_8", "_9", "_10", "_up", "_laugh", "_laugh_small", "_laugh2", "_laugh3", "_laugh4", "_laugh5", "_laugh6", "_laugh7", "_laugh8", "_laugh9", "_wink", "_wink2", "_shout", "_shout2", "_shout3", "_leer", "_sad", "_sad2",  "_sad3","_angry", "_angry2", "_angry3", "_angry4", "_roar", "_fear", "_fear2", "_cry", "_cry2", "_painful", "_painful2", "_painful3", "_painful4", "_shadow", "_shadow2", "_shadow3", "_light", "_close", "_serious", "_serious2", "_serious3", "_serious4", "_serious5", "_serious6", "_serious7", "_serious8", "_serious9", "_serious10", "_serious11", "_surprise", "_surprise2", "_surprise3", "_surprise4", "_think", "_think2", "_think3", "_think4", "_think5", "_serious", "_serious2", "_mood", "_mood2", "_mood3", "_despair", "_despair2", "_badmood", "_badmood2", "_ecstasy", "_ecstasy2", "_suddenly", "_suddenly2", "_speed2", "_shy", "_shy2", "_shy3", "_shy4", "_weak", "_weak2", "_sleep", "_sleepy", "_open", "_eye", "_bad", "_bad2", "_amaze", "_amaze2", "_amezed", "_joy", "_joy2", "_pride", "_pride2", "_jito", "_intrigue", "_intrigue2", "_pray", "_motivation", "_melancholy", "_concentration", "_mortifying", "_cold", "_cold2", "_cold3", "_cold4", "_weapon", "_stance", "_hood", "_letter", "_gesu", "_gesu2", "_stump", "_stump2", "_doya", "_fight", "_2021", "_2022", "_2023", "_2024", "_all", "_all2", "_pinya", "_ef", "_ef_left", "_ef_right", "_ef2", "_body", "_front", "_head", "_up_head", "_foot", "_back", "_middle", "_middle_left", "_middle_right", "_left", "_right", "_move", "_move2", "_jump", "_small", "_big", "_pair_1", "_pair_2", "_break", "_break2", "_break3", "_ghost", "_stand", "_two", "_three", "_stand", "_eyeline"],
            
            "unique": ["_valentine", "_valentine2", "_valentine3", "_white", "_whiteday", "_whiteday1", "_whiteday2", "_whiteday3", "_summer", "_summer2", "_halloween", "_sturm", "_rabbit"],
            
            "end": ["", "_a", "_b", "_b1", "_b2", "_b3", "_speed", "_line", "_up", "_up_speed", "_up_damage", "_up_line", "_up2", "_up3", "_up4", "_down", "_shadow", "_shadow2", "_shadow3", "_damage", "_damage_up", "_light", "_up_light", "_light_speed", "_vanish", "_vanish1", "_vanish2", "_fadein1", "_blood", "_up_blood"]
        },
        "3050000000": { # lyria
            "base": ["_muffler", "_swim"],
            "unique": ["_jewel", "_jewel2", "_birthday", "_birthday1", "_birthday2", "_birthday3", "_birthday4", "_birthday5"]
        },
        "3050001000": { # vyrn
            "unique": ["_birthday", "_birthday1", "_birthday2", "_birthday3", "_birthday4", "_birthday5"]
        },
        "3992852000": { # gold slime
            "unique": ["_jewel"]
        },
        "3990219000": { # mc (gran)
            "base": ["_dancer", "_mechanic", "_glory", "_kengo", "_monk", "_lumberjack", "_robinhood", "_horse", "_cavalry", "_paladin", "_panakeia", "_manadiver", "_king", "_eternals", "_eternals2"]
        },
        "3990002000": { # bk
            "base": ["_m"],
            "main": ["_off"]
        },
        "3030280000": { # sr joi
            "main": ["_off"]
        },
        "3030006000": { # sr io
            "base": ["_new"]
        },
        "3990326000": { # veight
            "base": ["_knife"]
        },
        "3991542000": { # rackam
            "base": ["_cigarette"]
        },
        "3991849000": { # shadowverse cards
            "unique": ["_03", "_06", "_09", "_10", "_11", "_12", "_19", "_20", "_21", "_22", "_25", "_30", "_31", "_32", "_37", "_40"]
        },
        "3993542000": { # marks
            "unique": ["_02", "_03", "_04", "_05", "_06", "_07", "_08", "_09", "_10"]
        },
        "3990135000": { # thug
            "base": ["_town"],
            "main": ["_thug"]
        },
        "3990162000": { # gastalga
            "main": ["_child1", "_child2"]
        },
        "3990465000": { # teepo
            "main": ["_chara"]
        },
        "3992265000": { # teepo
            "base": ["_helicopter"]
        },
        "3991666000": { # seox
            "base": ["_mask", "_halfmask"]
        },
        "3991829000": { # anthony
            "unique": ["_narrator"]
        },
        "3992169000": { # tsubasa
            "unique": ["_skin", "_skin_01", "_skin_02", "_skin_03"]
        },
        "3992888000": { # makura
            "unique": ["_rabbit1", "_rabbit2", "_rabbit3", "_rabbit4"]
        },
        "3993539000": { # miss heaty
            "unique": ["_uncontroll"]
        },
        "3040073000": { # ferry
            "unique": ["_beppo", "_beppo_jiji", "_jiji", "_foogee", "_foogee_nicola", "_nicola", "_momo"]
        }
    }
    SCENE_SUFFIXES["3990220000"] = SCENE_SUFFIXES["3990219000"] # djeeta = gran
    SCENE_SUFFIXES["3990024000"] = SCENE_SUFFIXES["3990135000"] # thug 2 = thug
    SCENE_SUFFIXES["3990031000"] = SCENE_SUFFIXES["3990135000"] # thug 3 = thug
    SCENE_SUFFIXES["3992257000"] = SCENE_SUFFIXES["3992265000"] # helicopter (auguste of the dead)
    SCENE_SUFFIXES["3040209000"] = SCENE_SUFFIXES["3040073000"] # ferry
    SCENE_SUFFIXES["3991804000"] = SCENE_SUFFIXES["3040073000"] # ferry
    
    SCENE_BUBBLE_FILTER = set([k[1:] for k in SCENE_SUFFIXES["default"]["end"] if len(k) > 0])
    
    def __init__(self) -> None:
        # main variables
        self.update_changelog = True # flag to enable or disable the generation of changelog.json
        self.debug_wpn = False # for testing
        self.debug_npc_detail = False # set to true for better detection
        self.data = { # data structure
            "version":self.SAVE_VERSION,
            "uncap_queue":[],
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
            "story":{},
            "premium":{}
        }
        self.load() # load self.data NOW
        self.modified = False # if set to true, data.json will be written on the next call of save()
        self.stat_string = None # set and updated by make_stats
        self.new_elements = [] # new indexed element
        self.addition = {} # new elements for changelog.json
        self.job_list = None
        self.scene_strings = None # contains list of suffix
        self.scene_strings_special = None # contains list of suffix
        self.force_partner = False # set to True by -partner
        self.shared_task_container = [] # used for -scene
        
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
        print("Type 'help' for a command list, or a command to execute, anything else to resume")
        while True:
            s = input(":").lower().split(' ')
            match s[0]:
                case 'help':
                    print("save    - call the save() function")
                    print("exit    - force exit the process, changes won't be saved")
                    print("peek    - check the content of data.json. Take two parameters: the index to look at and an id")
                    print("tchange - toggle update_changelog setting")
                case 'save':
                    if not self.modified:
                        print("No changes waiting to be saved")
                    else:
                        self.save()
                case 'peek':
                    if len(s) < 3:
                        print("missing 1 parameter: ID")
                    elif len(s) < 2:
                        print("missing 2 parameters: index, ID")
                    else:
                        try:
                            d = self.data[s[1]][s[2]]
                            print(s[1], '-', s[2])
                            print(d)
                        except Exception as e:
                            print("Can't read", s[1], '-', s[2])
                            print(e)
                case 'tchange':
                    self.update_changelog = not self.update_changelog
                    print("changelog.json updated list WILL be modified" if self.update_changelog else "changelog.json updated list won't be modified")
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
        except OSError as e:
            print(e)
            if input("Continue anyway? (type 'y' to continue):").lower() != 'y':
                os._exit(0)
        except Exception as e:
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
                    self.data[k].sort()
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
                        stat = data.get('stat', None)
                        issues = data.get('issues', [])
                        help = data.get('help', False)
                        existing = {}
                        for e in data.get('new', []): # convert content to dict
                            existing[e[0]] = e[1]
                except:
                    existing = {}
                    stat = None
                    issues = []
                    help = False
                if self.update_changelog:
                    for k, v in self.addition.items(): # merge but put updated elements last
                        if k in existing: existing.pop(k)
                        existing[k] = v
                    self.addition = {} # clear self.addition
                # updated new elements
                new = [[k, v] for k, v in existing.items()] # convert back to list. NOTE: maybe make a cleaner way later
                if len(new) > self.MAX_NEW: new = new[len(new)-self.MAX_NEW:]
                # update stat
                if self.stat_string is not None: stat = self.stat_string
                with open('json/changelog.json', mode='w', encoding='utf-8') as outfile:
                    json.dump({'timestamp':int(datetime.now(timezone.utc).timestamp()*1000), 'new':new, 'stat':stat, 'issues':issues, 'help':help}, outfile)
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
        res = [src for l in data if (src := l['src'].split('?')[0].split('/')[-1])] # list all string srcs
        if verify_file: # check if at least one file is visible
            for k in res:
                try:
                    await self.head(self.IMG + "sp/cjs/" + k)
                    return res
                except:
                    pass
            raise Exception("Invalid Spritesheets")
        return res

    # clean shared_task_container of completed tasks
    def clean_shared_task(self) -> None:
        self.shared_task_container = [t for t in self.shared_task_container if not t.done()]

    # wait for all tasks in shared_task_container to be complete
    async def wait_shared_task_completion(self) -> None:
        while len(self.shared_task_container) > 0:
            await asyncio.sleep(0.01)
            self.clean_shared_task()

    # wait for free space to appear in shared_task_container
    async def wait_shared_task_free(self, limit : int) -> None:
        while len(self.shared_task_container) >= limit:
            await asyncio.sleep(0.01)
            self.clean_shared_task()

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
        if self.job_list is None:
            self.job_list = await self.init_job_list()
        if self.job_list is None:
            print("Couldn't retrieve job list from the game")
            return
        jkeys = [k for k in list(self.job_list.keys()) if k not in self.data['job']]
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
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "img/sp/quest/scene/character/body/", ".png", 70))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # assets
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "img/sp/raid/navi_face/", ".png", 50))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # assets
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "img/sp/quest/scene/character/body/", "_a.png", 50))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # assets
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "img/sp/assets/npc/b/", "_01.png", 70))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # sounds
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "sound/voice/", "_v_001.mp3", 50))
        categories.append([])
        self.newShared(errs)
        for i in range(10): # boss sounds
            categories[-1].append(self.search_generic('npcs', i, 10, errs[-1], "399{}000", 4, "sound/voice/", "_boss_v_1.mp3", 50))
        # special
        categories.append([])
        categories[-1].append(self.search_generic('npcs', 0, 1, self.newShared(errs), "305{}000", 4, "img/sp/quest/scene/character/body/", ".png", 2))
        #rarity of various stuff
        for r in range(1, 5):
            # weapons
            for j in range(10):
                categories.append([])
                self.newShared(errs)
                for i in range(5):
                    categories[-1].append(self.search_generic('weapons', i, 5, errs[-1], "10"+str(r)+"0{}".format(j) + "{}00", 3, "img/sp/assets/weapon/m/", ".jpg", 20))
            # summons
            categories.append([])
            self.newShared(errs)
            for i in range(5):
                categories[-1].append(self.search_generic('summons', i, 5, errs[-1], "20"+str(r)+"0{}000", 3, "img/sp/assets/summon/m/", ".jpg", 20))
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
                    categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "img/sp/assets/npc/raid_normal/", "_01.jpg", 20))
                categories.append([])
                self.newShared(errs)
                for i in range(5):
                    categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/phit_", ".js", 20))
                categories.append([])
                self.newShared(errs)
                for i in range(5):
                    categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/nsp_", "_01.js", 20))
        # other partners
        for r in range(8, 10):
            categories.append([])
            self.newShared(errs)
            for i in range(5):
                categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "img/sp/assets/npc/raid_normal/", "_01.jpg", 20))
            categories.append([])
            self.newShared(errs)
            for i in range(5):
                categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/phit_", ".js", 20))
            categories.append([])
            self.newShared(errs)
            for i in range(5):
                categories[-1].append(self.search_generic('partners', i, 5, errs[-1], "38"+str(r)+"0{}000", 3, "js/model/manifest/nsp_", "_01.js", 20))
        # skins
        categories.append([])
        self.newShared(errs)
        for i in range(5):
            categories[-1].append(self.search_generic('skins', i, 5, errs[-1], "3710{}000", 3, "js/model/manifest/npc_", "_01.js", 20))
        # enemies
        for a in range(1, 10):
            for b in range(1, 4):
                for d in [1, 2, 3]:
                    categories.append([])
                    self.newShared(errs)
                    for i in range(5):
                        categories[-1].append(self.search_generic('enemies', i, 5, errs[-1], str(a) + str(b) + "{}" + str(d), 4, "img/sp/assets/enemy/s/", ".png", 50))
        # backgrounds
        # event & common
        for i in ["event_{}", "common_{}"]:
            categories.append([])
            self.newShared(errs)
            for j in range(5):
                categories[-1].append(self.search_generic('background', j, 5, errs[-1], i, 3 if i.startswith("common_") else 1, "img/sp/raid/bg/", ".jpg", 10))
        # main
        categories.append([])
        self.newShared(errs)
        for j in range(5):
            categories[-1].append(self.search_generic('background', j, 5, errs[-1], "main_{}", 1, "img/sp/guild/custom/bg/", ".png", 10))
        # others
        for i in ["ra", "rb", "rc"]:
            categories.append([])
            self.newShared(errs)
            for j in range(5):
                categories[-1].append(self.search_generic('background', j, 5, errs[-1], "{}"+i, 1, "img/sp/raid/bg/", "_1.jpg", 50))
            break
        for i in [("e", ""), ("e", "r"), ("f", ""), ("f", "r"), ("f", "ra"), ("f", "rb"), ("f", "rc"), ("e", "r_3_a"), ("e", "r_4_a")]:
            categories.append([])
            self.newShared(errs)
            for j in range(5):
                categories[-1].append(self.search_generic('background', j, 5, errs[-1], i[0]+"{}"+i[1], 3, "img/sp/raid/bg/", "_1.jpg", 50))
        # titles
        categories.append([])
        self.newShared(errs)
        for i in range(3):
            categories[-1].append(self.search_generic('title', i, 3, errs[-1], "{}", 1, "img/sp/top/bg/bg_", ".jpg", 5))
        # subskills
        categories.append([])
        self.newShared(errs)
        for i in range(3):
            categories[-1].append(self.search_generic('subskills', i, 3, errs[-1], "{}", 1, "img/sp/assets/item/ability/s/", "_1.jpg", 5))
        # suptix
        categories.append([])
        self.newShared(errs)
        for i in range(3):
            categories[-1].append(self.search_generic('suptix', i, 3, errs[-1], "{}", 1, "img/sp/gacha/campaign/surprise/top_", ".jpg", 15))
        print("Starting process...")
        self.progress = Progress(self, total=len(categories), silent=False)
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self.run_category(c)) for c in categories]
        for t in tasks:
            t.result()
        self.save()
        if len(self.new_elements) > 0:
            await self.manualUpdate(self.new_elements)
            await self.check_msq()
            await self.check_new_event()
            await self.update_npc_thumb()
        else:
            if len(self.data['uncap_queue']) > 0:
                await self.manualUpdate([])
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
                async with asyncio.TaskGroup() as tg:
                    tasks = [tg.create_task(coroutines[i]) for i in range(len(coroutines))]
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
                try:
                    await self.head(self.ENDPOINT + path + f + ext)
                    err[0] = 0
                    self.data[index][f] = 0
                    if index in self.ADD_SINGLE_ASSET:
                        self.addition[index+":"+f] = index
                    self.modified = True
                    self.new_elements.append(f)
                    break
                except:
                    err[0] += 1
                    if err[0] >= maxerr:
                        err[1] = False
                        return
            i += step

    # -run subroutine to search for new skills
    async def search_skill(self, start : int, step : int) -> None: # skill search
        err = 0
        i = start
        tmp_c = ("0" if start < 1000 else str(start)[0])
        tmp = [k for k in list(self.data["skills"].keys()) if k[0] == tmp_c]
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
        tmp_c = ("0" if start < 1000 else str(start)[0])
        tmp = [k for k in list(self.data["buffs"].keys()) if k[0] == tmp_c]
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
                data = [[keys[i]], [keys[i]+"_01"], [], [], [], [], cmh, [], [], [], []] # main id, alt id, detailed id (main), detailed id (alt), detailed id (all), sd, mainhand, sprites, phit, sp, unlock
                
                data[self.JOB_ALT] = [keys[i][:-2]+str(j).zfill(2)+"_01" for j in alts]
                data[self.JOB_DETAIL] = [keys[i]+"_"+cmh[0]+"_"+str(k)+"_01" for k in range(2)]
                for j in [1]+alts:
                    for k in range(2):
                        data[self.JOB_DETAIL_ALT].append(keys[i][:-2]+str(j).zfill(2)+"_"+cmh[0]+"_"+str(k)+"_01")
                for j in colors:
                    for k in range(2):
                        data[self.JOB_DETAIL_ALL].append(keys[i][:-2]+str(j).zfill(2)+"_"+cmh[0]+"_"+str(k)+"_01")
                for j in colors:
                    data[self.JOB_SD].append(keys[i][:-2]+str(j).zfill(2))
                for j in range(2): # currently only for gw skins
                    try: data[self.JOB_UNLOCK] += await self.processManifest("eventpointskin_release_{}_{}".format(keys[i], j))
                    except: pass
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
            print("[4] Check unlock animations")
            print("[5] Export Data")
            print("[6] Import Data")
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
                                    for v in self.data['job'][jid][self.JOB_DETAIL_ALL]:
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
                    tmp = [k for k, v in self.data['job_wpn'].items() if v is None]
                    if len(tmp) == 0:
                        print("No unset weapon in memory")
                    else:
                        print("\n".join(tmp))
                case "2":
                    tmp = [k for k, v in self.data['job_key'].items() if v is None]
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
                    print("Checking for unlock animations...")
                    tasks = [self.edit_job_unlock_task(k) for k in self.data["job"]]
                    await asyncio.gather(*tasks)
                    print("Done")
                case "5":
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
                case "6":
                    try:
                        with open("json/job_data_export.json", mode="r", encoding="ascii") as f:
                            tmp = json.load(f)
                            if 'lookup' not in tmp or 'weapon' not in tmp:
                                raise Exception()
                    except OSError as e:
                        print("Couldn't open json/job_data_export.json")
                        print(e)
                        tmp = None
                    except Exception as e:
                        print("Couldn't load json/job_data_export.json")
                        print(e)
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

    async def edit_job_unlock_task(self, jid : str) -> None:
        if isinstance(self.data["job"][jid], list):
            if len(self.data["job"][jid]) == self.JOB_UNLOCK:
                self.data["job"][jid].append([])
                self.modified = True
            self.data["job"][jid][self.JOB_UNLOCK] = []
            for i in range(2):
                try:
                    self.data["job"][jid][self.JOB_UNLOCK] += await self.processManifest("eventpointskin_release_{}_{}".format(jid, i))
                    self.modified = True
                except:
                    pass
            if len(self.data["job"][jid][self.JOB_UNLOCK]) > 0:
                print(len(self.data["job"][jid][self.JOB_UNLOCK]), "sheets for", jid)

    async def edit_job_import_task(self, jid : str, s : Any, mode : int) -> None:
        try:
            match mode:
                case 0:
                    # set key
                    sheets = []
                    for v in self.data['job'][jid][self.JOB_DETAIL_ALL]:
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
                    if jid == "360101": # special exception for racing suit
                        try:
                            sheets += await self.processManifest("phit_racer")
                        except:
                            pass
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
        if len(self.data["uncap_queue"]) > 0:
            ids += self.data["uncap_queue"]
            self.data["uncap_queue"] = []
        if len(ids) == 0:
            return
        ids = list(set(ids)) # remove dupes
        ids.sort()
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
        self.make_stats(silent=True)
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
                        base_fn = "{}_{}{}".format(id, uncap, style)
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
                                    await self.head(self.IMG + "/sp/assets/npc/sd/" + base_fn + g + ".png")
                                    sd.append(base_fn + g)
                                except:
                                    pass
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
                lookup = []
                try:
                    data = self.data['partners'][str((int(id) // 1000) * 1000)]
                    if data == 0: raise Exception()
                    # build set of existing ids to avoid looking for them again
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
                except:
                    pass
                lookup = set(lookup)
                # ready empty container and set id
                data = [[], [], [], [], [], []] # sprite, phit, sp, aoe, single, general
                tid = id
                id = str((int(id) // 1000) * 1000)
                style = "" # placeholder
                max_err = 15 if id == "3890005000" else max(5, step // 3)  # placeholder
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
                    for i in range(len(data)):
                        self.data['partners'][id][i] = list(set(self.data['partners'][id][i] + data[i]))
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
                    base_target, main_x, uncap_x = self.generate_scene_file_list(id)
                    if self.debug_npc_detail:
                        base_target = list(set(base_target + main_x))
                    for u in ["", "_02", "_03"]:
                        for f in base_target:
                            if f != "" and u != "": break
                            try:
                                if f not in data[self.NPC_SCENE]:
                                    if (await self.multi_head_nx([self.IMG + "sp/quest/scene/character/body/{}{}{}.png".format(id, u, f), self.IMG + "sp/raid/navi_face/{}{}{}.png".format(id, u, f)])) is not None:
                                        data[self.NPC_SCENE].append(u+f)
                                        exist = True
                                        break
                                else:
                                    exist = True
                                    break
                            except:
                                pass
                    # base sound
                    if not exist:
                        base_target = (["_v_" + str(i).zfill(3) for i in range(5, 200, 5)] + ["_v_001", "_boss_v_1", "_boss_v_2", "_boss_v_3", "_boss_v_4", "_boss_v_5", "_boss_v_10", "_boss_v_15", "_boss_v_20", "_boss_v_25", "_boss_v_30", "_boss_v_35", "_boss_v_45", "_boss_v_50", "_boss_v_55", "_boss_v_60", "_boss_v_65", "_boss_v_70", "_boss_v_75", "d_boss_v_1"]) if self.debug_npc_detail else ["_v_001", "_boss_v_1", "_boss_v_2"]
                        for k in base_target:
                            try:
                                f = "{}{}".format(id, k)
                                if f not in data[self.NPC_SOUND]:
                                    await self.head(self.SOUND + "voice/" + f + ".mp3")
                                    data[self.NPC_SOUND].append(k)
                                    exist = True
                                else:
                                    exist = True
                                break
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
                        uncaps.append("_"+uncap if uncap != "" else "")
                        if uncap == "": uncaps.append("_01")
                    except:
                        break
                if len(uncaps) == 0 and id not in self.CUT_CONTENT:
                    return False
                if len(data[self.SUM_GENERAL]) == 0 and id in self.CUT_CONTENT:
                    data[self.SUM_GENERAL].append(id)
                    uncaps = ["", "_01"]
                # attack
                for u in uncaps:
                    for m in ["", "_a", "_b", "_c", "_d", "_e"]:
                        try:
                            fn = "summon_{}{}{}_attack".format(id, u, m)
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
                            fn = "summon_{}{}{}_damage".format(id, u, m)
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
    def generate_scene_file_list(self, id : str) -> tuple:
        if self.scene_strings is None:
            self.scene_strings = [{}, {}] # dict to keep order
            for main in self.SCENE_SUFFIXES["default"]["main"]:
                for end in self.SCENE_SUFFIXES["default"]["end"]:
                    if main != "" and main == end: continue
                    f = main + end
                    self.scene_strings[0][f] = None
            self.scene_strings[1] = self.scene_strings[0].copy()
            self.scene_strings[1] = list(self.scene_strings[1].keys())
            for unique in self.SCENE_SUFFIXES["default"]["unique"]:
                for end in self.SCENE_SUFFIXES["default"]["end"]:
                    if unique != "" and unique == end: continue
                    f = unique + end
                    self.scene_strings[0][f] = None
            self.scene_strings[0] = list(self.scene_strings[0].keys())
        
        if id in self.SCENE_SUFFIXES:
            if "base" in self.SCENE_SUFFIXES[id]:
                base = self.SCENE_SUFFIXES["default"]["base"] + self.SCENE_SUFFIXES[id]["base"]
            else:
                base = self.SCENE_SUFFIXES["default"]["base"]
            if "main" in self.SCENE_SUFFIXES[id] or "end" in self.SCENE_SUFFIXES[id] or "unique" in self.SCENE_SUFFIXES[id]:
                d = {}
                for k in ["main", "unique", "end"]:
                    if k not in self.SCENE_SUFFIXES[id]:
                        d[k] = self.SCENE_SUFFIXES["default"][k]
                    else:
                        s = set()
                        d[k] = []
                        for f in (self.SCENE_SUFFIXES["default"][k] + self.SCENE_SUFFIXES[id].get(k, [])):
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
            return self.SCENE_SUFFIXES["default"]["base"], self.scene_strings[0], self.scene_strings[1]

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
                uncaps = ["", "02", "03"]
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
            self.shared_task_container = []
            async for result in self.map_unordered(self.update_all_scene_sub, elements, self.MAX_SCENE_CONCURRENT):
                pass
            await self.wait_shared_task_completion()
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
            
            base_target, main_x, uncap_x = self.generate_scene_file_list(id)
            suffixes = main_x if us == "" else uncap_x
            
            # search bare base suffix
            if us not in existing:
                await self.update_all_scene_sub_req(k, id, idx, us, False)
                if us in self.data[k][id][idx]:
                    existing.add(us)
            
            # opti for npcs: quit if no base _03 file
            if k == "npcs" and us != "" and us not in existing: return
            
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
                for ss in suffixes:
                    g = f + ss
                    if ss == "" or g in existing or (filter is not None and not self.scene_suffix_is_matching(g, filter)): continue
                    no_bubble = (g != "" and g.split("_")[-1] in self.SCENE_BUBBLE_FILTER)
                    await self.wait_shared_task_free(self.MAX_UPDATEALL)
                    self.shared_task_container.append(asyncio.create_task(self.update_all_scene_sub_req(k, id, idx, g, no_bubble)))

    # request used just above
    async def update_all_scene_sub_req(self, k : str, id : str, idx : int, g : str, no_bubble : bool) -> None:
        if (await self.multi_head_nx([self.IMG + "sp/quest/scene/character/body/{}{}.png".format(id, g)] if no_bubble else [self.IMG + "sp/quest/scene/character/body/{}{}.png".format(id, g), self.IMG + "sp/raid/navi_face/{}{}.png".format(id, g)])) is not None:
            self.data[k][id][idx].append(g)
            self.modified = True

    # Sort scene data by string suffix order, to keep some sort of coherency on the web page
    def sort_all_scene(self) -> None:
        print("Sorting scene data...")
        valentines = self.data['valentines'].copy()
        for t in ["characters", "skins", "npcs"]:
            if t == "npcs": idx = self.NPC_SCENE
            else: idx = self.CHARA_SCENE
            for id, v in self.data[t].items():
                if not isinstance(v, list): continue
                new = v[idx].copy()
                new.sort(key=lambda e: (int(e.split("_")[1]) if ("_" in e and e.split("_")[1].isnumeric()) else 0, e, len(e)))
                if new != v[idx]:
                    self.modified = True
                    self.data[t][id][idx] = new
                if id not in valentines:
                    snew = str(new)
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
        start_index = 0
        if len(parameters) > 0 and len(parameters[0]) < 10:
            try:
                start_index = int(parameters[0])
                parameters = parameters[1:]
            except:
                pass
        target_list = list(set(self.data['sound_queue'])) if update_pending else []
        if len(parameters) > 0:
            target_list += [id for id in parameters if id not in target_list]
        elif len(target_list) == 0:
            target_list = []
            for k in ["characters", "skins", "npcs"]:
                target_list += list(self.data[k].keys())
            target_list = set(list(target_list))
        print("Updating sound data for {} element(s)".format(len(target_list)))
        if start_index > 0: print("(Skipping the first {} tasks(s) )".format(start_index))
        si = start_index
        elements = []
        for id in target_list:
            if len(id) != 10: continue
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
            if si > 0:
                si -= 1
            else:
                elements.append((k, id, idx, uncaps, voices))
        # start
        self.progress = Progress(self, total=len(elements)+start_index, silent=False, current=start_index)
        self.shared_task_container = []
        async for result in self.map_unordered(self.update_all_sound_sub, elements, self.MAX_UPDATEALL):
            pass
        await self.wait_shared_task_completion()
        print("Done")
        if update_pending and len(self.data['sound_queue']) > 0:
            self.data['sound_queue'] = []
            self.modified = True
        self.save()
        print("Cleaning...")
        for id in target_list: # removing dupes if any
            if len(id) != 10: continue
            if id[:3] in ['399', '305']:
                uncaps = ["01"]
                idx = self.NPC_SOUND
                k = "npcs"
            else:
                uncaps = []
                idx = self.CHARA_SOUND
                k = 'characters' if id.startswith('30') else 'skins'
            if not isinstance(self.data[k].get(id, None), list): continue
            voices = list(set(self.data[k][id][idx]))
            if len(voices) != len(self.data[k][id][idx]):
                self.data[k][id][idx] = voices
                self.modified = True
        print("Done")
        self.save()

    # update_all_sound() subroutine
    async def update_all_sound_sub(self, tup : tuple) -> None:
        with self.progress:
            index, id, idx, uncaps, existing = tup
            # banter
            await self.wait_shared_task_free(self.MAX_UPDATEALL)
            self.shared_task_container.append(asyncio.create_task(self.update_chara_sound_file_sub_banter(index, id, idx, existing)))
            prep = self.update_chara_sound_file_prep(id, uncaps, existing)
            # finish
            for i in range(0, len(prep), self.SOUND_CONCURRENT_PER_STEP):
                for kk in prep[i:i + self.SOUND_CONCURRENT_PER_STEP]:
                    await self.wait_shared_task_free(self.MAX_UPDATEALL)
                    self.shared_task_container.append(asyncio.create_task(self.update_chara_sound_file_sub(index, id, idx, existing, kk)))

    # prep work for update_chara_sound_file
    def update_chara_sound_file_prep(self, id : str, uncaps : Optional[list] = None, existing : set = set()) -> list:
        elements = []
        # standard stuff
        for uncap in uncaps:
            if uncap == "01": uncap = ""
            elif uncap == "02": continue # seems unused
            elif uncap != "": uncap = "_" + uncap
            for mid, Z in [("_", 3), ("_introduce", 1), ("_mypage", 1), ("_formation", 2), ("_evolution", 2), ("_archive", 2), ("_zenith_up", 2), ("_zenith_lankup", 2), ("_kill", 2), ("_ready", 2), ("_damage", 2), ("_healed", 2), ("_dying", 2), ("_power_down", 2), ("_cutin", 1), ("_attack", 1), ("_attack", 2), ("_ability_them", 1), ("_ability_us", 1), ("_mortal", 1), ("_win", 1), ("_lose", 1), ("_to_player", 1), ("d_boss_v_", 1)]:
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
                elements.append((uncap + mid + "{}", suffixes, A, Z, max_err))
            for i in range(0, 10): # break down _navi for speed, up to 100
                elements.append((uncap + "_boss_v_" + ("" if i == 0 else str(i)) + "{}", ["", "a", "_a", "_1", "b", "_b", "_2", "_mix"], 0, 1, 6))
            for i in range(0, 65): # break down _v_ for speed, up to 650
                elements.append((uncap + "_v_" + str(i).zfill(2) + "{}", ["", "a", "_a", "_1", "b", "_b", "_2", "c", "_c", "_3"], 0, 1, 6))
        # chain burst
        elements.append(("_chain_start", [], None, None, None))
        for A in range(2, 5):
            elements.append(("_chain{}_"+str(A), [], 1, 1, 1))
        # seasonal A
        for mid, Z in [("_birthday", 1), ("_Birthday", 1), ("_birthday_mypage", 1), ("_newyear_mypage", 1), ("_newyear", 1), ("_Newyear", 1), ("_valentine_mypage", 1), ("_valentine", 1), ("_Valentine", 1), ("_white_mypage", 1), ("_whiteday", 1), ("_Whiteday", 1), ("_WhiteDay", 1), ("_halloween_mypage", 1), ("_halloween", 1), ("_Halloween", 1), ("_christmas_mypage", 1), ("_christmas", 1), ("_Christmas", 1), ("_xmas", 1), ("_Xmas", 1)]:
            elements.append((mid + "{}", [], 1, Z, 5))
        for suffix in ["white","newyear","valentine","christmas","halloween","birthday"]:
            for s in range(1, 6):
                elements.append(("_s{}_{}".format(s, suffix) + "{}", [], 1, 1, 5))
        return elements

    # generic sound subroutine
    async def update_chara_sound_file_sub(self, index : str, id : str, idx : int, existing : set, element : tuple) -> None:
        result = []
        (suffix, post, current, zfill, max_err) = element
        if len(post) == 0: post = [""]
        if current is None: # single mode
            for p in post:
                f = suffix + p
                if f in existing or (await self.head_nx(self.VOICE + "{}{}.mp3".format(id, f))) is not None:
                    result.append(f)
        else:
            err = 0
            is_z_limited = suffix.startswith('_v_') or suffix.startswith('_boss_v_')
            while not is_z_limited or (is_z_limited and len(str(current)) <= zfill):
                found = False
                for p in post: # check if already processed in the past
                    f = suffix.format(str(current).zfill(zfill)) + p
                    if f in existing:
                        found = True
                        err = 0
                        break
                if not found: # if not
                    tasks = []
                    for p in post:
                        f = suffix.format(str(current).zfill(zfill)) + p
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
                        if err >= max_err and current > 0:
                            break
                    else:
                        err = 0
                current += 1
        if len(result) > 0:
            self.data[index][id][idx] += result
            self.modified = True

    async def update_chara_sound_file_sub_req(self, id : str, f : str) -> Optional[str]: # used above for asyncio gather
        if (await self.head_nx(self.VOICE + "{}{}.mp3".format(id, f))) is not None:
            return f
        return None

    # banter sound subroutine
    async def update_chara_sound_file_sub_banter(self, index : str, id : str, idx : int, existing : set) -> None:
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
        if len(result) > 0:
            self.data[index][id][idx] += result
            self.modified = True

    ### Lookup ##################################################################################################################

    # Check for new elements to lookup on the wiki, to update the lookup list
    async def buildLookup(self) -> None:
        if not self.use_wiki: return
        modified = set()
        # manual npcs
        
        try:
            print("Importing manual_lookup.json ...")
            with open("json/manual_lookup.json", mode="r", encoding="utf-8") as f:
                data = json.load(f)
            # check entries
            to_save = False
            for t in ["npcs", "enemies"]:
                for k in self.data[t]:
                    s = self.data['lookup'].get(k, None)
                    valid = s is not None and s != "" and not s.startswith("missing-help-wanted")
                    if valid and data.get(k, None) is None:
                        if '@@' in s:
                            s = s.split("@@", 1)[1].split(" ", 1)[1]
                        s = s.split(" ")
                        i = 0
                        while i < len(s):
                            if s[i] in ["/", "N", "R", "SR", "SSR", "n", "r", "sr", "ssr", "sabre", "axe", "spear", "gun", "staff", "melee", "harp", "katana", "bow", "dagger", "fire", "water", "earth", "wind", "light", "dark"]:
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
                print("json/manual_lookup.json updated with new entries")
        except OSError as e:
            print("Couldn't open json/manual_lookup.json")
            print(e)
            data = {}
        except Exception as e:
            print("Couldn't load json/manual_lookup.json")
            print(e)
            data = {}
        try:
            # fill the lookup table
            for k, v in data.items():
                try:
                    voice = (len(k) == 10 and self.data["npcs"].get(k, 0) != 0 and len(self.data["npcs"][k][self.NPC_SOUND]) > 0)
                    voice_only = voice and self.data["npcs"][k][self.NPC_JOURNAL] and len(self.data["npcs"][k][self.NPC_SCENE]) == 0
                    if v is None or v == "":
                        if self.data["lookup"].get(k, "missing-help-wanted").startswith("missing-help-wanted"):
                            l = "missing-help-wanted"
                            if voice:
                                l += " voiced"
                                if not voice_only:
                                    l += " voice-only"
                            if l != self.data["lookup"].get(k, None):
                                self.data["lookup"][k] = l
                                modified.add(k)
                        continue
                    if "$$" not in v and "$" in v: print("Missing $ Warning for", k, "in manual_lookup.json")
                    match len(k):
                        case 10: # npc
                            if "@@" in self.data["lookup"].get(k, ""): continue
                            if "$$" in v:
                                v = " ".join(v.split("$$")[0])
                            append = ""
                        case 7: # enemy
                            if "$$" in v:
                                vs = v.split("$$")
                                if vs[1] not in ["fire", "water", "earth", "wind", "light", "dark", "null"]: print("Element Warning for", k, "in manual_lookup.json")
                                v = vs[1] + " " + vs[0]
                            else:
                                print("Element Warning for", k, "in manual_lookup.json")
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
                    if vs[0] in ["/", "N", "R", "SR", "SSR", "n", "r", "sr", "ssr"]: vs = vs[1:]
                    l = (" ".join(vs) + append).lower().strip().replace('(', ' ').replace(')', ' ').replace('（', ' ').replace('）', ' ').replace(',', ' ').replace('、', ' ').replace('  ', ' ').replace('  ', ' ')
                    if voice:
                        l += " voiced"
                        if voice_only:
                            l += " voice-only"
                    if l != self.data["lookup"].get(k, ""):
                        self.data["lookup"][k] = l
                        modified.add(k)
                except:
                    pass
        except Exception as e:
            print("An error occured while updating the lookup table with json/manual_lookup.json", e)
        # first pass
        premium_lookup = {}
        weapon_associations = {}
        tables = {'job':['classes', 'mc_outfits'], 'skins':['character_outfits'], 'npcs':['npc_characters']}
        fields = {'characters':'id,element,rarity,name,series,race,gender,type,weapon,jpname,va,jpva,release_date,obtain,join_weapon', 'weapons':'id,element,type,rarity,name,series,jpname,release_date,character_unlock', 'summons':'id,element,rarity,name,series,jpname,release_date,obtain', 'classes':'id,name,jpname,release_date', 'mc_outfits':'outfit_id,outfit_name,release_date', 'character_outfits':'outfit_id,outfit_name,character_name,release_date', 'npc_characters':'id,name,series,race,gender,jpname,va,jpva,release_date'}
        for t in self.LOOKUP_TYPES:
            for table in tables.get(t, [t]):
                try:
                    print("Checking", table, "wiki cargo table for", t, "lookup...")
                    data = (await self.get("https://gbf.wiki/index.php?title=Special:CargoExport&tables={}&fields=_pageName,{}&format=json&limit=20000".format(table, fields.get(table)), headers={'User-Agent':self.USER_AGENT}, get_json=True))
                    await asyncio.sleep(0.2)
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
                        looks = wiki + html.unescape(html.unescape(" ".join(looks))).replace('(', ' ').replace(')', ' ').replace('（', ' ').replace('）', ' ').replace(',', ' ').replace('、', ' ').replace('<br />', ' ').replace('<br />', ' ').replace('  ', ' ').replace('  ', ' ').strip()
                        # voice
                        if len(id) == 10 and self.data["npcs"].get(id, 0) != 0 and len(self.data["npcs"][id][self.NPC_SOUND]) > 0: # npc sound
                            looks += " voiced"
                            if not self.data["npcs"][id][self.NPC_JOURNAL] and len(self.data["npcs"][id][self.NPC_SCENE]) == 0:
                                looks += " voice-only"
                        if id not in self.data['lookup'] or self.data['lookup'][id] != looks:
                            self.data['lookup'][id] = looks
                            modified.add(id)
                except Exception as e:
                    print(e)
                    pass
        if premium_lookup != self.data['premium']:
            self.data['premium'] = premium_lookup
            self.modified = True
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
            await self.update_all_event_skycompass()
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
                    await self.update_all_event_skycompass()
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
                    s = input("Input a list of Event dates to associate (Leave blank to continue):")
                    await self.event_thumbnail_association(s.split(" "))
                case _:
                    break

    # Check skycompass for all events
    async def update_all_event_skycompass(self) -> None:
        tasks = []
        async with asyncio.TaskGroup() as tg:
            for ev in self.data["events"]:
                if self.data["events"][ev][self.EVENT_THUMB] is not None:
                    tasks.append(tg.create_task(self.update_event_sky(ev)))
            print("Checking", len(tasks), "event(s)...")
        for t in tasks: t.result()
        print("Done.")
        self.save()

    # Attempt to automatically associate new event thumbnails to events
    async def event_thumbnail_association(self, events : list) -> None:
        tmp = []
        for ev in events:
            if ev == "" or ev not in self.data["events"]: continue
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

    def make_stats(self, silent=False) -> None:
        try:
            entity_count = 0
            scene_count = 0
            sound_count = 0
            file_estimation = 0
            for t in ["characters", "partners", "summons", "weapons", "enemies", "skins", "job", "npcs", "title", "suptix", "events", "skills", "subskills", "buffs", "story"]:
                ref = self.data.get(t, {})
                entity_count += len(ref.keys())
                for k, v in ref.items():
                    match t:
                        case "characters"|"skins"|"partners":
                            if v is None or v == 0: continue
                            file_estimation += len(v[self.CHARA_SPRITE])
                            file_estimation += len(v[self.CHARA_PHIT])
                            file_estimation += len(v[self.CHARA_SP])
                            file_estimation += len(v[self.CHARA_AB_ALL])
                            file_estimation += len(v[self.CHARA_AB])
                            file_estimation += len(v[self.CHARA_GENERAL]) * 14
                            if t != "partners":
                                file_estimation += len(v[self.CHARA_SD]) * 5
                                file_estimation += len(v[self.CHARA_SCENE])
                                file_estimation += len(v[self.CHARA_SOUND])
                                
                                scene_count += len(v[self.CHARA_SCENE])
                                sound_count += len(v[self.CHARA_SOUND])
                        case "summons":
                            if v is None or v == 0: continue
                            file_estimation += len(v[self.SUM_GENERAL]) * 12
                            file_estimation += len(v[self.SUM_CALL])
                            file_estimation += len(v[self.SUM_DAMAGE])
                        case "weapons":
                            if v is None or v == 0: continue
                            file_estimation += len(v[self.WEAP_GENERAL]) * 9
                            file_estimation += len(v[self.WEAP_PHIT])
                            file_estimation += len(v[self.WEAP_SP])
                        case "job":
                            if v is None or v == 0: continue
                            file_estimation += len(v[self.JOB_ID]) * 5
                            file_estimation += len(v[self.JOB_ALT]) * 3
                            file_estimation += len(v[self.JOB_DETAIL]) * 4
                            file_estimation += len(v[self.JOB_DETAIL_ALT]) * 14
                            file_estimation += len(v[self.JOB_DETAIL_ALL])
                            
                            file_estimation += len(v[self.JOB_SPRITE])
                            file_estimation += len(v[self.JOB_PHIT])
                            file_estimation += len(v[self.JOB_SP])
                            file_estimation += len(v[self.JOB_UNLOCK])
                        case "enemies":
                            if v is None or v == 0: continue
                            file_estimation += len(v[self.BOSS_GENERAL])
                            file_estimation += len(v[self.BOSS_SPRITE])
                            file_estimation += len(v[self.BOSS_APPEAR])
                            file_estimation += len(v[self.BOSS_HIT])
                            file_estimation += len(v[self.BOSS_SP])
                            file_estimation += len(v[self.BOSS_SP_ALL])
                        case "events":
                            if v is None or v == 0: continue
                            if v[self.EVENT_THUMB] is not None: file_estimation += 1
                            for i in range(self.EVENT_OP, self.EVENT_SKY+1):
                                file_estimation += len(v[i])
                        case "story":
                            if v is None or v == 0: continue
                            file_estimation += len(v[self.STORY_CONTENT])
                        case "npcs":
                            if v is None or v == 0: continue
                            if v[self.NPC_JOURNAL]: file_estimation += 1
                            file_estimation += len(v[self.NPC_SCENE])
                            file_estimation += len(v[self.NPC_SOUND])
                            
                            scene_count += len(v[self.NPC_SCENE])
                            sound_count += len(v[self.NPC_SOUND])
                        case "buffs":
                            if v is None or v == 0: continue
                            if len(v[0][0].split('_')) == 1: file_estimation += 1
                            file_estimation += len(v[1])
                        case _:
                            file_estimation += 2
            if not silent:
                print("")
                print("==== Indexation Stats ====")
                print(entity_count, "indexed elements")
                print(scene_count, "scene files" + ("" if file_estimation == 0 else " ({:.1f}%)".format(100*scene_count/file_estimation)))
                print(sound_count, "sound files" + ("" if file_estimation == 0 else " ({:.1f}%)".format(100*sound_count/file_estimation)))
                print("Approximately", file_estimation, "files total")
            self.stat_string = "{:,} indexed elements, for ~{:.1f}K files".format(entity_count, file_estimation / 1000).replace(".0K", "K")
        except Exception as e:
            print("An unexpected error occured, can't produce stats")
            print(e)

    async def missing_npcs(self) -> None: # check for missing npc
        try:
            keys = list(self.data['npcs'].keys())
            keys.sort()
            max_id = int(keys[-1][3:7])
            ids = [id for i in range(0, max_id) if (id := "399" + str(i).zfill(4) + "000") not in self.data['npcs']] # list of all npc without data
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
        print("-stats       : Display data.json stats before quitting.")
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
        print("-adduncap    : Add a list of element ID and they will automatically be checked the next time -run or -update is used.")
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
                print("GBFAL updater v2.43\n")
                self.use_wiki = await self.test_wiki()
                if not self.use_wiki: print("Use of gbf.wiki is currently impossible")
                start_flags = set(["-debug_scene", "-debug_wpn", "-wait", "-nochange", "-stats"])
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
                run_stats = "-stats" in flags
                
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
                    elif "-adduncap" in flags:
                        self.data['uncap_queue'] += extras
                        self.modified = True
                        self.save()
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
                    elif run_stats:
                        self.make_stats()
                        run_stats = False
                    elif not ran:
                        self.print_help()
                        print("")
                        print("Unknown parameter:", k)
                self.save()
                if run_stats:
                    self.make_stats()
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    def start(self, argv : list):
        asyncio.run(self.boot(argv))

if __name__ == "__main__":
    Updater().start(sys.argv[1:])