from urllib import request
import json
import concurrent.futures
from threading import Lock
import json
import os.path
import re
import zlib
import sys

class Generator():
    def __init__(self):
        self.data = {
            "version":0,
            "characters":set(),
            "summons":set(),
            "weapons":set(),
            "enemies":set(),
            "skins":set()
        }
        self.null_characters = ["3030182000", "3710092000", "3710139000", "3710078000", "3710105000", "3710083000", "3020072000", "3710184000"]
        self.endpoints = [
            "prd-game-a-granbluefantasy.akamaized.net/",
            "prd-game-a1-granbluefantasy.akamaized.net/",
            "prd-game-a2-granbluefantasy.akamaized.net/",
            "prd-game-a3-granbluefantasy.akamaized.net/",
            "prd-game-a4-granbluefantasy.akamaized.net/",
            "prd-game-a5-granbluefantasy.akamaized.net/"
        ]

    def load(self): # load data.json
        try:
            with open('data.json') as f:
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
            with open('data.json', 'w') as outfile:
                json.dump(data, outfile)
            print("data.json updated")
        except Exception as e:
            print(e)

    def newShared(self, errs):
        errs.append([])
        errs[-1].append(0)
        errs[-1].append(True)
        errs[-1].append(Lock())

    def run(self):
        self.load()
        count = 0
        errs = []
        possibles = []
        
        # characters
        self.newShared(errs)
        for i in range(4):
            possibles.append(('characters', i, 4, errs[-1], "3040{}000", 3, "assets_en/img_low/sp/assets/npc/m/", "_01{}.jpg", ["", "_st2"]))
        # summons
        self.newShared(errs)
        for i in range(4):
            possibles.append(('summons', i, 4, errs[-1], "2040{}000", 3, "assets_en/img_low/sp/assets/summon/m/", ".jpg"))
        # weapons
        for j in range(10):
            self.newShared(errs)
            for i in range(5):
                possibles.append(('weapons', i, 5, errs[-1], "1040{}".format(j) + "{}00", 3, "assets_en/img_low/sp/assets/weapon/m/", ".jpg"))
        # skins
        self.newShared(errs)
        for i in range(4):
            possibles.append(('skins', i, 4, errs[-1], "3710{}000", 3, "assets_en/img_low/sp/assets/npc/m/", "_01.jpg"))
        #enemies
        for ab in [62, 72]:
            for d in [1, 2, 3]:
                self.newShared(errs)
                for i in range(5):
                    possibles.append(('enemies', i, 5, errs[-1], str(ab) + "{}" + str(d), 4, "assets_en/img/sp/assets/enemy/s/", ".png"))
        
        print("Starting...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(possibles)) as executor:
            futures = []
            for p in possibles:
                futures.append(executor.submit(self.subroutine, self.endpoints[count], *p))
                count = (count + 1) % len(self.endpoints)
            for future in concurrent.futures.as_completed(futures):
                future.result()
        print("Done")
        self.save()
        self.update()

    def update(self):
        with open("base.js", mode="r", encoding="utf-8") as f:
            base = f.read()
        with open("docs/js/list.js", mode="w", encoding="utf-8") as f:
            for k in self.data:
                if k == "version": continue
                s = list(self.data[k])
                s.sort()
                f.write(k + "=" + str(s) + ";\n")
            f.write(base)
            print("list.js updated")

    def req(self, url, headers={}):
        return request.urlopen(request.Request(url, headers=headers), timeout=50)

    def subroutine(self, endpoint, index, start, step, err, file, zfill, path, ext, styles = [""]):
        id = start
        while err[0] < 20 and err[1]:
            f = file.format(str(id).zfill(zfill))
            if f in self.data[index]:
                with err[2]:
                    err[0] = 0
                id += step
                continue
            for s in styles:
                try:
                    url_handle = self.req("http://" + endpoint + path + f + ext.replace("{}", s))
                    url_handle.read()
                    url_handle.close()
                    with err[2]:
                        err[0] = 0
                        self.data[index].add(f + s)
                except Exception as e:
                    try: url_handle.close()
                    except: pass
                    if s != "": break
                    with err[2]:
                        err[0] += 1
                        if err[0] >= 20:
                            if err[1]: print("Threads", index+":"+file, "are done")
                            err[1] = False
                            return
                    break
            id += step

    def manualUpdate(self):
        for id in self.new:
            if len(id) == 10 or len(id) == 14:
                match id[0]:
                    case '1':
                        self.data['weapons'].add(id)
                    case '2':
                        self.data['summons'].add(id)
                    case '3':
                        if id[1] == '7': self.data['skins'].add(id)
                        else: self.data['characters'].add(id)
            elif len(id) == 7:
                self.data['enemies'].add(id)

if __name__ == '__main__':
    g = Generator()
    if len(sys.argv) > 2 and sys.argv[1] == '-update':
        g.new = sys.argv[2:]
        g.manualUpdate()
        g.save()
        g.update()
    else:
        g.run()