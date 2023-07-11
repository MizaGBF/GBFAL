import httpx
import json
import concurrent.futures
from threading import Lock
import sys
import queue
import time
import string
import re
from bs4 import BeautifulSoup
from datetime import datetime, timezone

class Parser():
    def __init__(self):
        self.running = False # control if the app is running
        self.update_changelog = True # flag to enable or disable the generation of changelog.json
        self.style_queue = queue.Queue() # queue used to process character styles
        self.request_queue = queue.Queue() # queue used to retrieve npc data
        self.quality = ("/img/", "/js/") # image and js quality
        self.data = { # data structure
            "characters":{},
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
            "lookup":{}
        }
        self.lock = Lock() # lock for self.data
        self.modified = False # if set to true, data.json will be updated
        self.new_elements = [] # new indexed element
        self.addition = {} # new elements for changelog.json
        self.mh = ['sw', 'wa', 'kn', 'me', 'bw', 'mc', 'sp', 'ax', 'gu', 'kt'] # main hand keyword list
        
        # TO BE MANUALLY UPDATED
        self.null_characters = ["3030182000", "3710092000", "3710139000", "3710078000", "3710105000", "3710083000", "3020072000", "3710184000"] # known NULL characters such as Lyria, skins included
        self.multi_summon = ["2040414000"] # summons with multiple calls
        self.chara_special = {"3710171000":"3710167000","3710170000":"3710167000","3710169000":"3710167000","3710168000":"3710167000"} # bobobo skins reuse bobobo data
        self.cut_ids = ["2040145000","2040147000","2040148000","2040150000","2040152000","2040153000","2040154000","2040200000"] # cut content (beta arcarum here)
        
        # relation processing
        self.name_table = {}
        self.name_table_modified = False 
        self.name_lock = Lock()
        
        # search lookup processing
        self.lookup_group = [["2030081000", "2030082000", "2030083000", "2030084000"], ["2030085000", "2030086000", "2030087000", "2030088000"], ["2030089000", "2030090000", "2030091000", "2030092000"], ["2030093000", "2030094000", "2030095000", "2030096000"], ["2030097000", "2030098000", "2030099000", "2030100000"], ["2030101000", "2030102000", "2030103000", "2030104000"], ["2030105000", "2030106000", "2030107000", "2030108000"], ["2030109000", "2030110000", "2030111000", "2030112000"], ["2030113000", "2030114000", "2030115000", "2030116000"], ["2030117000", "2030118000", "2030119000", "2030120000"], ["2040236000", "2040313000", "2040145000"], ["2040237000", "2040314000", "2040146000"], ["2040238000", "2040315000", "2040147000"], ["2040239000", "2040316000", "2040148000"], ["2040240000", "2040317000", "2040149000"], ["2040241000", "2040318000", "2040150000"], ["2040242000", "2040319000", "2040151000"], ["2040243000", "2040320000", "2040152000"], ["2040244000", "2040321000", "2040153000"], ["2040245000", "2040322000", "2040154000"], ["1040019500", '1040008000', '1040008100', '1040008200', '1040008300', '1040008400'], ["1040112400", '1040107300', '1040107400', '1040107500', '1040107600', '1040107700'], ["1040213500", '1040206000', '1040206100', '1040206200', '1040206300', '1040206400'], ["1040311500", '1040304900', '1040305000', '1040305100', '1040305200', '1040305300'], ["1040416400", '1040407600', '1040407700', '1040407800', '1040407900', '1040408000'], ["1040511800", '1040505100', '1040505200', '1040505300', '1040505400', '1040505500'], ["1040612300", '1040605000', '1040605100', '1040605200', '1040605300', '1040605400'], ["1040709500", '1040704300', '1040704400', '1040704500', '1040704600', '1040704700'], ["1040811500", '1040804400', '1040804500', '1040804600', '1040804700', '1040804800'], ["1040911800", '1040905000', '1040905100', '1040905200', '1040905300', '1040905400'], ["2040306000","2040200000"]] # elements sharing names (to be updated manually)
        self.other_lookup = { # special elements
            "3020065000": "r character brown poppet trial",
            "3030158000": "sr character blue poppet trial",
            "3040097000": "ssr character sierokarte trial",
            "2030004000": "sr summon fire not-playable",
            "2030014000": "sr summon dark not-playable",
        }
        
        # others
        self.re = re.compile("[123][07][1234]0\\d{4}00")
        self.vregex = re.compile("Game\.version = \"(\d+)\";")
        self.scene_strings, self.scene_special_strings = self.build_scene_strings()
        
        limits = httpx.Limits(max_keepalive_connections=300, max_connections=300, keepalive_expiry=10)
        self.client = httpx.Client(limits=limits)
        self.manifestUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/model/manifest/"
        self.cjsUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/cjs/"
        self.imgUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img"
        self.endpoint = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/"
        
        # startup
        self.load()
        self.exclusion = set([]) # a banned id list
        self.job_list = None

    def load(self): # load data.json
        try:
            with open('json/data.json', mode='r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict): return
            for k in self.data:
                self.data[k] = data.get(k, {})
        except Exception as e:
            print(e)

    def save(self): # save data.json
        try:
            if self.modified:
                self.modified = False
                with open('json/data.json', mode='w', encoding='utf-8') as outfile:
                    # custom json indentation
                    outfile.write("{\n")
                    keys = list(self.data.keys())
                    for k, v in self.data.items():
                        outfile.write('"{}":{}\n'.format(k, '{'))
                        last = list(v.keys())[-1]
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
                            existing = {}
                            for e in json.load(f).get('new', []):
                                existing[e[0]] = e[1]
                    except:
                        existing = {}
                    new = []
                    existing = existing | self.addition
                    self.addition = {}
                    for k, v in existing.items():
                        new.append([k, v])
                    if len(new) > 100: new = new[len(new)-100:]
                    with open('json/changelog.json', mode='w', encoding='utf-8') as outfile:
                        json.dump({'timestamp':int(datetime.now(timezone.utc).timestamp()*1000), 'new':new}, outfile)
                    print("changelog.json updated")
        except Exception as e:
            print(e)

    def newShared(self, errs): # create a list to be shared by threads
        errs.append([])
        errs[-1].append(0)
        errs[-1].append(True)
        errs[-1].append(Lock())
        return errs[-1]

    def run(self): # called by -run, update the indexed content
        errs = []
        possibles = []
        self.new_elements = []
        job_thread = 20
        
        if self.job_list is None:
            self.job_list = self.init_job_list()
        
        #rarity
        for r in range(1, 5):
            # characters
            if r > 1:
                self.newShared(errs)
                for i in range(4):
                    possibles.append(('characters', i, 4, errs[-1], "30"+str(r)+"0{}000", 3, "js/model/manifest/npc_", "_01{}.js", ["", "_st2"], 20))
            # summons
            possibles.append(('summons', 0, 1, self.newShared(errs), "20"+str(r)+"0{}000", 3, "js/model/manifest/summon_", "_01_damage.js", [""], 20))
            # weapons
            for j in range(10):
                possibles.append(('weapons', 0, 1, self.newShared(errs), "10"+str(r)+"0{}".format(j) + "{}00", 3, "img_low/sp/assets/weapon/m/", ".jpg", [""], 20))
        # skins
        self.newShared(errs)
        for i in range(2):
            possibles.append(('skins', i, 2, errs[-1], "3710{}000", 3, "js/model/manifest/npc_", "_01{}.js", [""], 20))
        # enemies
        for a in range(1, 10):
            for b in range(1, 4):
                for d in [1, 2, 3]:
                    possibles.append(('enemies', 0, 1, self.newShared(errs), str(a) + str(b) + "{}" + str(d), 4, "img/sp/assets/enemy/s/", ".png", [""], 50))
        # npc
        self.newShared(errs)
        for i in range(7):
            possibles.append(('npcs', i, 7, errs[-1], "399{}000", 4, "img_low/sp/quest/scene/character/body/", ".png", [""], 60))
        possibles.append(('npcs', 0, 1, self.newShared(errs), "305{}000", 4, "img_low/sp/quest/scene/character/body/", ".png", [""], 2))
        
        # backgrounds
        possibles.append(('background', 0, 1, self.newShared(errs), "event_{}", 1, "img_low/sp/raid/bg/", ".jpg", [""], 10))
        possibles.append(('background', 0, 1, self.newShared(errs), "common_{}", 3, "img_low/sp/raid/bg/", ".jpg", [""], 10))
        possibles.append(('background', 0, 1, self.newShared(errs), "main_{}", 1, "img_low/sp/guild/custom/bg/", ".png", [""], 10))
        for i in ["ra", "rb", "rc"]:
            possibles.append(('background', 0, 1, self.newShared(errs), "{}"+i, 1, "img_low/sp/raid/bg/", "_1.jpg", [""], 50))
        for i in [("e", ""), ("e", "r"), ("f", ""), ("f", "r"), ("f", "ra"), ("f", "rb"), ("f", "rc"), ("e", "r_3_a"), ("e", "r_4_a")]:
            possibles.append(('background', 0, 1, self.newShared(errs), i[0]+"{}"+i[1], 3, "img_low/sp/raid/bg/", "_1.jpg", [""], 50))
        
        # titles
        possibles.append(('title', 0, 1, self.newShared(errs), "{}", 1, "img_low/sp/top/bg/bg_", ".jpg", [""], 20))
        
        # job
        self.newShared(errs)
        jkeys = []
        for k in list(self.job_list.keys()):
            if k not in self.data["job"]:
                jkeys.append(k)
        if len(jkeys) > 0:
            job_thread == 0

        print("Starting index update... (", len(possibles)+job_thread, " threads )")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(possibles)+job_thread) as executor:
            futures = []
            for i in range(job_thread):
                futures.append(executor.submit(self.search_job, i, job_thread, jkeys, errs[-1]))
            # start
            for p in possibles:
                futures.append(executor.submit(self.subroutine, self.endpoint, *p))
            for future in concurrent.futures.as_completed(futures):
                future.result()
        print("Index update done")
        self.manualUpdate(self.new_elements)
        self.save()
        self.build_relation()

    def init_job_list(self): # to be called once when needed
        print("Initializing job list...")
        # existing classes
        try: job_list = self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/js_low/constant/job.js", get=True).decode('utf-8') # contain a list of all classes. it misses the id of the outfits however.
        except: return
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
            futures = []
            for i in range(31, 41):
                for j in range(0, 20):
                    if str(i * 100 + j)+"01" in job_list: continue
                    futures.append(executor.submit(self.init_job_list_sub, str(i * 100 + j)+"01"))
            for future in concurrent.futures.as_completed(futures):
                r = future.result()
                if r is not None:
                    job_list[r] = string.ascii_lowercase
        print("Done")
        return job_list

    def init_job_list_sub(self, id): # subroutine for threading
        try:
            self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/leader/m/{}_01.jpg".format(id))
            return id
        except:
            return None

    def search_job(self, start, step, keys, shared): # search jobs to be indexed
        i = start
        while i < len(keys):
            if keys[i] in self.data["job"]: continue
            cmh = []
            colors = [1]
            alts = []
            # mh check
            for mh in self.mh:
                try:
                    self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/leader/raid_normal/{}_{}_0_01.jpg".format(keys[i], mh))
                    cmh.append(mh)
                except:
                    continue
            if len(cmh) > 0:
                # alt check
                for j in [2, 3, 4, 5, 80]:
                    try:
                        self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/sd/{}_{}_0_01.png".format(keys[i][:-2]+str(j).zfill(2), cmh[0]))
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
                
                with self.lock:
                    self.data["job"][keys[i]] = data
                    self.modified = True
                    self.addition[keys[i]] = 0
            i += step
        with shared[2]:
            if shared[1]:
                if len(keys) > 1: print("Job search is done")
                shared[1] = False

    def search_job_detail(self): # used by -job, more specific but also slower job detection system
        if self.job_list is None:
            self.job_list = self.init_job_list()
        print("Searching additional job data...")
        futures = []
        to_search = []
        full_key_search = False
        # key search
        for k, v in self.data["job"].items():
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            for v in to_search:
                if v[0] == 0:
                    futures.append(executor.submit(self.detail_job_search, v[1], v[2]))
                elif v[0] == 1:
                    futures.append(executor.submit(self.detail_job_weapon_search, v[1]))
            # full key search
            if full_key_search:
                time.sleep(10) # delay to give time to detail_job_search
                for a in string.ascii_lowercase:
                    for b in string.ascii_lowercase:
                        for c in string.ascii_lowercase:
                            d = a+b+c
                            if d in self.data["job_key"]: continue
                            futures.append(executor.submit(self.detail_job_search_single, d))
                            time.sleep(0.005) # delay to give time to detail_job_search
            count = 0
            if len(futures) > 0:
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    count += 1
                    if count % 100 == 0:
                        print("Progress: {:.1f}%".format(100*count/len(futures)))
        print("Done")
        self.save()

    def detail_job_search(self, key, job): # subroutine for threading
        cmh = self.data["job"][job][6]
        a = key[0]
        for b in key:
            for c in key:
                d = a+b+c
                if d in self.data["job_key"] and self.data["job_key"][d] is not None: continue
                passed = True
                for mh in cmh:
                    try:
                        self.processManifest("{}_{}_0_01".format(d, mh))
                    except:
                        passed = False
                        break
                if passed:
                    with self.lock:
                        self.data["job_key"][d] = job
                        self.modified = True
                    print("Set", job, "to", d)

    def detail_job_weapon_search(self, wid): # subroutine for threading
        try:
            self.req(self.imgUri + '_low/sp/assets/weapon/m/' + wid + ".jpg")
            return
        except:
            pass
        for k in [["phit_", ""], ["sp_", "_1_s2"]]:
            try:
                self.req(self.manifestUri + k[0] + wid + k[1] + ".js")
                with self.lock:
                    self.data["job_wpn"][wid] = None
                    self.modified = True
                print("Possible job skin related weapon:", wid)
                break
            except:
                pass

    def detail_job_search_single(self, key): # subroutine for threading
        for mh in self.mh:
            try:
                self.processManifest("{}_{}_0_01".format(key, mh))
                with self.lock:
                    self.data["job_key"][key] = None
                    self.modified = True
                print("Unknown job key", key, "for mh", mh)
                break
            except:
                pass

    def edit_job(self): # CLI menu to manually fix data. to be used as a last resort
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
                        elif s not in self.data["job"]:
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
                                    for v in self.data["job"][jid][4]:
                                        try:
                                            sheets += self.processManifest(s + "_" + '_'.join(v.split('_')[1:3]) + "_" + v.split('_')[0][-2:])
                                        except:
                                            pass
                                    self.data['job'][jid][7] = list(dict.fromkeys(sheets))
                                    self.data['job_key'][s] = jid
                                    self.modified = True
                                    print(len(sheets),"sprites set to job", jid)
                                elif s in self.data['job_wpn']:
                                    # phit
                                    try:
                                        self.data['job'][jid][8] = list(dict.fromkeys(self.processManifest("phit_{}".format(s))))
                                    except:
                                        pass
                                    # ougi
                                    sheets = []
                                    for u in ["", "_0", "_1", "_0_s2", "_1_s2", "_0_s3", "_1_s3"]:
                                        try:
                                            sheets += self.processManifest("sp_{}{}".format(s, u))
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
                                    for v in self.data["job"][jid][4]:
                                        try:
                                            sheets += self.processManifest(s + "_" + '_'.join(v.split('_')[1:3]) + "_" + v.split('_')[0][-2:])
                                        except:
                                            pass
                                    self.data['job'][jid][7] = list(dict.fromkeys(sheets))
                                    self.data['job_key'][s] = jid
                                    self.modified = True
                                    print(len(sheets),"sprites set to job", jid)
                            for jid, s in tmp["weapon"].items():
                                if s is not None:
                                    # phit
                                    try:
                                        self.data['job'][jid][8] = list(dict.fromkeys(self.processManifest("phit_{}".format(s))))
                                    except:
                                        pass
                                    # ougi
                                    sheets = []
                                    for u in ["", "_0", "_1", "_0_s2", "_1_s2", "_0_s3", "_1_s3"]:
                                        try:
                                            sheets += self.processManifest("sp_{}{}".format(s, u))
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

    def subroutine(self, endpoint, index, start, step, err, file, zfill, path, ext, styles, maxerr): # run() subroutine
        id = start
        is_js = ext.endswith('.js')
        while err[0] < maxerr and err[1]:
            f = file.format(str(id).zfill(zfill))
            for s in styles:
                try:
                    if f+s in self.data[index] and (not is_js or (is_js and self.data[index][f+s] != 0)):
                        with err[2]:
                            err[0] = 0
                        continue
                    if f in self.multi_summon: self.req(endpoint + path + f + ext.replace("_damage", "_a_damage"))
                    else: self.req(endpoint + path + f + ext.replace("{}", s))
                    with err[2]:
                        err[0] = 0
                        self.data[index][f+s] = 0
                        self.modified = True
                        self.new_elements.append(f+s)
                        print("New Element:",f+s)
                except:
                    if s != "": break
                    with err[2]:
                        err[0] += 1
                        if err[0] >= maxerr:
                            if err[1]: print("Group", index, "("+file.format('X'*zfill)+")", "is done")
                            err[1] = False
                            return
                    break
            id += step

    def req(self, url, headers={}, get=False): # HEAD or GET request function. Set get to True when the content must be downloaded and read
        if get:
            response = self.client.get(url.replace('/img/', self.quality[0]).replace('/js/', self.quality[1]), headers={'connection':'keep-alive'} | headers, timeout=50)
        else:
            response = self.client.head(url.replace('/img/', self.quality[0]).replace('/js/', self.quality[1]), headers={'connection':'keep-alive'} | headers, timeout=50)
        if response.status_code != 200: raise Exception()
        if get:
            return response.content
        else:
            return response.headers

    def run_index_content(self): # called by -index. check and attempt to update incomplete content
        print("Checking index content...")
        to_update = []
        for k in ["characters", "summons", "skins", "weapons", "enemies", "npcs"]:
            for id in self.data[k]:
                if self.data[k][id] == 0:
                    to_update.append(id)
        if len(to_update) > 0:
            print(len(to_update), "element(s) to be updated. Starting...")
            self.manualUpdate(to_update)
        else:
            print("No elements need to be updated")

    def styleProcessing(self): # subroutine checking for content in style_queue
        count = 0
        while self.running:
            try:
                id, styles = self.style_queue.get(block=True, timeout=0.1)
            except:
                continue
            for s in styles:
                if self.charaUpdate(id, s):
                    count += 1
        return count

    def artCheck(self, id, style, uncaps): # build a list of flags for each uncap levels to determine what kind of arts to expect
        flags = {}
        for uncap in uncaps + ["81", "82", "83", "91", "92", "93"]:
            for g in ["_1", ""]:
                if flags.get(uncap, [False, False, False])[0]: continue
                for m in ["_101", ""]:
                    if flags.get(uncap, [False, False, False])[1]: continue
                    for n in ["_01", ""]:
                        if flags.get(uncap, [False, False, False])[2]: continue
                        try:
                            self.req(self.imgUri + "_low/sp/assets/npc/m/" + id + "_" + uncap + style + g + m + n + ".jpg")
                            if uncap not in flags:
                                flags[uncap] = [False, False, False]
                            flags[uncap][0] = flags[uncap][0] or (g == "_1")
                            flags[uncap][1] = flags[uncap][1] or (m == "_101")
                            flags[uncap][2] = flags[uncap][2] or (n == "_01")
                        except:
                            pass
        return flags

    def manualUpdate(self, ids): # called by -update or other function. manually update elements
        if len(ids) == 0:
            return
        self.running = True
        with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
            futures = [executor.submit(self.styleProcessing), executor.submit(self.styleProcessing)]
            for id in range(100): futures.append(executor.submit(self.bulkRequest))
            tcounter = len(futures)
            for id in ids:
                if len(id) >= 10:
                    if id.startswith('2'):
                        futures.append(executor.submit(self.sumUpdate, id))
                    elif id.startswith('10'):
                        futures.append(executor.submit(self.weapUpdate, id))
                    elif id.startswith('39') or id.startswith('305'):
                        try: scenes = set(self.data["npcs"][id][0])
                        except: scenes = set()
                        futures.append(executor.submit(self.update_all_scene_sub, "npcs", id, None, scenes))
                    elif id.startswith('3'):
                        el = id.split('_')
                        if len(el) == 2:
                            futures.append(executor.submit(self.charaUpdate, el[0], '_'+el[1]))
                        else:
                            futures.append(executor.submit(self.charaUpdate, id))
                    else:
                        pass
                else:
                    futures.append(executor.submit(self.mobUpdate, id))
            tfinished = 0
            tcounter = len(futures) - tcounter
            if tcounter > 0: print("Attempting to update", tcounter, "element(s)")
            else: self.running = False
            for future in concurrent.futures.as_completed(futures):
                future.result()
                tfinished += 1
                if tfinished == tcounter:
                    print("Progress: 100%")
                    self.running = False
                elif tfinished < tcounter and tfinished % 10 == 0:
                    print("Progress: {:.1f}%".format(100 * tfinished / tcounter))
        self.save()
        self.running = False
        print("Done")

    # index chara/skin data
    def charaUpdate(self, id, style=""):
        data = [[], [], [], [], [], [], [], None, None] # sprite, phit, sp, aoe, single, general, sd, scene, sound
        uncaps = []
        sheets = []
        altForm = False
        # # # Main sheets
        tid = self.chara_special.get(id, id) # special substitution (mostly for bobobo)
        for uncap in ["01", "02", "03", "04"]:
            for ftype in ["", "_s2"]:
                for form in ["", "_f", "_f1", "_f_01"]:
                    try:
                        fn = "npc_{}_{}{}{}{}".format(tid, uncap, style, form, ftype)
                        sheets += self.processManifest(fn)
                        if form == "": uncaps.append(uncap)
                        else: altForm = True
                    except:
                        if form == "":
                            break
        data[0] = sheets
        if len(uncaps) == 0 and id+style not in self.cut_ids:
            return False
        # # # Assets
        # arts
        flags = self.artCheck(id, style, uncaps)
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
        data[5] = targets
        data[6] = sd
        if len(targets) == 0:
            return False
        if not id.startswith("371") and style == "":
            self.style_queue.put((id, ["_st2"])) # style check
        # # # Other sheets
        # attack
        targets = [""]
        for i in range(2, len(uncaps)):
            targets.append("_" + uncaps[i])
        attacks = []
        for t in targets:
            try:
                fn = "phit_{}{}{}".format(tid, t, style)
                attacks += self.processManifest(fn)
            except:
                break
        data[1] = attacks
        # ougi
        attacks = []
        for uncap in uncaps:
            for form in (["", "_f", "_f1", "_f_01"] if altForm else [""]):
                for catype in ["", "_s2", "_s3"]:
                    try:
                        fn = "nsp_{}_{}{}{}{}".format(tid, uncap, style, form, catype)
                        attacks += self.processManifest(fn)
                        break
                    except:
                        pass
        data[2] = attacks
        # skills
        attacks = []
        for el in ["01", "02", "03", "04", "05", "06", "07", "08"]:
            try:
                fn = "ab_all_{}{}_{}".format(tid, style, el)
                attacks += self.processManifest(fn)
            except:
                pass
        data[3] = attacks
        attacks = []
        for el in ["01", "02", "03", "04", "05", "06", "07", "08"]:
            try:
                fn = "ab_{}{}_{}".format(tid, style, el)
                attacks += self.processManifest(fn)
            except:
                pass
        data[4] = attacks
        # scenes and sounds
        uncaps = [u for u in uncaps if ("_" not in u and u.startswith("0"))] # format uncaps (remove useless ones)
        try: scenes = set(self.data['characters'][id+style][7])
        except: scenes = set()
        pending = self.request_scene_bulk(id+style, uncaps, scenes)
        try: voices = set(self.data['characters'][id+style][8])
        except: voices = set()
        data[8] = self.update_chara_sound_file(id+style, uncaps, voices)
        data[7] = self.process_scene_bulk(pending)
        with self.lock:
            self.modified = True
            if tid.startswith('37'):
                self.data['skins'][id+style] = data
            else:
                self.data['characters'][id+style] = data
            self.addition[id+style] = 3
        self.generateNameLookup(id+style)
        return True
        
    # index summon data
    def sumUpdate(self, id):
        data = [[], [], []] # general, call, damage
        uncaps = []
        # main sheet
        for uncap in ["", "_02", "_03", "_04"]:
            try:
                fn = "{}_{}".format(id, uncap)
                self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/m/{}{}.jpg".format(id, uncap))
                data[0].append("{}{}".format(id, uncap))
                uncaps.append("01" if uncap == "" else uncap[1:])
            except:
                break
        if len(uncaps) == 0 and id not in self.cut_ids:
            return False
        multi = [""] if id not in self.multi_summon else ["", "_a", "_b", "_c", "_d", "_e"]
        # attack
        for u in uncaps:
            for m in multi:
                try:
                    fn = "summon_{}_{}{}_attack".format(id, u, m)
                    data[1] += self.processManifest(fn)
                except:
                    pass
        # damage
        for u in uncaps:
            for m in multi:
                try:
                    fn = "summon_{}_{}{}_damage".format(id, u, m)
                    data[2] += self.processManifest(fn)
                except:
                    pass
        with self.lock:
            self.modified = True
            self.data['summons'][id] = data
            self.addition[id] = 2
        self.generateNameLookup(id)
        return True

    # index weapon data
    def weapUpdate(self, id):
        data = [[], [], []] # general, phit, sp
        # art
        try:
            self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/weapon/ls/{}.jpg".format(id))
            data[0].append("{}".format(id))
        except:
            return False
        # attack
        try:
            fn = "phit_{}".format(id)
            data[1] += self.processManifest(fn)
        except:
            pass
        # ougi
        for u in ["", "_0", "_1", "_0_s2", "_1_s2", "_0_s3", "_1_s3"]:
            try:
                fn = "sp_{}{}".format(id, u)
                data[2] += self.processManifest(fn)
            except:
                pass
        with self.lock:
            self.modified = True
            self.data['weapons'][id] = data
            self.addition[id] = 1
        self.generateNameLookup(id)
        return True

    # index enemy data
    def mobUpdate(self, id):
        data = [[], [], [], [], [], []] # general, sprite, appear, ehit, esp, esp_all
        # icon
        try:
            self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/enemy/s/{}.png".format(id))
            data[0].append("{}".format(id))
        except:
            return False
        # sprite
        try:
            fn = "enemy_{}".format(id)
            data[1] += self.processManifest(fn)
        except:
            pass
        # appear
        try:
            fn = "raid_appear_{}".format(id)
            data[2] += self.processManifest(fn)
        except:
            pass
        # ehit
        try:
            fn = "ehit_{}".format(id)
            data[3] += self.processManifest(fn)
        except:
            pass
        # esp
        for i in range(0, 20):
            try:
                fn = "esp_{}_{}".format(id, str(i).zfill(2))
                data[4] += self.processManifest(fn)
            except:
                pass
            try:
                fn = "esp_{}_{}_all".format(id, str(i).zfill(2))
                data[5] += self.processManifest(fn)
            except:
                pass
        with self.lock:
            self.modified = True
            self.data['enemies'][id] = data
            self.addition[id] = 4
        return True

    # called once. generate a list of string to check for npc data
    def build_scene_strings(self):
        expressions = ["", "_laugh", "_laugh2", "_laugh3", "_wink", "_shout", "_shout2", "_sad", "_sad2", "_angry", "_angry2", "_school", "_shadow", "_close", "_serious", "_serious2", "_surprise", "_surprise2", "_think", "_think2", "_serious", "_serious2", "_mood", "_mood2", "_ecstasy", "_ecstasy2", "_ef", "_body", "_speed2", "_suddenly", "_shy", "_shy2", "_weak"]
        variationsA = ["", "_a", "_b", "_battle"]
        variationsB = ["", "_speed", "_up"]
        specials = ["_up_speed", "_valentine", "_valentine_a", "_a_valentine", "_valentine2", "_valentine3", "_white", "_whiteday", "_whiteday2", "_whiteday3"]
        scene_alts = []
        for A in variationsA:
            for ex in expressions:
                for B in variationsB:
                    scene_alts.append(A+ex+B)
        return scene_alts, specials

    def bulkRequest(self): # used to make threaded requests for npc data retrieval
        while self.running:
            try:
                base_url, id, suffix, data = self.request_queue.get(block=True, timeout=0.1)
            except:
                time.sleep(0.1)
                continue
            try:
                self.req(base_url.format(id, suffix))
                data[suffix] = True
            except:
                data[suffix] = False

    def update_scene_file(self, id, uncaps = None, existing = set()):  # return npc data for chara/skin/npc (the function is divided in two, see below)
        r = self.request_scene_bulk(id, uncaps, existing)
        if r is not None:
            l = 1 if uncaps is None else len(uncaps)
            time.sleep(5+10*l) # take a break, waiting for the requests to go through
            res = self.process_scene_bulk(r)
            if res is not None and len(res) > 0 and (id.startswith('399') or id.startswith('305')):
                with self.lock:
                    self.addition[id] = 5
                    self.modified = True
            return res
        return None

    def request_scene_bulk(self, id, uncaps = None, existing = set()):
        try:
            scene_alts = []
            if uncaps is None:
                uncaps = [""]
            for uncap in uncaps:
                if uncap == "01": uncap = ""
                elif uncap != "": uncap = "_" + uncap
                for s in self.scene_strings:
                    scene_alts.append(uncap+s)
            scene_alts += self.scene_special_strings
            if id.startswith("305"):
                scene_alts += ["_birthday", "_birthday2", "_birthday3", "_birthday3_a", "_birthday3_b"]
            result = {}
            for s in scene_alts:
                if s in existing:
                    result[s] = True
                else:
                    result[s] = None
            for s in result:
                if result[s] is None:
                    self.request_queue.put(("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/quest/scene/character/body/{}{}.png", id, s, result))
            for s in scene_alts:
                self.request_queue.put(("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/quest/scene/character/body/{}{}.png", id, s, result))
            return result
        except:
            return None

    def process_scene_bulk(self, result):
        try:
            if result is None: return None
            while True:
                has_none = False
                for k, v in result.items():
                    if v is None:
                        has_none = True
                        break
                if not has_none: break
                time.sleep(5)
            result = [k for k, v in result.items() if v == True]
            return result
        except:
            return None

    def update_all_sound(self): # update sound data for every character
        self.running = True
        print("Updating sound data...")
        to_update = {}
        for k in ["characters", "skins"]:
            to_update[k] = []
            for id in self.data[k]:
                uncaps = []
                for u in self.data[k][id][5]:
                    uu = u.replace(id+"_", "")
                    if "_" not in uu and uu.startswith("0") and uu != "02":
                        uncaps.append(uu)
                try: voices = set(self.data[k][id][8])
                except: voices = set()
                to_update[k].append((id, uncaps, voices))
        with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
            futures = []
            for k in to_update:
                for e in to_update[k]:
                    futures.append(executor.submit(self.update_all_sound_sub, k, e[0], e[1], e[2]))
            count = 0
            countmax = len(futures)
            print(countmax, "element(s) to update...")
            if countmax == 0:
                self.running = False
            for future in concurrent.futures.as_completed(futures):
                future.result()
                count += 1
                if count < countmax and count % 20 == 0:
                    print("Progress: {:.1f}%".format(100*count/countmax))
                elif count == countmax:
                    print("Progress: 100%")
                    self.running = False
        self.save()
        print("Done")

    def update_all_sound_sub(self, index, id, uncaps, voices): # subroutine
        if index not in ["characters", "skins"]: return
        r = self.update_chara_sound_file(id, uncaps, voices)
        if len(self.data[index][id]) == 8: self.data[index][id].append(None)
        if r is not None:
            with self.lock:
                self.modified = True
                self.data[index][id][8] = r # character

    def update_chara_sound_file(self, id, uncaps = None, existing = set()): # result all sounds (not multithreaded)
        result = []
        if uncaps is None:
            uncaps = [""]
        # standard stuff
        for uncap in uncaps:
            if uncap == "01": uncap = ""
            elif uncap == "02": continue # seems unused
            elif uncap != "": uncap = "_" + uncap
            for mid, Z in [("_", 3), ("_v_", 3), ("_introduce", 1), ("_mypage", 1), ("_formation", 2), ("_evolution", 2), ("_archive", 2), ("_zenith_up", 2), ("_kill", 2), ("_ready", 2), ("_damage", 2), ("_healed", 2), ("_dying", 2), ("_power_down", 2), ("_cutin", 1), ("_attack", 1), ("_ability_them", 1), ("_ability_us", 1), ("_mortal", 1), ("_win", 1), ("_lose", 1), ("_to_player", 1)]:
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
                searching = True
                err = 0
                while searching:
                    exists = False
                    for suffix in suffixes:
                        f = "{}{}{}{}".format(uncap, mid, str(A).zfill(Z), suffix)
                        if f in existing:
                            result.append(f)
                            exists = True
                            err = 0
                            break
                    if not exists:
                        for suffix in suffixes:
                            try:
                                f = "{}{}{}{}".format(uncap, mid, str(A).zfill(Z), suffix)
                                self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/sound/voice/{}{}.mp3".format(id, f))
                                result.append(f)
                                if suffix in ["a", "_a", "_1"]: # gender stuff
                                    try:
                                        f = "{}{}{}{}".format(uncap, mid, str(A).zfill(Z), suffix.replace('a', 'b').replace('1', '2'))
                                        self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/sound/voice/{}{}.mp3".format(id, f))
                                        result.append(f)
                                    except:
                                        pass
                                err = 0
                                break
                            except:
                                if suffix == suffixes[-1] and A > 0:
                                    err += 1
                                    if err >= max_err:
                                        searching = False
                    A += 1
        # chain burst
        try:
            f = "_chain_start"
            if f not in existing: self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/sound/voice/{}{}.mp3".format(id, f))
            result.append(f)
        except:
            pass
        try:
            f = "_chain{}_{}".format(1, 2)
            if f not in existing: self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/sound/voice/{}{}.mp3".format(id, f))
            for A in range(1, 7):
                for B in range(2, 5):
                    result.append("_chain{}_{}".format(A, B))
        except:
            pass
        # banter
        A = 1
        B = 1
        Z = None
        while True:
            success = False
            for i in range(1, 3):
                if Z is None or Z == i:
                    try:
                        f = "_pair_{}_{}".format(A, str(B).zfill(i))
                        if f not in existing: self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/sound/voice/{}{}.mp3".format(id, f))
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
        # seasonal scenes
        flags = set()
        for suffix in [("_birthday", 1), ("_Birthday", 1), ("_birthday_mypage", 1), ("_newyear_mypage", 1), ("_newyear", 1), ("_Newyear", 1), ("_valentine_mypage", 1), ("_valentine", 1), ("_Valentine", 1), ("_white_mypage", 1), ("_whiteday", 1), ("_WhiteDay", 1), ("_halloween_mypage", 1), ("_halloween", 1), ("_Halloween", 1), ("_christmas_mypage", 1), ("_christmas", 1), ("_Christmas", 1), ("_xmas", 1), ("_Xmas", 1)]:
            if "valentine" in suffix[0].lower():
                t = "valentine"
            elif "white" in suffix[0].lower():
                t = "white"
            elif "birth" in suffix[0].lower():
                t = "birthday"
            elif "halloween" in suffix[0].lower():
                t = "halloween"
            elif "newyear" in suffix[0].lower():
                t = "newyear"
            elif "mas" in suffix[0].lower():
                t = "christmas"
            if t in flags: continue
            A = 0
            while True:
                try:
                    f = suffix[0] + str(A)
                    if f not in existing: self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/sound/voice/{}{}.mp3".format(id, f))
                    result.append(f)
                except:
                    break
                A += 1
            if A > 0:
                flags.add(t)
        for suffix in ["white","newyear","valentine","christmas","halloween","birthday"]:
            #if suffix not in flags: continue
            for s in range(1, 6):
                exists = False
                for A in range(1, 10): # check if already indexed
                    if "_s{}_{}{}".format(s, suffix, A) in existing:
                        exists = True
                        break
                if exists: continue
                exists = False
                err = 0
                A = 1
                while err < 5:
                    try:
                        f = "_s{}_{}{}".format(s, suffix, A)
                        self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/sound/voice/{}{}.mp3".format(id, f))
                        result.append(f)
                        success = True
                        err = 0
                        exists = True
                    except:
                        err += 1
                    A += 1
                if not exists:
                    break
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

    # extract json data from a manifest file
    def processManifest(self, file):
        manifest = self.req(self.manifestUri + file + ".js", get=True).decode('utf-8')
        st = manifest.find('manifest:') + len('manifest:')
        ed = manifest.find(']', st) + 1
        data = json.loads(manifest[st:ed].replace('Game.imgUri+', '').replace('src:', '"src":').replace('type:', '"type":').replace('id:', '"id":'))
        res = []
        for l in data:
            src = l['src'].split('?')[0].split('/')[-1]
            res.append(src)
        return res

    # remove extra from wiki name
    def cleanName(self, name):
        for k in ['(Grand)', '(Yukata)', '(Summer)', '(Valentine)', '(Holiday)', '(Halloween)', '(SSR)', '(Fire)', '(Water)', '(Earth)', '(Wind)', '(Light)', '(Dark)', '(Grand)', '(Event SSR)', '(Event)', '(Promo)']:
            name = name.replace(k, '')
        return name.strip()

    # check id on the wiki to retrieve element name
    def generateNameLookup(self, cid):
        if not cid.startswith("20") and not cid.startswith("10") and not cid.startswith("30"): return
        r = self.req("https://gbf.wiki/index.php?search={}".format(cid), get=True)
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
                self.generateNameLookup_sub(cid, m)
            else: # CN wiki fallback
                try:
                    r = self.req("https://gbf.huijiwiki.com/wiki/{}/{}".format({"3":"Char","2":"Summon","1":"Weapon"}[cid[0]], cid), get=True)
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
                                self.generateNameLookup_sub(cid, str(r)[a:b])
                except:
                    pass

    # subroutine. read the wiki page to extract element ata
    def generateNameLookup_sub(self, cid, wiki_lookup):
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
            return
        match cid[2]:
            case '1': data['Rarity'] = 'N'
            case '2': data['Rarity'] = 'R'
            case '3': data['Rarity'] = 'SR'
            case '4': data['Rarity'] = 'SSR'
        try:
            r = self.req("https://gbf.wiki/{}".format(wiki_lookup.replace(' ', '_')), get=True)
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
            if (data["What"] == "Weapon" and len(data.keys()) > 3) or (data["What"] != "Weapon" and len(data.keys()) > 2):
                with self.lock:
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

    def buildLookup(self): # build a list of element to lookup on the wiki
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            print("Checking elements in need of update...")
            futures = []
            for t in ['characters', 'summons', 'weapons']:
                for k in self.data[t]:
                    if k not in self.data['lookup'] or self.data['lookup'][k] is None:
                        if k in self.other_lookup:
                            self.data['lookup'][k] = self.other_lookup[k]
                            self.modified = True
                        else:
                            futures.append(executor.submit(self.generateNameLookup, k))
            count = 0
            countmax = len(futures)
            print(countmax, "element(s) to update...")
            if countmax > 0:
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    count += 1
                    if count % 100 == 0:
                        print("Progress: {:.1f}%".format(100*count/countmax))
        # second pass
        for t in ['characters', 'summons', 'weapons']:
            for k in self.data[t]:
                if k not in self.data['lookup'] or self.data['lookup'][k] is None:
                    for l in self.lookup_group:
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
        self.running = False
        print("Done")

    def manualLookup(self): # for manual lookup. used as a last resort
        for t in ['characters', 'summons', 'weapons']:
            for k in self.data[t]:
                if k not in self.data['lookup'] or self.data['lookup'][k] is None:
                    print("##########################################")
                    print("Input the Wiki URL string for ID", k, "(Leave blank to skip)")
                    while True:
                        s = input()
                        if s == "": break
                        if not self.generateNameLookup_sub(k, s):
                            print("Page not found, try again")
                        else:
                            break
        self.save()
        print("Done")

    def update_all_scene(self, full=False): # update npc data for every element (if full is true) or every non indexed elements
        self.running = True
        print("Updating scene data...")
        to_update = {}
        to_update["npcs"] = []
        for id in self.data["npcs"]:
            if isinstance(self.data["npcs"][id], int) or full or self.data["npcs"][id][0] is None or len(self.data["npcs"][id][0]) == 0:
                try: scenes = set(self.data["npcs"][id][0])
                except: scenes = set()
                to_update["npcs"].append((id, None, scenes))
        for k in ["characters", "skins"]:
            to_update[k] = []
            for id in self.data[k]:
                if not isinstance(self.data[k][id], int) and (full or (len(self.data[k][id]) >= 8 and (self.data[k][id][7] is None or len(self.data[k][id][7]) == 0))):
                    uncaps = []
                    for u in self.data[k][id][5]:
                        uu = u.replace(id+"_", "")
                        if "_" not in uu and uu.startswith("0"):
                            uncaps.append(uu)
                    try: scenes = set(self.data["npcs"][id][7])
                    except: scenes = set()
                    to_update[k].append((id, uncaps, scenes))
        with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
            futures = []
            for k in range(100): futures.append(executor.submit(self.bulkRequest))
            countmax = len(futures)
            for k in to_update:
                for e in to_update[k]:
                    futures.append(executor.submit(self.update_all_scene_sub, k, e[0], e[1], e[2]))
            count = 0
            countmax = len(futures) - countmax
            print(countmax, "element(s) to update...")
            if countmax == 0:
                self.running = False
            for future in concurrent.futures.as_completed(futures):
                future.result()
                count += 1
                if count < countmax and count % 50 == 0:
                    print("Progress: {:.1f}%".format(100*count/countmax))
                elif count == countmax:
                    print("Progress: 100%")
                    self.running = False
        self.save()
        print("Done")

    def update_all_scene_sub(self, index, id, uncaps, scenes): # subroutine
        r = self.update_scene_file(id, uncaps, scenes)
        if r is not None:
            with self.lock:
                self.modified = True
                if index == "npcs":
                    self.data[index][id] = [r]
                else:
                    self.data[index][id][7] = r

    def get_relation(self, eid): # retrieve element relation
        try:
            page = self.req("https://gbf.wiki/index.php?search={}".format(eid), get=True)
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
                page = self.req("https://gbf.wiki" + link, get=True)
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
                    for sid in self.re.findall(page[a:b]):
                        if sid != eid:
                            ids.add(sid)
                b = 0
                while True:
                    a = page.find("wikitable", b)
                    if a == -1: break
                    a += len("wikitable")
                    b = page.find("</table>", a)
                    for sid in self.re.findall(page[a:b]):
                        if sid != eid:
                            ids.add(sid)
                return eid, list(ids)
            except:
                return eid, []

    def build_relation(self, to_update=[]): # build a list of relation to update and call get_relation
        try:
            with open("json/relation_name.json", "r") as f:
                self.name_table = json.load(f)
            print("Element name table loaded")
        except:
            self.name_table = {}
        self.name_table_modified = False
        try:
            with open("json/relation.json", "r") as f:
                relation = json.load(f)
            print("Existing relationships loaded")
        except:
            relation = {}
        futures = []
        new = []
        modified = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            if len(to_update) == 0:
                for eid in self.data['characters']:
                    if eid not in relation or len(relation[eid]) == 0:
                        futures.append(executor.submit(self.get_relation, eid))
                for eid in self.data['summons']:
                    if eid not in relation:
                        futures.append(executor.submit(self.get_relation, eid))
                for eid in self.data['weapons']:
                    if eid not in relation:
                        futures.append(executor.submit(self.get_relation, eid))
            else:
                for eid in to_update:
                    futures.append(executor.submit(self.get_relation, eid))
            if len(futures) == 0: return
            print("Checking for new relationships...")
            for future in concurrent.futures.as_completed(futures):
                r = future.result()
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
                        modified = True
                    if n not in relation[eid]:
                        relation[eid].append(n)
                        relation[eid].sort()
                        modified = True
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
                            modified = True
                        for oid in self.name_table[k]:
                            if oid == eid or oid in relation[eid]: continue
                            relation[eid].append(oid)
                            relation[eid].sort()
                            modified = True
                if modified:
                    try:
                        with open("json/relation.json", "w") as f:
                            json.dump(relation, f, sort_keys=True, indent='\t', separators=(',', ':'))
                        print("Relationships updated")
                    except:
                        pass
            if self.name_table_modified:
                try:
                    with open("json/relation_name.json", "w") as f:
                        json.dump(self.name_table, f, sort_keys=True, indent='\t', separators=(',', ':'))
                    print("Name table updated")
                except:
                    pass

    def connect_relation(self, As, B): # connect relation between element A and B
        try:
            with open("json/relation_name.json", "r") as f:
                self.name_table = json.load(f)
            print("Element name table loaded")
        except:
            self.name_table = {}
        self.name_table_modified = False
        try:
            with open("json/relation.json", "r") as f:
                relation = json.load(f)
            print("Existing relationships loaded")
        except:
            relation = {}
        print("Trying to add relation...")
        modified = False
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
            modified = True
            for eid in relation[A]:
                if eid not in relation:
                    relation[eid] = []
                if A not in relation[eid]:
                    relation[eid].append(A)
                    relation[eid].sort()
            relation[A].sort()
        if modified:
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
            try:
                with open("json/relation.json", "w") as f:
                    json.dump(relation, f, sort_keys=True, indent='\t', separators=(',', ':'))
                print("Relationships updated")
            except:
                pass

    def relation_edit(self): # manual edit mode for relation
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
                            self.build_relation([x for x in s.split(' ') if x != ''])
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

    def gbfversion(self):
        try:
            res = self.req('https://game.granbluefantasy.jp/', headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36', 'Accept-Language':'en', 'Host':'game.granbluefantasy.jp', 'Connection':'keep-alive'}, get=True)
            res = res.decode('utf-8')
            return int(self.vregex.findall(res)[0])
        except:
            try:
                if 'maintenance' in res.lower(): return "maintenance"
            except:
                pass
            return None

    def wait(self):
        v = self.gbfversion()
        if v is None:
            print("Impossible to currently access the game.\nWait and try again.")
            exit(0)
        elif v == "maintenance":
            print("Game is in maintenance")
            exit(0)
        print("Waiting update, ctrl+C to cancel...")
        while True:
            t = int(datetime.now(timezone.utc).replace(tzinfo=None).timestamp()) % 300
            if 300 - t > 10:
                time.sleep(10)
            else:
                time.sleep(310 - t)
                n = self.gbfversion()
                if isinstance(n, int) and n != v:
                    print("Update detected.")
                    return

    def debug_output_scene_strings(self, recur=False):
        print("Exporting all scene file suffixes...")
        keys = set()
        errs = []
        for x in ["characters", "skins"]:
            d = self.data[x]
            for k, v in d.items():
                try:
                    if isinstance(v, list) and isinstance(v[7], list):
                        for e in v[7]:
                            if e[:3] in ["_02", "_03", "_04", "_05"]: keys.add(e[3:])
                            else: keys.add(e)
                except:
                    errs.append(k)
        for x in ["npcs"]:
            for k, v in self.data[x].items():
                try:
                    if isinstance(v, list) and isinstance(v[0], list):
                        for e in v[0]:
                            if e[:3] in ["_02", "_03", "_04", "_05"]: keys.add(e[3:])
                            else: keys.add(e)
                except:
                    errs.append(k)
        if len(errs) > 0: # refresh elements with errors
            if recur:
                print("Still", len(errs), "elements incorrectly formed, manual debugging is necessary")
            else:
                tmp = self.update_changelog
                self.update_changelog = False
                print(len(errs), "elements incorrectly formed, attempting to update")
                self.manualUpdate(errs)
                self.debug_output_scene_strings()
                self.update_changelog = tmp
        else:
            keys = list(keys)
            keys.sort()
            with open("json/debug_scene_strings.json", mode="w", encoding="utf-8") as f:
                json.dump(keys, f)
            print("Data exported to 'json/debug_scene_strings.json'")

def print_help():
    print("Usage: python parser.py [option]")
    print("options:")
    print("-run       : Update the index with new content.")
    print("-update    : Manual JSON updates (Followed by IDs to check).")
    print("-updaterun : Like '-update' but also do '-run' after.")
    print("-index     : Check the index for missing content.")
    print("-job       : Search additional class related data (Very time consuming).")
    print("-jobedit   : Manually edit job data (Command Line Menu).")
    print("-lookup    : Update the lookup table (Time Consuming).")
    print("-lookupfix : Manually edit the lookup table.")
    print("-relation  : Update the relationship index.")
    print("-relinput  : Update to relationships.")
    print("-listjob   : List indexed spritesheet Job IDs. You can add specific Mainhand ID to filter the list.")
    print("-scene     : Update scene index for characters/npcs with missing data (Time consuming).")
    print("-scenefull : Update scene index for every characters/npcs (Very time consuming).")
    print("-sound     : Update sound index for characters (Very ime consuming).")
    print("-wait      : Wait an in-game update (Must be the first parameter, usable with others).")
    print("-nochange  : Disable the update of changelog.json (Must be the first parameter or after -wait, usable with others).")
    time.sleep(2)

if __name__ == '__main__':
    p = Parser()
    argv = sys.argv.copy()
    # debug stuff
    if "-debug_scene" in argv:
        p.debug_output_scene_strings()
    else:
        # normal stuff
        if len(argv) > 1 and argv[1] == "-wait":
            argv.pop(1)
            p.wait()
        if len(argv) > 1 and argv[1] == "-nochange":
            argv.pop(1)
            p.update_changelog = False
        if len(argv) < 2:
            print_help()
        else:
            if argv[1] == '-run':
                p.run()
            elif argv[1] == '-updaterun':
                if len(argv) == 2:
                    print_help()
                else:
                    p.manualUpdate(argv[2:])
                    p.run()
            elif argv[1] == '-update':
                if len(argv) == 2:
                    print_help()
                else:
                    p.manualUpdate(argv[2:])
            elif argv[1] == '-index':
                p.run_index_content()
            elif argv[1] == '-job':
                p.search_job_detail()
            elif argv[1] == '-jobedit':
                p.edit_job()
            elif argv[1] == '-lookup':
                p.buildLookup()
            elif argv[1] == '-lookupfix':
                p.manualLookup()
            elif argv[1] == '-relation':
                p.build_relation()
            elif argv[1] == '-relinput':
                p.relation_edit()
            elif argv[1] == '-listjob':
                if len(argv) == 2:
                    p.listjob()
                else:
                    p.listjob(argv[2:])
            elif argv[1] == '-scene':
                p.update_all_scene()
            elif argv[1] == '-scenefull':
                p.update_all_scene(True)
            elif argv[1] == '-sound':
                p.update_all_sound()
            else:
                print_help()