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

def read(data):
    try:
        j = json.loads(pyperclip.paste())
        assert("files" in j)
        assert("names" in j)
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
        print("Updated data, type 'report' or 'copy' to retrieve it")
    except Exception as e:
        print("Can't read clipboard data:", e)
        return

def to_ordered_id(data):
    return {
        "ids": sorted(list(data["ids"])),
        "suffixes": {k: sorted(list(v)) for k, v in sorted(data["suffixes"].items())},
        "names": {k: sorted(list(v)) for k, v in sorted(data["names"].items())}
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

def copy(data):
    try:
        j = to_ordered_id(data)
        j["ids"] = " ".join(j["ids"])
        pyperclip.copy(json.dumps(j, default=list, indent=4, ensure_ascii=False))
        print("Data has been copied to your clipboard")
    except:
        print("An unexpected error occured")

data = {"ids":set(), "suffixes":{}, "names":{}}
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
        case _:
            read(data)