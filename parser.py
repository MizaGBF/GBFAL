from urllib import request
import json
import concurrent.futures
from threading import Lock
import json
import os
import os.path
import zlib
import sys
import queue

class Parser():
    def __init__(self):
        self.running = False
        self.index = set()
        self.queue = queue.Queue()
        self.quality = ("/img/", "/js/")
        self.force_update = False
        
        self.manifestUri = "http://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/model/manifest/"
        self.cjsUri = "http://prd-game-a-granbluefantasy.akamaized.net/assets_en/js/cjs/"
        self.imgUri = "http://prd-game-a-granbluefantasy.akamaized.net/assets_en/img"
        self.endpoints = [
            "http://prd-game-a-granbluefantasy.akamaized.net/assets_en/",
            "http://prd-game-a1-granbluefantasy.akamaized.net/assets_en/",
            "http://prd-game-a2-granbluefantasy.akamaized.net/assets_en/",
            "http://prd-game-a3-granbluefantasy.akamaized.net/assets_en/",
            "http://prd-game-a4-granbluefantasy.akamaized.net/assets_en/",
            "http://prd-game-a5-granbluefantasy.akamaized.net/assets_en/"
        ]
        self.endpoint_counter = 0
        self.exclusion = set([])
        self.loadIndex()

    def loadIndex(self):
        files = [f for f in os.listdir('docs/data/') if os.path.isfile(os.path.join('docs/data/', f))]
        known = []
        for f in files:
            if f.startswith("371") or f.startswith("304") or f.startswith("303") or f.startswith("302"):
                known.append(f.split('.')[0])
        self.index = set(known)

    def getEndpoint(self):
        e = self.endpoints[self.endpoint_counter]
        self.endpoint_counter = (self.endpoint_counter + 1) % len(self.endpoints)
        return e

    def req(self, url, headers={}):
        return request.urlopen(request.Request(url.replace('/img/', self.quality[0]).replace('/js/', self.quality[1]), headers=headers), timeout=50)

    def run(self):
        max_thread = 10
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
                elif finished > 0 and finished % 10 == 0:
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
                if self.update(id, s):
                    count += 1
        return count

    def run_sub(self, start, step, err, file):
        id = start
        while err[1] and err[0] < 20 and self.running:
            f = file.format(str(id).zfill(3))
            if self.force_update or f not in self.index:
                if not self.update(f):
                    with err[2]:
                        err[0] += 1
                        if err[0] >= 20:
                            err[1] = False
                            return
                else:
                    with err[2]:
                        err[0] = 0
                        err[3] += 1
            id += step

    def update(self, id, style=""):
        urls = {}
        urls["Main Arts"] = []
        urls["Inventory Portraits"] = []
        urls["Square Portraits"] = []
        urls["Party Portraits"] = []
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
            for form in ["", "_f", "_f1", "_f_01"]:
                try:
                    fn = "npc_{}_{}{}{}".format(id, uncap, style, form)
                    urls['Character Sheets'] += self.processManifest(fn)
                    if form == "": uncaps.append(uncap)
                    else: altForm = True
                except:
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
        gendered = self.artCheck(id, style, "_1")
        multi = self.artCheck(id, style, "_101")
        null = self.artCheck(id, style, "_01")
        bonus = []
        for b in ["_81", "_82", "_83"]:
            if self.artCheck(id, style, b):
                bonus.append(b[1:])
        # # # Assets
        for uncap in uncaps + bonus:
            # main
            base_fn = "{}_{}{}".format(id, uncap, style)
            for g in (["", "_1"] if gendered else [""]):
                for m in (["", "_101", "_102", "_103"] if multi else [""]):
                    for n in (["", "_01", "_02", "_03", "_04", "_05", "_06"] if null else [""]):
                        fn = base_fn + g + m + n
                        urls["Main Arts"].append(self.getEndpoint() + "img_low/sp/assets/npc/zoom/" + fn + ".png")
                        urls["Main Arts"].append("https://media.skycompass.io/assets/customizes/characters/1138x1138/" + fn + ".png")
                        urls["Inventory Portraits"].append(self.getEndpoint() + "img_low/sp/assets/npc/m/" + fn + ".jpg")
                        urls["Square Portraits"].append(self.getEndpoint() + "img_low/sp/assets/npc/s/" + fn + ".jpg")
                        urls["Party Portraits"].append(self.getEndpoint() + "img_low/sp/assets/npc/f/" + fn + ".jpg")
                        urls["Raid"].append(self.getEndpoint() + "img/sp/assets/npc/raid_normal/" + fn + ".jpg")
                        urls["Twitter Arts"].append(self.getEndpoint() + "img_low/sp/assets/npc/sns/" + fn + ".jpg")
                        urls["Charge Attack Cutins"].append(self.getEndpoint() + "img_low/sp/assets/npc/cutin_special/" + fn + ".jpg")
                        urls["Chain Cutins"].append(self.getEndpoint() + "img_low/sp/assets/npc/raid_chain/" + fn + ".jpg")
            # sprites
            urls["Sprites"].append(self.getEndpoint() + "img/sp/assets/npc/sd/" + base_fn + ".png")
        # sorting
        for k in urls:
            if "Sheet" not in k: continue
            el = [f.split("/")[-1] for f in urls[k]]
            el.sort()
            for i in range(len(urls[k])):
                urls[k][i] = "/".join(urls[k][i].split("/")[:-1]) + "/" + el[i]
        with open("docs/data/" + id + style + ".json", 'w') as outfile:
            json.dump(urls, outfile)
        return True

    def processManifest(self, file):
        url_handle = self.req(self.manifestUri + file + ".js")
        manifest = url_handle.read().decode('utf-8')
        url_handle.close()
        st = manifest.find('manifest:') + len('manifest:')
        ed = manifest.find(']', st) + 1
        data = json.loads(manifest[st:ed].replace('Game.imgUri+', '').replace('src', '"src"').replace('type', '"type"').replace('id', '"id"'))
        res = []
        for l in data:
            src = self.getEndpoint() + "img_low" + l['src'].split('?')[0]
            res.append(src)
        return res

    def artCheck(self, id, style, append):
        try:
            url_handle = self.req(self.imgUri + "_low/sp/assets/npc/m/" + id + "_01" + style + append + ".jpg")
            url_handle.read()
            url_handle.close()
            return True
        except:
            return False

    def manualUpdate(self, ids):
        max_thread = 40
        counter = 0
        tcounter = 0
        self.running = True
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_thread+2) as executor:
            futures = [executor.submit(self.styleProcessing), executor.submit(self.styleProcessing)]
            for id in ids:
                if len(id) == 10:
                    futures.append(executor.submit(self.update, id))
                    tcounter += 1
            print("Attempting to update", tcounter, "element(s)")
            tfinished = 0
            for future in concurrent.futures.as_completed(futures):
                tfinished += 1
                if tfinished >= tcounter:
                    self.running = False
                r = future.result()
                if isinstance(r, int): counter += r
                elif r: counter += 1
        self.running = False
        print("Done")
        if counter > 0:
            print(counter, "successfully processed ID")

if __name__ == '__main__':
    p = Parser()
    if len(sys.argv) >= 2 and sys.argv[1] == '-update':
        if len(sys.argv) == 2:
            print("Add IDs to update after '-update'")
            print("Example 'parser.py -update 3040000000 3040001000'")
        else:
            p.manualUpdate(sys.argv[2:])
    else:
        p.run()