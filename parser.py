import httpx
import json
import concurrent.futures
from threading import Lock
import sys
import queue
import time
import string
import re
from datetime import datetime, timezone

# parser to generate json files (characters/skins only for now) and to index a list of all existing character, etc
class Parser():
    def __init__(self):
        self.running = False
        self.queue = queue.Queue()
        self.quality = ("/img/", "/js/")
        self.data = {
            "characters":{},
            "summons":{},
            "weapons":{},
            "enemies":{},
            "skins":{},
            "job":{},
            "npcs":{},
            "background":{},
            "title":{}
        }
        self.lock = Lock()
        self.modified = False
        self.null_characters = ["3030182000", "3710092000", "3710139000", "3710078000", "3710105000", "3710083000", "3020072000", "3710184000"]
        self.multi_summon = ["2040414000"]
        self.chara_special = {"3710171000":"3710167000","3710170000":"3710167000","3710169000":"3710167000","3710168000":"3710167000"}
        self.new_elements = []
        self.name_table = {}
        self.name_table_modified = False
        self.name_lock = Lock()
        self.re = re.compile("[123][07][1234]0\\d{4}00")
        
        limits = httpx.Limits(max_keepalive_connections=300, max_connections=300, keepalive_expiry=10)
        self.client = httpx.Client(http2=False, limits=limits)
        self.manifestUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/model/manifest/"
        self.cjsUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/cjs/"
        self.imgUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img"
        self.endpoint = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/"
        
        self.load()
        self.exclusion = set([])

    def load(self): # load data.json
        try:
            with open('json/data.json', mode='r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict): return
            for k in data:
                self.data[k] = data.get(k, {})
        except Exception as e:
            print(e)

    def save(self): # save data.json
        try:
            if self.modified:
                self.modified = False
                with open('json/data.json', mode='w', encoding='utf-8') as outfile:
                    json.dump(self.data, outfile)
                print("data.json updated")
                with open('json/changelog.json', mode='w', encoding='utf-8') as outfile:
                    json.dump({'timestamp':int(datetime.now(timezone.utc).timestamp()*1000)}, outfile)
                print("changelog.json updated")
        except Exception as e:
            print(e)

    def newShared(self, errs):
        errs.append([])
        errs[-1].append(0)
        errs[-1].append(True)
        errs[-1].append(Lock())

    def run(self):
        errs = []
        possibles = []
        self.new_elements = []
        
        #rarity
        for r in range(1, 5):
            # characters
            if r > 1:
                self.newShared(errs)
                for i in range(2):
                    possibles.append(('characters', i, 2, errs[-1], "30"+str(r)+"0{}000", 3, "img_low/sp/assets/npc/m/", "_01{}.jpg", ["", "_st2"]))
            # summons
            self.newShared(errs)
            for i in range(2):
                possibles.append(('summons', i, 2, errs[-1], "20"+str(r)+"0{}000", 3, "img_low/sp/assets/summon/m/", ".jpg"))
            # weapons
            for j in range(10):
                self.newShared(errs)
                for i in range(2):
                    possibles.append(('weapons', i, 2, errs[-1], "10"+str(r)+"0{}".format(j) + "{}00", 3, "img_low/sp/assets/weapon/m/", ".jpg"))
        # skins
        self.newShared(errs)
        for i in range(2):
            possibles.append(('skins', i, 2, errs[-1], "3710{}000", 3, "img_low/sp/assets/npc/m/", "_01.jpg"))
        # enemies
        for a in range(1, 10):
            for b in range(1, 4):
                for d in [1, 2, 3]:
                    self.newShared(errs)
                    possibles.append(('enemies', 0, 1, errs[-1], str(a) + str(b) + "{}" + str(d), 4, "img/sp/assets/enemy/s/", ".png", [""], 40))
        # npc
        self.newShared(errs)
        for i in range(5):
            possibles.append(('npcs', i, 5, errs[-1], "399{}000", 4, "img_low/sp/quest/scene/character/body/", ".png", [""], 80))
        
        # backgrounds
        self.newShared(errs)
        for i in range(2):
            possibles.append(('background', i, 2, errs[-1], "event_{}", 1, "img_low/sp/raid/bg/", ".jpg", [""], 10))
        self.newShared(errs)
        for i in range(2):
            possibles.append(('background', i, 2, errs[-1], "common_{}", 3, "img_low/sp/raid/bg/", ".jpg", [""], 10))
        self.newShared(errs)
        for i in range(2):
            possibles.append(('background', i, 2, errs[-1], "main_{}", 1, "img_low/sp/guild/custom/bg/", ".png", [""], 10))
        for i in ["ra", "rb", "rc"]:
            self.newShared(errs)
            possibles.append(('background', 0, 1, errs[-1], "{}"+i, 1, "img_low/sp/raid/bg/", "_1.jpg", [""], 50))
        for i in [("e", ""), ("e", "r"), ("f", ""), ("f", "r"), ("f", "ra"), ("f", "rb"), ("f", "rc"), ("e", "r_3_a"), ("e", "r_4_a")]:
            self.newShared(errs)
            possibles.append(('background', 0, 1, errs[-1], i[0]+"{}"+i[1], 3, "img_low/sp/raid/bg/", "_1.jpg", [""], 50))
        
        # titles
        self.newShared(errs)
        possibles.append(('title', 0, 1, errs[-1], "{}", 1, "img_low/sp/top/bg/bg_", ".jpg", [""], 20))
        
        thread_count = len(possibles)+40
        
        print("Starting index update... (", thread_count, " threads )")
        with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
            # jop threads
            futures = self.job_search(executor)
            # start
            for p in possibles:
                futures.append(executor.submit(self.subroutine, self.getEndpoint(), *p))
            for future in concurrent.futures.as_completed(futures):
                future.result()
        print("Index update done")
        self.manualUpdate(self.new_elements)
        self.save()
        self.build_relation()

    def listjob(self, mhs=['sw', 'wa', 'kn', 'me', 'bw', 'mc', 'sp', 'ax', 'gu', 'kt']):
        job_index = {}
        mhs = set(mhs)
        try:
            with open('json/job.json', mode='r', encoding='utf-8') as f:
                job_index = json.load(f)
        except:
            pass
        count = 0
        for k in job_index:
            if k.split('_')[1] in mhs:
                print(k)
                count += 1
        print(count, "result(s)")

    def dig_job_spritesheet(self, mhs=['sw', 'wa', 'kn', 'me', 'bw', 'mc', 'sp', 'ax', 'gu', 'kt']):
        job_index = {}
        try:
            with open('json/job.json', mode='r', encoding='utf-8') as f:
                job_index = json.load(f)
        except:
            pass
        existing_list = set()
        for k in job_index:
            existing_list.add(k.split('_')[0])
        shared = [Lock(), queue.Queue(), job_index]
        generate_queue = True
        i = 0
        while i < len(mhs):
            if len(mhs[i]) == 6 and mhs[i][3] == '_':
                generate_queue = False
                shared[1].put(mhs[i].split('_')[0])
                mhs[i] = mhs[i].split('_')[1]
                i += 1
            elif len(mhs[i]) == 3:
                generate_queue = False
                shared[1].put(mhs[i])
                mhs.pop(i)
            else:
                i += 1
        if len(mhs) == 0:
            mhs = ['sw', 'wa', 'kn', 'me', 'bw', 'mc', 'sp', 'ax', 'gu', 'kt']
        if generate_queue:
            for a in string.ascii_lowercase:
                for b in string.ascii_lowercase:
                    for c in string.ascii_lowercase:
                        d = a+b+c
                        if d not in existing_list:
                            shared[1].put(a+b+c)
        print("Checking job spritesheets...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            for count in range(100):
                futures.append(executor.submit(self.dig_job_spritesheet_subroutine, shared, mhs))
            for future in concurrent.futures.as_completed(futures):
                future.result()
        try:
            with open('json/job.json', mode='w', encoding='utf-8') as f:
                json.dump(shared[2], f)
            print("job.json updated")
        except:
            pass

    def dig_job_spritesheet_subroutine(self, shared, mhs):
        while shared[1].qsize() > 0:
            try:
                permut = shared[1].get(block=False)
            except:
                time.sleep(0.001)
                continue
            for mh in mhs:
                sheets = self.dig_job_spritesheet_image(permut, mh)
                if len(sheets) != 0:
                    print("Found:", permut, mh)
                    with shared[0]:
                        shared[2][permut + "_" + mh] = sheets

    def dig_job_spritesheet_image(self, permut, mh):
        sheets = []
        colors = [
            ['01', '02', '03', '04', '05'],
            ['80']
        ]
        for cl in colors:
            for col in cl:
                try:
                    sheets += self.processManifest("{}_{}_0_{}".format(permut, mh, col))
                except:
                    if col == '01': return sheets
        return sheets

    def subroutine(self, endpoint, index, start, step, err, file, zfill, path, ext, styles = [""], maxerr=20):
        id = start
        while err[0] < maxerr and err[1]:
            f = file.format(str(id).zfill(zfill))
            if f in self.data[index]:
                with err[2]:
                    err[0] = 0
                id += step
                continue
            for s in styles:
                try:
                    self.req(endpoint + path + f + ext.replace("{}", s))
                    with err[2]:
                        err[0] = 0
                        self.data[index][f + s] = 0
                        self.modified = True
                        self.new_elements.append(f + s)
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

    def job_search(self, executor):
        shared = [Lock(), queue.Queue(), False]
        lookup = list(self.data['job'])
        for i in range(10, 50):
            for j in range(0, 10):
                for k in range(0, 10):
                    id = "{}{}{}01".format(i, j, k)
                    exist = False
                    for jid in lookup:
                        if jid.startswith(id):
                            exist = True
                            break
                    if not exist:
                        shared[1].put(id)
        futures = []
        for i in range(40):
            futures.append(executor.submit(self.subroutine_job, self.getEndpoint(), shared))
        return futures

    def subroutine_job(self, endpoint, shared):
        mh = ['sw', 'wa', 'kn', 'me', 'bw', 'mc', 'sp', 'ax', 'gu', 'kt']
        while shared[1].qsize() > 0:
            try:
                id = shared[1].get(block=False)
            except:
                time.sleep(0.001)
                continue
            try:
                path = "img_low/sp/assets/leader/m/{}_01.jpg".format(id)
                self.req(endpoint + path)
            except:
                continue
            for mhid in mh:
                try:
                    path = "img_low/sp/assets/leader/sd/{}_{}_0_01.png".format(id, mhid)
                    self.req(endpoint + path)
                    with shared[0]:
                        self.data['job'][id + "_" + mhid] = 0
                        self.modified = True
                    break
                except:
                    pass
        with shared[0]:
            if not shared[2]:
                shared[2] = True
                print("Threads job are done")

    def dig_job_chargeattack(self):
        try:
            with open('json/job_ca.json', mode='r', encoding='utf-8') as f:
                index = set(json.load(f))
        except:
            index = set()
        shared = [Lock(), queue.Queue(), index]
        for i in range(10):
            count = 0
            j = 0
            while count < 10 and j < 1000:
                f = "1040{}{}00".format(i, str(j).zfill(3))
                if f in self.data["weapons"]:
                    count = 0
                else:
                    count += 1
                    shared[1].put(f)
                j += 1
        print("Checking job charge attacks...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            for count in range(100):
                futures.append(executor.submit(self.dig_job_chargeattack_subroutine, shared))
            for future in concurrent.futures.as_completed(futures):
                future.result()
        try:
            with open('json/job_ca.json', mode='w', encoding='utf-8') as f:
                json.dump(list(shared[2]), f)
            print("job_ca.json updated")
        except:
            pass

    def dig_job_chargeattack_subroutine(self, shared):
        while shared[1].qsize() > 0:
            try:
                file = shared[1].get(block=False)
            except:
                time.sleep(0.001)
                continue
            try:
                self.req(self.imgUri + '_low/sp/assets/weapon/m/' + file + ".jpg")
                continue
            except:
                pass
            for k in [["phit_", ""], ["sp_", "_1_s2"]]:
                try:
                    self.req(self.manifestUri + k[0] + file + k[1] + ".js")
                    print("Possible:", file)
                    with shared[0]:
                        shared[2].add(file)
                    break
                except:
                    pass

    def getEndpoint(self):
        return self.endpoint

    def req(self, url, headers={}, get=False):
        if get:
            response = self.client.get(url.replace('/img/', self.quality[0]).replace('/js/', self.quality[1]), headers={'connection':'keep-alive'} | headers, timeout=50)
        else:
            response = self.client.head(url.replace('/img/', self.quality[0]).replace('/js/', self.quality[1]), headers={'connection':'keep-alive'} | headers, timeout=50)
        if response.status_code != 200: raise Exception()
        if get:
            return response.content
        else:
            return response.headers

    def run_index_content(self):
        print("Checking index content...")
        to_update = []
        for k in ["characters", "summons", "skins", "enemies", "npcs"]:
            for id in self.data[k]:
                if self.data[k][id] == 0:
                    to_update.append(id)
        if len(to_update) > 0:
            print(len(to_update), "element(s) to be updated. Starting...")
            self.manualUpdate(to_update)
        else:
            print("No elements need to be updated")

    def styleProcessing(self):
        count = 0
        while self.running:
            try:
                id, styles = self.queue.get(block=True, timeout=0.1)
            except:
                continue
            for s in styles:
                if self.charaUpdate(id, s):
                    count += 1
        return count

    def run_sub(self, start, step, err, file, index):
        id = start
        while err[1] and err[0] < 80 and self.running:
            f = file.format(str(id).zfill(3))
            if f not in self.data[index] or isinstance(self.data[index], int):
                r = True
                if f.startswith('20'):
                    r = self.sumUpdate(f)
                elif f.startswith('10'):
                    r = self.weapUpdate(f)
                elif len(f) == 7:
                    r = self.mobUpdate(f)
                else:
                    r = self.charaUpdate(f)
                if not r:
                    with err[2]:
                        err[0] += 1
                        if err[0] >= 80:
                            err[1] = False
                            return
                else:
                    with err[2]:
                        err[0] = 0
                        err[3] += 1
            id += step

    def charaUpdate(self, id, style=""):
        data = [[], [], [], [], [], [], [], None] # sprite, phit, sp, aoe, single, general, sd, scene
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
        if len(uncaps) == 0:
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
            self.queue.put((id, ["_st2"])) # style check
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
        data[7] = self.update_scene_file(id+style, uncaps)
        with self.lock:
            self.modified = True
            if tid.startswith('37'):
                self.data['skins'][id+style] = data
            else:
                self.data['characters'][id+style] = data
        return True

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
        if len(uncaps) == 0:
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
        return True

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
        return True

    def mobUpdate(self, id):
        data = [[], [], [], [], [], None] # general, sprite, appear, ehit, esp, scene
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
        with self.lock:
            self.modified = True
            self.data['enemies'][id] = data
        return True

    def update_scene_file(self, id, uncaps = None):
        try:
            expressions = ["", "_laugh", "_laugh2", "_laugh3", "_wink", "_shout", "_shout2", "_sad", "_sad2", "_angry", "_angry2", "_school", "_shadow", "_close", "_serious", "_serious2", "_surprise", "_surprise2", "_think", "_think2", "_serious", "_serious2", "_ecstasy", "_ecstasy2", "_ef", "_body", "_speed2", "_suddenly", "_shy", "_shy2", "_weak"]
            variationsA = ["", "_battle"]
            variationsB = ["", "_speed", "_up"]
            others = ["_up_speed"]
            specials = ["_valentine", "_valentine_a", "_a_valentine", "_valentine2", "_valentine3", "_white", "_whiteday", "_whiteday2", "_whiteday3"]
            scene_alts = []
            if uncaps is None:
                uncaps = [""]
            for uncap in uncaps:
                if uncap == "01": uncap = ""
                elif uncap != "": uncap = "_" + uncap
                for A in variationsA:
                    for ex in expressions:
                        for B in variationsB:
                            scene_alts.append(uncap+A+ex+B)
            scene_alts += others + specials
            result = []
            for s in scene_alts:
                try:
                    self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/quest/scene/character/body/{}{}.png".format(id, s))
                    result.append(s)
                except:
                    pass
            return result
        except:
            return None

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

    def artCheck(self, id, style, uncaps):
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

    def manualUpdate(self, ids):
        if len(ids) == 0:
            return
        max_thread = 80
        self.running = True
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_thread+2) as executor:
            futures = [executor.submit(self.styleProcessing), executor.submit(self.styleProcessing)]
            for id in ids:
                if len(id) >= 10:
                    if id.startswith('2'):
                        futures.append(executor.submit(self.sumUpdate, id))
                    elif id.startswith('10'):
                        futures.append(executor.submit(self.weapUpdate, id))
                    elif id.startswith('39'):
                        futures.append(executor.submit(self.update_all_scene_sub, "npcs", id, None))
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
            tcounter = len(futures) - 2
            if tcounter > 0:
                print("Attempting to update", tcounter, "element(s)")
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    tfinished += 1
                    if tfinished >= tcounter:
                        self.running = False
            else:
                self.running = False
                for future in concurrent.futures.as_completed(futures):
                    future.result()
        self.save()
        self.running = False
        print("Done")

    def update_all_scene(self, full=False):
        self.running = True
        print("Updating scene data...")
        to_update = {}
        to_update["npcs"] = []
        for id in self.data["npcs"]:
            if full or (isinstance(self.data["npcs"][id], int) or self.data["npcs"][id][0] is None or len(self.data["npcs"][id][0])):
                to_update["npcs"].append((id, None))
        for k in ["characters", "skins"]:
            to_update[k] = []
            for id in self.data[k]:
                if not isinstance(self.data[k][id], int) and (full or (len(self.data[k][id]) < 8 or self.data[k][id][7] is None or len(self.data[k][id][7]) == 0)):
                    uncaps = []
                    for u in self.data[k][id][5]:
                        uncaps.append(u.replace(id+"_", ""))
                    to_update[k].append((id, uncaps))
        with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
            futures = []
            for k in to_update:
                for e in to_update[k]:
                    futures.append(executor.submit(self.update_all_scene_sub, k, e[0], e[1]))
            count = 0
            countmax = len(futures)
            print(countmax, "element(s) to update...")
            if countmax > 0:
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    count += 1
                    if count % 50 == 0:
                        print("Progress: {:.1f}%".format(100*count/countmax))
        self.save()
        self.running = False
        print("Done")

    def update_all_scene_sub(self, index, id, uncaps):
        r = self.update_scene_file(id, uncaps)
        if r is not None:
            with self.lock:
                self.modified = True
                if index == "npcs" and self.data[index][id] == 0:
                    self.data[index][id] = [r]
                else:
                    self.data[index][id][-1] = r

    def get_relation(self, eid):
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
                        if eid not in self.name_table[name] and not eid.startswith('399'):
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

    def build_relation(self, to_update=[]):
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
        print("Checking new relationships...")
        futures = []
        new = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            if len(to_update) == 0:
                for eid in self.data['characters']:
                    if eid not in relation:
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
            for future in concurrent.futures.as_completed(futures):
                r = future.result()
                try:
                    if r[0] is None or (r[0] not in self.data['characters'] and r[0] not in self.data['summons'] and r[0] not in self.data['weapons'] and r[0] not in self.data['skins']): raise Exception()
                    relation[r[0]] = r[1]
                    new.append(r[0])
                except:
                    pass
            for n in new:
                for eid in relation[n]:
                    if eid not in relation:
                        relation[eid] = []
                    if n not in relation[eid]:
                        relation[eid].append(n)
                        relation[eid].sort()
                relation[n].sort()
            if len(new) > 0:
                print("Checking with the name table...")
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
            if self.name_table_modified:
                try:
                    with open("json/relation_name.json", "w") as f:
                        json.dump(self.name_table, f, sort_keys=True, indent='\t', separators=(',', ':'))
                    print("Name table updated")
                except:
                    pass

    def connect_relation(self, As, B):
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

    def relation_edit(self):
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
def print_help():
    print("Usage: python parser.py [option]")
    print("options:")
    print("-run       : Update the index with new content.")
    print("-update    : Manual JSON updates (Followed by IDs to check).")
    print("-index     : Check the index for missing content.")
    print("-job       : Search Job spritesheets (Very time consuming). You can add specific ID, Mainhand ID or Job ID to reduce the search time.")
    print("-jobca     : Search Job Attack spritesheets (Very time consuming).")
    print("-relation  : Update the relationship index.")
    print("-relinput  : Update to relationships.")
    print("-listjob   : List indexed spritesheet Job IDs. You can add specific Mainhand ID to filter the list.")
    print("-scene     : Update scene index for characters/npcs with missing data (Time consuming).")
    print("-scenefull : Update scene index for every characters/npcs (Very time consuming).")
    time.sleep(2)

if __name__ == '__main__':
    p = Parser()
    if len(sys.argv) < 2:
        print_help()
    else:
        if sys.argv[1] == '-run':
            p.run()
        elif sys.argv[1] == '-update':
            if len(sys.argv) == 2:
                print_help()
            else:
                p.manualUpdate(sys.argv[2:])
        elif sys.argv[1] == '-index':
            p.run_index_content()
        elif sys.argv[1] == '-job':
            if len(sys.argv) == 2:
                p.dig_job_spritesheet()
            else:
                p.dig_job_spritesheet(sys.argv[2:])
        elif sys.argv[1] == '-jobca':
            p.dig_job_chargeattack()
        elif sys.argv[1] == '-relation':
            p.build_relation()
        elif sys.argv[1] == '-relinput':
            p.relation_edit()
        elif sys.argv[1] == '-listjob':
            if len(sys.argv) == 2:
                p.listjob()
            else:
                p.listjob(sys.argv[2:])
        elif sys.argv[1] == '-scene':
            p.update_all_scene()
        elif sys.argv[1] == '-scenefull':
            p.update_all_scene(True)
        else:
            print_help()