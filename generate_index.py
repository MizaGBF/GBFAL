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
        self.new = self.null_characters
        self.new.append("3840396000")
        self.endpoints = [
            "prd-game-a-granbluefantasy.akamaized.net/",
            "prd-game-a1-granbluefantasy.akamaized.net/",
            "prd-game-a2-granbluefantasy.akamaized.net/",
            "prd-game-a3-granbluefantasy.akamaized.net/",
            "prd-game-a4-granbluefantasy.akamaized.net/",
            "prd-game-a5-granbluefantasy.akamaized.net/"
        ]
        self.version = str(self.getGameVersion())
        if self.version == "None":
            print("Can't retrieve the game version")
            exit(0)

    def getGameVersion(self):
        vregex = re.compile("Game\.version = \"(\d+)\";")
        handler = self.req('https://game.granbluefantasy.jp/', headers={'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36", 'Accept-Language':'en', 'Accept-Encoding':'gzip, deflate', 'Host':'game.granbluefantasy.jp', 'Connection':'keep-alive'})
        try:
            res = zlib.decompress(handler.read(), 16+zlib.MAX_WBITS)
            handler.close()
            return int(vregex.findall(str(res))[0])
        except:
            return None

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
            possibles.append(('characters', i, 4, errs[-1], "3040{}000", 3, "assets_en/img_low/sp/assets/npc/m/", "_01.jpg"))
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
        self.jsonGenerator()

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

    def subroutine(self, endpoint, index, start, step, err, file, zfill, path, ext):
        id = start
        while err[0] < 20 and err[1]:
            try:
                f = file.format(str(id).zfill(zfill))
                if f in self.data[index]:
                    with err[2]:
                        err[0] = 0
                    id += step
                    continue
                url_handle = self.req("http://" + endpoint + path + f + ext)
                url_handle.read()
                url_handle.close()
                with err[2]:
                    err[0] = 0
                    self.data[index].add(f)
                    self.new.append(f)
            except Exception as e:
                try: url_handle.close()
                except: pass
                with err[2]:
                    err[0] += 1
                    if err[0] >= 20:
                        if err[1]: print("Threads", index+":"+file, "are done")
                        err[1] = False
                        return
            id += step

    def jsonGenerator(self):
        print("Generating JSON for new IDs...")
        max_thread = 70
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_thread) as executor:
            futures = []
            for i in range(max_thread):
                futures.append(executor.submit(self.genSub, i, max_thread, self.endpoints[i%len(self.endpoints)]))
        for future in concurrent.futures.as_completed(futures):
            future.result()
        print("Done")

    def genSub(self, start, step, endpoint):
        i = start
        while i < len(self.new):
            id = self.new[i]
            if len(id) == 7:
                #self.processEnemy(id, endpoint)
                pass
            elif len(id) == 10:
                match id[0]:
                    case '1':
                        #self.processWeapon(id, endpoint)
                        pass
                    case '2':
                        #self.processSummon(id, endpoint)
                        pass
                    case '3':
                        self.processCharacter(id, endpoint)
            i += step

    def processEnemy(self, id, endpoint):
        if os.path.exists("docs/data/" + id + ".json"): return
        assets = [
            ["Big Icon", "sp/assets/enemy/m/", "png", "img/", [""], [""]],
            ["Small Icon", "sp/assets/enemy/s/", "png", "img/", [""], [""]],
            ["Sprite Sheets", "sp/cjs/enemy_", "png", "img_low/", [""], [""]],
            ["Raid Appear Sheets", "sp/cjs/raid_appear_", "png", "img_low/", ["", "_a", "_b", "_c", "_d", "_e"], [""]],
            ["Attack Effect Sheets", "sp/cjs/ehit_", "png", "img_low/", ["", "_a", "_b", "_c", "_d", "_e"], [""]],
            ["Charge Attack Sheets", "sp/cjs/esp_", "png", "img_low/", ["", "_a", "_b", "_c", "_d", "_e"], ["_01", "_02", "_03", "_04", "_05", "_06", "_07", "_08", "_09", "_10", "_11", "_12", "_13", "_14", "_15", "_16", "_17", "_18", "_19", "_20"]]
        ]
        jsoncontent = {}
        for a in assets:
            for sub1 in a[4]:
                for sub2 in a[5]:
                    try:
                        f = "http://" + endpoint + "assets_en/" + a[3] + a[1] + id + sub1 + sub2 + "." + a[2]
                        url_handle = self.req(f)
                        url_handle.read()
                        url_handle.close()
                        if a[0] not in jsoncontent:
                            jsoncontent[a[0]] = []
                        jsoncontent[a[0]].append(f)
                    except:
                        pass
        if len(jsoncontent.keys()) != 0:
            with open("docs/data/" + id + ".json", "w") as out:
                json.dump(jsoncontent, out)
            print("Saved", id + ".json")
        else:
            print("Warning:", id, "didn't return any positive result")

    def processWeapon(self, id, endpoint):
        if os.path.exists("docs/data/" + id + ".json"): return
        assets = [
            ["Main Arts", "sp/assets/weapon/b/", "png", "img_low/", [""], [""]],
            ["Inventory Portraits", "sp/assets/weapon/m/", "jpg", "img_low/", [""], [""]],
            ["Square Portraits", "sp/assets/weapon/s/", "jpg", "img_low/", [""], [""]],
            ["Main Hand Portraits", "sp/assets/weapon/ls/", "jpg", "img_low/", [""], [""]],
            ["Battle Sprites", "sp/cjs/", "png", "img/", ["", "_1", "_2"], [""]],
            ["Attack Effects", "sp/cjs/phit_", "png", "img/", ["", "_f1", "_1", "_1_f1", "_2", "_2_f1"], ["", "_a", "_b", "_c", "_d", "_e"]],
            ["Charge Attack Sheets", "sp/cjs/sp_", "png", "img_low/", ["", "_f1", "_1", "_1_f1", "_2", "_2_f1", "_s2", "_f1_s2", "_1_s2", "_1_f1_s2", "_2_s2", "_2_f1_s2"], ["", "_a", "_b", "_c", "_d", "_e"]]
        ]
        jsoncontent = {}
        for a in assets:
            for sub1 in a[4]:
                for sub2 in a[5]:
                    try:
                        f = "http://" + endpoint + "assets_en/" + a[3] + a[1] + id + sub1 + sub2 + "." + a[2]
                        url_handle = self.req(f)
                        url_handle.read()
                        url_handle.close()
                        if a[0] not in jsoncontent:
                            jsoncontent[a[0]] = []
                        jsoncontent[a[0]].append(f)
                    except:
                        pass
        if len(jsoncontent.keys()) != 0:
            with open("docs/data/" + id + ".json", "w") as out:
                json.dump(jsoncontent, out)
            print("Saved", id + ".json")
        else:
            print("Warning:", id, "didn't return any positive result")

    def processSummon(self, id, endpoint):
        if os.path.exists("docs/data/" + id + ".json"): return
        assets = [
            ["Main Arts", "sp/assets/summon/b/", "png", "img_low/", ["", "_01", "_02"], [""]],
            ["Inventory Portraits", "sp/assets/summon/m/", "jpg", "img_low/", ["", "_01", "_02"], [""]],
            ["Square Portraits", "sp/assets/summon/s/", "jpg", "img_low/", ["", "_01", "_02"], [""]],
            ["Main Summon Portraits", "sp/assets/summon/party_main/", "jpg", "img_low/", ["", "_01", "_02"], [""]],
            ["Sub Summon Portraits", "sp/assets/summon/party_sub/", "jpg", "img_low/", ["", "_01", "_02"], [""]],
            ["Raid Portraits", "sp/assets/summon/raid_normal/", "jpg", "img/", ["", "_01", "_02"], [""]],
            ["Summon Call Sheets", "sp/cjs/summon_", "png", "img_low/", ["_attack", "_01_attack", "_02_attack"], ["", "_a", "_b", "_c", "_d", "_e", "_f", "_bg", "_bg1", "_bg2", "_bg3"]],
            ["Summon Damage Sheets", "sp/cjs/summon_", "png", "img_low/", ["_damage", "_01_damage", "_02_damage"], ["", "_a", "_b", "_c", "_d", "_e", "_f", "_bg", "_bg1", "_bg2", "_bg3"]]
        ]
        jsoncontent = {}
        for a in assets:
            for sub1 in a[4]:
                for sub2 in a[5]:
                    try:
                        f = "http://" + endpoint + "assets_en/" + a[3] + a[1] + id + sub1 + sub2 + "." + a[2]
                        url_handle = self.req(f)
                        url_handle.read()
                        url_handle.close()
                        if a[0] not in jsoncontent:
                            jsoncontent[a[0]] = []
                        jsoncontent[a[0]].append(f)
                    except:
                        pass
            if a[0] == "Main Arts":
                try:
                    f = "https://media.skycompass.io/assets/archives/summons/" + id + "/detail_l.png"
                    url_handle = self.req(f)
                    url_handle.read()
                    url_handle.close()
                    if a[0] not in jsoncontent:
                        jsoncontent[a[0]] = []
                    jsoncontent[a[0]].append(f)
                except:
                    pass
        if len(jsoncontent.keys()) != 0:
            with open("docs/data/" + id + ".json", "w") as out:
                json.dump(jsoncontent, out)
            print("Saved", id + ".json")
        else:
            print("Warning:", id, "didn't return any positive result")
        
    def processCharacter(self, id, endpoint):
        if os.path.exists("docs/data/" + id + ".json"): return
        skinFolder = ["", "skin/"] if id[1] == '7' else [""]
        skinAppend = ["", "_s1", "_s2", "_s3", "_s4", "_s5", "_s6"] if id[1] == '7' else [""]
        assets = [
            ["Main Arts", "sp/assets/npc/zoom/", "png", "img_low/", [""], [""], ["", "_0", "_1"], [""], ["_01", "_02", "_03", "_04", "_81", "_82", "_83"], [""]],
            ["Inventory Portraits", "sp/assets/npc/m/", "jpg", "img_low/", [""], [""], ["", "_0", "_1"], [""], ["_01", "_02", "_03", "_04", "_81", "_82", "_83"], [""]],
            ["Square Portraits", "sp/assets/npc/s/", "jpg", "img_low/", skinFolder, skinAppend, ["", "_0", "_1"], [""], ["_01", "_02", "_03", "_04", "_81", "_82", "_83"], [""]],
            ["Party Portraits", "sp/assets/npc/f/", "jpg", "img_low/", skinFolder, skinAppend, ["", "_0", "_1"], [""], ["_01", "_02", "_03", "_04", "_81", "_82", "_83"], [""]],
            ["Sprites", "sp/assets/npc/sd/", "png", "img/", [""], [""], [""], [""], ["_01", "_02", "_03", "_04", "_81", "_82", "_83"], [""]],
            ["Raid", "sp/assets/npc/raid_normal/", "jpg", "img/", [""], [""], ["", "_0", "_1"], [""], ["_01", "_02", "_03", "_04", "_81", "_82", "_83"], [""]],
            ["Twitter Arts", "sp/assets/npc/sns/", "jpg", "img_low/", [""], [""], ["", "_0", "_1"], [""], ["_01", "_02", "_03", "_04", "_81", "_82", "_83"], [""]],
            ["Charge Attack Cutins", "sp/assets/npc/cutin_special/", "jpg", "img_low/", [""], [""], ["", "_0", "_1"], [""], ["_01", "_02", "_03", "_04", "_81", "_82", "_83"], [""]],
            ["Chain Cutins", "sp/assets/npc/raid_chain/", "jpg", "img_low/", [""], [""], ["", "_0", "_1"], [""], ["_01", "_02", "_03", "_04", "_81", "_82", "_83"], [""]],
            ["Character Sheets", "sheet", "img_low/", "npc_", ["_01", "_02", "_03", "_04"], ["", "_f1"]],
            ["Attack Effect Sheets", "sheet", "img_low/", "phit_", [""], ["", "_f1", "_1", "_1_f1", "_2", "_2_f1"]],
            ["Charge Attack Sheets", "sheet", "img_low/", "nsp_", ["_01", "_02", "_03", "_04"], ["", "_f1", "_1", "_1_f1", "_2", "_2_f1", "_s2", "_f1_s2", "_1_s2", "_1_f1_s2", "_2_s2", "_2_f1_s2"]],
            ["AOE Skill Sheets", "sheet","img_low/", "ab_all_", ["_01", "_02", "_03", "_04"], [""]],
            ["Single Target Skill Sheets", "sheet", "img_low/", "ab_", ["_01", "_02", "_03", "_04"], [""]]
        ]
        if id in self.null_characters:
            if id[1] == '7':
                for a in assets:
                    a[-1] = ["_01"]
            assets[0][-1] = ["", "_01"]
            assets[1][-1] = ["", "_01", "_02", "_03", "_04", "_05", "_06"]
            assets[2][-1] = ["", "_01", "_02", "_03", "_04", "_05", "_06"]
            assets[3][-1] = ["", "_01", "_02", "_03", "_04", "_05", "_06"]
            assets[8][-1] = ["", "_01", "_02", "_03", "_04", "_05", "_06"]
        isSkin = id[1] == '7'
        isMulti = True
        isGender = True
        
        jsoncontent = {}
        
        for a in assets:
            if a[1] == "sheet": continue
            for skin in a[4]:
                for sub1 in a[5]:
                    if sub1 != "" and not isGender: continue
                    for sub2 in a[6]:
                        if sub2 != "" and not isMulti: continue
                        for sub3 in a[7]:
                            for uncap in a[8]:
                                for extra in a[9]:
                                    try:
                                        f = "http://" + endpoint + "assets_en/img_low/" + a[1] + skin + id + uncap + extra + sub1 + sub2 + sub3 + "." + a[2]
                                        url_handle = self.req(f)
                                        url_handle.read()
                                        url_handle.close()
                                        if a[0] not in jsoncontent:
                                            jsoncontent[a[0]] = []
                                        jsoncontent[a[0]].append(f.replace('img_low/', a[3]))
                                    except:
                                        if a[0] == "Inventory Portraits":
                                            if sub1 != "": isGender = False
                                            if sub2 != "": isMulti = False
                                    if a[0] == "Main Arts" and skin == a[4][0]:
                                        try:
                                            f = "https://media.skycompass.io/assets/customizes/characters/1138x1138/" + id + uncap + extra + sub1 + sub2 + sub3 + "." + a[2]
                                            url_handle = self.req(f)
                                            url_handle.read()
                                            url_handle.close()
                                            if a[0] not in jsoncontent:
                                                jsoncontent[a[0]] = []
                                            jsoncontent[a[0]].append(f)
                                        except:
                                            pass
        for a in assets:
            if a[1] != "sheet": continue
            for sub1 in a[4]:
                for sub2 in a[5]:
                    try:
                        f = "http://" + endpoint + "assets_en/" + self.version + "/js_low/model/manifest/" + a[3] + id + sub1 + sub2 + ".js"
                        url_handle = self.req(f)
                        data = url_handle.read().decode("utf-8")
                        url_handle.close()
                        st = data.find('manifest:') + len('manifest:')
                        ed = data.find(']', st) + 1
                        data = json.loads(data[st:ed].replace('Game.imgUri+', '').replace('src', '"src"').replace('type', '"type"').replace('id', '"id"'))
                        for l in data:
                            if a[0] not in jsoncontent:
                                jsoncontent[a[0]] = []
                            jsoncontent[a[0]].append("http://" + endpoint + "assets_en/" + a[3] + l['src'].split('?')[0])
                    except:
                        pass
        if len(jsoncontent.keys()) != 0:
            with open("docs/data/" + id + ".json", "w") as out:
                json.dump(jsoncontent, out)
            print("Saved", id + ".json")
        else:
            print("Warning:", id, "didn't return any positive result")

    def manualUpdate(self):
        for id in self.new:
            if len(id) == 10:
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
        g.update()
        g.save()
    elif len(sys.argv) > 2 and sys.argv[1] == '-jsonupdate':
        g.new = sys.argv[2:]
        g.manualUpdate()
        g.jsonGenerator()
    else:
        g.run()