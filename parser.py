import httpx
import json
import concurrent.futures
from threading import Lock
import os
import os.path
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
        self.index = set()
        self.queue = queue.Queue()
        self.quality = ("/img/", "/js/")
        self.force_update = False
        self.data = {
            "version":0,
            "characters":set(),
            "summons":set(),
            "weapons":set(),
            "enemies":set(),
            "skins":set(),
            "job":set(),
            "npcs":set(),
            "background":set()
        }
        self.null_characters = ["3030182000", "3710092000", "3710139000", "3710078000", "3710105000", "3710083000", "3020072000", "3710184000"]
        self.multi_summon = ["2040414000"]
        self.new_elements = []
        self.name_table = {}
        self.name_table_modified = False
        self.name_lock = Lock()
        self.re = re.compile("[123][07][1234]0\\d{4}00")
        
        limits = httpx.Limits(max_keepalive_connections=100, max_connections=100, keepalive_expiry=10)
        self.client = httpx.Client(http2=False, limits=limits)
        self.manifestUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/model/manifest/"
        self.cjsUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/cjs/"
        self.imgUri = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img"
        self.endpoint = "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/"
        
        self.load()
        self.exclusion = set([])
        self.loadIndex()

    def load(self): # load data.json
        try:
            with open('data.json', mode='r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict): return
            for k in data:
                if isinstance(data[k], list): self.data[k] = set(data[k])
                else: self.data[k] = data[k]
        except Exception as e:
            print(e)

    def save(self): # save data.json
        try:
            data = {}
            for k in self.data:
                if isinstance(self.data[k], set):
                    data[k] = list(self.data[k])
                else:
                    data[k] = self.data[k]
            with open('data.json', mode='w', encoding='utf-8') as outfile:
                json.dump(data, outfile)
            print("data.json updated")
            with open('changelog.json', mode='w', encoding='utf-8') as outfile:
                json.dump({'timestamp':int(datetime.now(timezone.utc).timestamp()*1000)}, outfile)
            print("changelog.json updated")
        except Exception as e:
            print(e)

    def newShared(self, errs):
        errs.append([])
        errs[-1].append(0)
        errs[-1].append(True)
        errs[-1].append(Lock())

    def run_index_update(self, no_manual=False):
        errs = []
        possibles = []
        self.new_elements = []
        
        #rarity
        for r in range(1, 5):
            # characters
            if r > 1:
                self.newShared(errs)
                for i in range(4):
                    possibles.append(('characters', i, 4, errs[-1], "30"+str(r)+"0{}000", 3, "img_low/sp/assets/npc/m/", "_01{}.jpg", ["", "_st2"]))
            # summons
            self.newShared(errs)
            for i in range(4):
                possibles.append(('summons', i, 4, errs[-1], "20"+str(r)+"0{}000", 3, "img_low/sp/assets/summon/m/", ".jpg"))
            # weapons
            for j in range(10):
                self.newShared(errs)
                for i in range(5):
                    possibles.append(('weapons', i, 5, errs[-1], "10"+str(r)+"0{}".format(j) + "{}00", 3, "img_low/sp/assets/weapon/m/", ".jpg"))
        # skins
        self.newShared(errs)
        for i in range(4):
            possibles.append(('skins', i, 4, errs[-1], "3710{}000", 3, "img_low/sp/assets/npc/m/", "_01.jpg"))
        # enemies
        for a in range(1, 10):
            for b in range(1, 4):
                for d in [1, 2, 3]:
                    self.newShared(errs)
                    for i in range(2):
                        possibles.append(('enemies', i, 2, errs[-1], str(a) + str(b) + "{}" + str(d), 4, "img/sp/assets/enemy/s/", ".png", [""], 40))
        # npc
        self.newShared(errs)
        for i in range(8):
            possibles.append(('npcs', i, 8, errs[-1], "399{}000", 4, "img_low/sp/quest/scene/character/body/", "{}.png", [""], 80))
        
        # backgrounds
        self.newShared(errs)
        for i in range(2):
            possibles.append(('background', i, 2, errs[-1], "event_{}", 1, "img_low/sp/raid/bg/", "{}.jpg", [""], 10))
        self.newShared(errs)
        for i in range(2):
            possibles.append(('background', i, 2, errs[-1], "common_{}", 3, "img_low/sp/raid/bg/", "{}.jpg", [""], 10))
        self.newShared(errs)
        for i in range(2):
            possibles.append(('background', i, 2, errs[-1], "main_{}", 1, "img_low/sp/guild/custom/bg/", "{}.png", [""], 10))
        for i in ["ra", "rb", "rc"]:
            self.newShared(errs)
            possibles.append(('background', 0, 1, errs[-1], "{}"+i, 1, "img_low/sp/raid/bg/", "{}_1.jpg", [""], 50))
        for i in [("e", ""), ("e", "r"), ("f", ""), ("f", "r"), ("f", "ra"), ("f", "rb"), ("f", "rc")]:
            self.newShared(errs)
            possibles.append(('background', 0, 1, errs[-1], i[0]+"{}"+i[1], 3, "img_low/sp/raid/bg/", "{}_1.jpg", [""], 50))
        
        print("Starting Index update... (", len(possibles), " threads )")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(possibles)) as executor:
            futures = self.job_search(executor)
            for p in possibles:
                futures.append(executor.submit(self.subroutine, self.getEndpoint(), *p))
            for future in concurrent.futures.as_completed(futures):
                future.result()
        print("Done")
        if not no_manual:
            self.manualUpdate(self.new_elements)
        self.save()
        self.build_relation()

    def listjob(self, mhs=['sw', 'wa', 'kn', 'me', 'bw', 'mc', 'sp', 'ax', 'gu', 'kt']):
        job_index = {}
        mhs = set(mhs)
        try:
            with open('data/job.json', mode='r', encoding='utf-8') as f:
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
            with open('data/job.json', mode='r', encoding='utf-8') as f:
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
            with open('data/job.json', mode='w', encoding='utf-8') as f:
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
                        self.data[index].add(f + s)
                        if file.startswith("30") or file.startswith("37") or file.startswith("20"):
                            self.new_elements.append(f + s)
                except:
                    if s != "": break
                    with err[2]:
                        err[0] += 1
                        if err[0] >= maxerr:
                            if err[1]: print("Threads", index, "("+file+")", "are done")
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
                        self.data['job'].add(id + "_" + mhid)
                    break
                except:
                    pass
        with shared[0]:
            if not shared[2]:
                shared[2] = True
                print("Threads job are done")

    def dig_job_chargeattack(self):
        try:
            with open('job_ca.json', mode='r', encoding='utf-8') as f:
                index = set(json.load(f))
        except:
            index = set()
        shared = [Lock(), queue.Queue(), index]
        for i in range(10):
            count = 0
            j = 0
            while count < 10 and j < 1000:
                f = "1040{}{}00".format(i, str(j).zfill(3))
                if f in self.data["weapons"] or f in index:
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
            with open('job_ca.json', mode='w', encoding='utf-8') as f:
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

    def loadIndex(self):
        files = [f for f in os.listdir('data/') if os.path.isfile(os.path.join('data/', f))]
        known = []
        for f in files:
            if f.startswith("371") or f.startswith("304") or f.startswith("303") or f.startswith("302"):
                known.append(f.split('.')[0])
        self.index = set(known)

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

    def run(self):
        max_thread = 16
        print("Updating Database...")
        if self.force_update:
            print("Note: All characters will be updated")
            s = input("Type quit to exit now:").lower()
            if s == "quit":
                print("Process aborted")
                return
        
        possibles = [
            ("3020{}000", "R Characters"),
            ("3030{}000", "SR Characters"),
            ("3040{}000", "SSR Characters"),
            ("3710{}000", "Skins")
        ]

        self.running = True
        tmul = len(possibles)+1
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_thread*tmul) as executor:
            futures = []
            err = []
            for i in range(max_thread):
                futures.append(executor.submit(self.styleProcessing))
            for p in possibles:
                err.append([0, True, Lock(), 0, p[1]])
                for i in range(max_thread):
                    futures.append(executor.submit(self.run_sub, i, max_thread, err[-1], p[0]))
            finished = 0
            for future in concurrent.futures.as_completed(futures):
                future.result()
                finished += 1
                if finished == max_thread*len(possibles):
                    self.running = False
                    print("Progress 100%")
                elif finished > max_thread*len(possibles):
                    pass
                elif finished > 0 and finished % (max_thread//2) == 0:
                    print("Progress {:.1f}%".format((100*finished)/(max_thread*len(possibles))))
        self.running = False
        print("Done")
        for e in err:
            if e[3] > 0:
                print(e[3], e[4])

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

    def run_sub(self, start, step, err, file):
        id = start
        while err[1] and err[0] < 80 and self.running:
            f = file.format(str(id).zfill(3))
            if self.force_update or f not in self.index:
                if not self.charaUpdate(f):
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
        urls = {}
        urls["Main Arts"] = []
        urls["Journal Arts"] = []
        urls["Inventory Portraits"] = []
        urls["Square Portraits"] = []
        urls["Party Portraits"] = []
        urls["Popup Portraits"] = []
        urls["Party Select Portraits"] = []
        urls["Sprites"] = []
        urls["Raid"] = []
        urls["Twitter Arts"] = []
        urls["Charge Attack Cutins"] = []
        urls["Chain Cutins"] = []
        urls['Character Sheets'] = []
        urls['Attack Effect Sheets'] = []
        urls['Charge Attack Sheets'] = []
        urls['AOE Skill Sheets'] = []
        urls['Single Target Skill Sheets'] = []
        uncaps = []
        altForm = False
        # main sheet
        for uncap in ["01", "02", "03", "04"]:
            for ftype in ["", "_s2"]:
                for form in ["", "_f", "_f1", "_f_01"]:
                    try:
                        fn = "npc_{}_{}{}{}{}".format(id, uncap, style, form, ftype)
                        urls['Character Sheets'] += self.processManifest(fn)
                        if form == "": uncaps.append(uncap)
                        else: altForm = True
                    except:
                        if form == "":
                            break
        if len(uncaps) == 0:
            return False
        if not id.startswith("371") and style == "":
            self.queue.put((id, ["_st2"])) # style check
        # attack
        targets = [""]
        for i in range(2, len(uncaps)):
            targets.append("_" + uncaps[i])
        for t in targets:
            try:
                fn = "phit_{}{}{}".format(id, t, style)
                urls['Attack Effect Sheets'] += self.processManifest(fn)
            except:
                break
        # ougi
        for uncap in uncaps:
            for form in (["", "_f", "_f1", "_f_01"] if altForm else [""]):
                for catype in ["", "_s2", "_s3"]:
                    try:
                        fn = "nsp_{}_{}{}{}{}".format(id, uncap, style, form, catype)
                        urls['Charge Attack Sheets'] += self.processManifest(fn)
                        break
                    except:
                        pass
        # skills
        for el in ["01", "02", "03", "04", "05", "06", "07", "08"]:
            try:
                fn = "ab_all_{}{}_{}".format(id, style, el)
                urls['AOE Skill Sheets'] += self.processManifest(fn)
            except:
                pass
            try:
                fn = "ab_{}{}_{}".format(id, style, el)
                urls['Single Target Skill Sheets'] += self.processManifest(fn)
            except:
                pass
        # arts
        flags = self.artCheck(id, style, uncaps)
        # # # Assets
        for uncap in flags:
            # main
            base_fn = "{}_{}{}".format(id, uncap, style)
            uf = flags[uncap]
            for g in (["", "_0", "_1"] if (uf[0] is True) else [""]):
                for m in (["", "_101", "_102", "_103", "_104", "_105"] if (uf[1] is True) else [""]):
                    for n in (["", "_01", "_02", "_03", "_04", "_05", "_06"] if (uf[2] is True) else [""]):
                        for af in (["", "_f", "_f1"] if altForm else [""]):
                            fn = base_fn + af + g + m + n
                            urls["Main Arts"].append("img_low/sp/assets/npc/zoom/" + fn + ".png")
                            urls["Main Arts"].append("https://media.skycompass.io/assets/customizes/characters/1138x1138/" + fn + ".png")
                            urls["Journal Arts"].append("img_low/sp/assets/npc/b/" + fn + ".png")
                            urls["Inventory Portraits"].append("img_low/sp/assets/npc/m/" + fn + ".jpg")
                            urls["Square Portraits"].append("img_low/sp/assets/npc/s/" + fn + ".jpg")
                            urls["Party Portraits"].append("img_low/sp/assets/npc/f/" + fn + ".jpg")
                            urls["Popup Portraits"].append("img/sp/assets/npc/qm/" + fn + ".png")
                            urls["Party Select Portraits"].append("img/sp/assets/npc/quest/" + fn + ".jpg")
                            urls["Raid"].append("img/sp/assets/npc/raid_normal/" + fn + ".jpg")
                            urls["Twitter Arts"].append("img_low/sp/assets/npc/sns/" + fn + ".jpg")
                            urls["Charge Attack Cutins"].append("img_low/sp/assets/npc/cutin_special/" + fn + ".jpg")
                            urls["Chain Cutins"].append("img_low/sp/assets/npc/raid_chain/" + fn + ".jpg")
            # sprites
            urls["Sprites"].append("img/sp/assets/npc/sd/" + base_fn + ".png")
        # sorting
        for k in urls:
            if "Sheet" not in k: continue
            el = [f.split("/")[-1] for f in urls[k]]
            el.sort()
            for i in range(len(urls[k])):
                urls[k][i] = "/".join(urls[k][i].split("/")[:-1]) + "/" + el[i]
        with open("data/" + id + style + ".json", 'w') as outfile:
            json.dump(urls, outfile)
        return True

    def sumUpdate(self, id):
        urls = {}
        urls["Main Arts"] = []
        urls["Home Arts"] = []
        urls["Inventory Portraits"] = []
        urls["Square Portraits"] = []
        urls["Main Summon Portraits"] = []
        urls["Sub Summon Portraits"] = []
        urls["Raid Portraits"] = []
        urls['Summon Call Sheets'] = []
        urls['Summon Damage Sheets'] = []
        uncaps = []
        # main sheet
        for uncap in ["", "_02", "_03", "_04"]:
            try:
                fn = "{}_{}".format(id, uncap)
                self.req("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/m/{}{}.jpg".format(id, uncap))
                urls['Main Arts'].append("img_low/sp/assets/summon/b/{}{}.png".format(id, uncap))
                if uncap == "": urls['Main Arts'].append("https://media.skycompass.io/assets/archives/summons/{}/detail_l.png".format(id))
                urls['Home Arts'].append("img_low/sp/assets/summon/my/{}{}.png".format(id, uncap))
                urls['Inventory Portraits'].append("img_low/sp/assets/summon/m/{}{}.jpg".format(id, uncap))
                urls['Square Portraits'].append("img_low/sp/assets/summon/s/{}{}.jpg".format(id, uncap))
                urls['Main Summon Portraits'].append("img_low/sp/assets/summon/party_main/{}{}.jpg".format(id, uncap))
                urls['Sub Summon Portraits'].append("img_low/sp/assets/summon/party_sub/{}{}.jpg".format(id, uncap))
                urls['Raid Portraits'].append("img/sp/assets/summon/raid_normal/{}{}.jpg".format(id, uncap))
                uncaps.append("01" if uncap == "" else uncap[1:])
            except:
                break
        if len(uncaps) == 0:
            return False
        if id in self.multi_summon:
            tmp = []
            for u in uncaps:
                for c in 'abcde':
                    tmp.append(u+"_"+c)
            uncaps = tmp
        # attack
        for u in uncaps:
            try:
                fn = "summon_{}_{}_attack".format(id, u)
                urls['Summon Call Sheets'] += self.processManifest(fn)
            except:
                pass
        # damage
        for u in uncaps:
            try:
                fn = "summon_{}_{}_damage".format(id, u)
                urls['Summon Damage Sheets'] += self.processManifest(fn)
            except:
                pass
        # sorting
        for k in urls:
            if "Sheet" not in k: continue
            el = [f.split("/")[-1] for f in urls[k]]
            el.sort()
            for i in range(len(urls[k])):
                urls[k][i] = "/".join(urls[k][i].split("/")[:-1]) + "/" + el[i]
        with open("data/" + id + ".json", 'w') as outfile:
            json.dump(urls, outfile)
        return True

    def processManifest(self, file):
        manifest = self.req(self.manifestUri + file + ".js", get=True).decode('utf-8')
        st = manifest.find('manifest:') + len('manifest:')
        ed = manifest.find(']', st) + 1
        data = json.loads(manifest[st:ed].replace('Game.imgUri+', '').replace('src:', '"src":').replace('type:', '"type":').replace('id:', '"id":'))
        res = []
        for l in data:
            src = "img_low" + l['src'].split('?')[0]
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
        max_thread = 40
        counter = 0
        tcounter = 0
        self.running = True
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_thread+2) as executor:
            futures = [executor.submit(self.styleProcessing), executor.submit(self.styleProcessing)]
            for id in ids:
                if len(id) >= 10:
                    if id.startswith('2'):
                        futures.append(executor.submit(self.sumUpdate, id))
                    else:
                        futures.append(executor.submit(self.charaUpdate, id))
                    tcounter += 1
            tfinished = 0
            if tcounter > 0:
                print("Attempting to update", tcounter, "element(s)")
                for future in concurrent.futures.as_completed(futures):
                    tfinished += 1
                    if tfinished >= tcounter:
                        self.running = False
                    r = future.result()
                    if isinstance(r, int): counter += r
                    elif r: counter += 1
            else:
                self.running = False
                for future in concurrent.futures.as_completed(futures):
                    r = future.result()
        self.running = False
        print("Done")
        if counter > 0:
            print(counter, "successfully processed ID")
        return (counter > 0)

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
                        if eid not in self.name_table[name]:
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
            with open("relation_name.json", "r") as f:
                self.name_table = json.load(f)
            print("Element name table loaded")
        except:
            self.name_table = {}
        self.name_table_modified = False
        try:
            with open("relation.json", "r") as f:
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
                    with open("relation.json", "w") as f:
                        json.dump(relation, f, sort_keys=True, indent='\t', separators=(',', ':'))
                    print("Relationships updated")
                except:
                    pass
            if self.name_table_modified:
                try:
                    with open("relation_name.json", "w") as f:
                        json.dump(self.name_table, f, sort_keys=True, indent='\t', separators=(',', ':'))
                    print("Name table updated")
                except:
                    pass

    def connect_relation(self, As, B):
        try:
            with open("relation_name.json", "r") as f:
                self.name_table = json.load(f)
            print("Element name table loaded")
        except:
            self.name_table = {}
        self.name_table_modified = False
        try:
            with open("relation.json", "r") as f:
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
                with open("relation.json", "w") as f:
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
    print("-run     : Update character JSON files and update the index.")
    print("-update  : Manual JSON updates (Followed by IDs to check).")
    print("-index   : Update the index and create new character JSON files if any.")
    print("-job     : Search Job spritesheets (Very time consuming). You can add specific ID, Mainhand ID or Job ID to reduce the search time.")
    print("-jobca   : Search Job Attack spritesheets (Very time consuming).")
    print("-relation: Update the relationship index.")
    print("-relinput: Update to relationships.")
    print("-listjob : List indexed spritesheet Job IDs. You can add specific Mainhand ID to filter the list.")
    print("-debug   : List downloaded skins with multi portraits.")
    time.sleep(2)

def debug_multi_portrait_skin():
    files = [f for f in os.listdir('data/') if os.path.isfile(os.path.join('data/', f))]
    known = []
    for f in files:
        if f.startswith("371"):
            known.append(f)
    for k in known:
        with open("data/" + k) as f:
            data = json.load(f)
        counted = set()
        for x in data['Inventory Portraits']:
            if '_f' not in x and '_f1' not in x and x not in counted:
                counted.add(x)
        if len(counted) > 1: print(k)

if __name__ == '__main__':
    p = Parser()
    if len(sys.argv) < 2:
        print_help()
    else:
        if sys.argv[1] == '-run':
            p.run()
            p.run_index_update(no_manual=True)
        elif sys.argv[1] == '-update':
            if len(sys.argv) == 2:
                print_help()
            else:
                if p.manualUpdate(sys.argv[2:]):
                    p.save()
        elif sys.argv[1] == '-index':
            p.run_index_update()
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
        elif sys.argv[1] == '-debug':
            debug_multi_portrait_skin()
        else:
            print_help()