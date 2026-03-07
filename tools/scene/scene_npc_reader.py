try:
    import pyperclip
except:
    print("Missing module:")
    print("pip install pyperclip")
    exit(0)
import json

def print_help():
    print("Commands:")
    print("\tReturn to add a scene")
    print("\t'quit' to quit")
    print("\t'report' to print the data")
    print("\t'copy' to copy the data")
    print("\t'image' to dump the image list")

def read(data):
    try:
        j = json.loads(pyperclip.paste())
        assert("files" in j)
        assert("names" in j)
        assert("images" in j)
        for f in j["files"]:
            sp = f.split("_", 1)
            if len(sp) == 2:
                sp[1] = "_" + sp[1]
                if sp[1] not in data["suffixes"]:
                    data["suffixes"][sp[1]] = set()
                data["suffixes"][sp[1]].add(sp[0])
            data["ids"].add(sp[0])
        for k, v in j["names"].items():
            if k not in data["names"]:
                data["names"][k] = set()
            for n in v:
                data["names"][k].add(n)
        for f in j["images"]:
            data["images"].add(f)
        print("Updated data, type 'report' or 'copy' to retrieve it")
    except Exception as e:
        print("Can't read clipboard data:", e)
        return

def to_ordered_id(data):
    return {
        "ids": sorted(list(data["ids"])),
        "suffixes": {k: sorted(list(v)) for k, v in sorted(data["suffixes"].items())},
        "names": {k: sorted(list(v)) for k, v in sorted(data["names"].items())},
        "images": sorted(list(data["images"]))
    }

def report(data):
    ordered = to_ordered_id(data)
    print(f"# ID list ({len(ordered['ids'])})")
    print(" ".join(list(ordered['ids'])))
    print(f"# Suffix list ({len(ordered['suffixes'])})")
    for k, v in ordered['suffixes'].items():
        print(f"{k}: {", ".join(list(v))}")
    print(" ".join(list(ordered['suffixes'])))
    print(f"# Name list ({len(ordered['names'])})")
    for k, v in ordered['names'].items():
        print(f"{k}: {", ".join(list(v))}")
    print(f"# {len(ordered['images'])} images")

def copy(data):
    try:
        j = to_ordered_id(data)
        j["ids"] = " ".join(j["ids"])
        pyperclip.copy(json.dumps(j, default=list, indent=4, ensure_ascii=False))
        print("Data has been copied to your clipboard")
    except:
        print("An unexpected error occured")

def image(data):
    try:
        l = sorted(list(data["images"]))
        if len(l) == 0:
            print("No images in memory")
            return
        possible_event_ids = {}
        best_guess = None
        for f in l:
            if f.startswith("scene_evt"):
                pid = f.split("scene_evt", 1)[1].split("_")[0].split(".")[0]
                if len(pid) == 6 and pid.isdigit():
                    possible_event_ids[pid] = possible_event_ids.get(pid, 0) + 1
                    if pid != best_guess and possible_event_ids[pid] > possible_event_ids.get(best_guess, 0):
                        best_guess = pid
        if len(possible_event_ids) == 0:
            print("No valid images in memory")
            return
        print(f"Guessed event ID: {best_guess}")
        print("Press return to continue or a different event ID (6 digits) if wrong or type 'c' to cancel")
        while True:
            s = input().lower().strip()
            if len(s) == 0:
                evid = best_guess
                break
            elif s == "c":
                return
            elif len(s) == 6 and s.isdigit():
                evid = s
                break
        print(f"Writing scene_evt{evid} image list to {evid}.json...")
        img_list = []
        for f in l:
            if f.startswith("scene_evt" + evid):
                img_list.append(f)
        with open(evid + ".json", mode="w", encoding="utf-8") as f:
            json.dump(img_list, f)
        print(f"{evid}.json written")
    except:
        print("An unexpected error occured")

data = {"ids":set(), "suffixes":{}, "names":{}, "images":set()}
print_help()
while True:
    match input().lower():
        case 'quit'|'q':
            break
        case 'help'|'h':
            print_help()
        case 'report'|'r':
            report(data)
        case 'copy'|'c':
            copy(data)
        case 'image'|'img'|'i':
            image(data)
        case _:
            read(data)