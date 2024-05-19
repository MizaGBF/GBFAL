import tkinter as Tk
from tkinter.simpledialog import askstring, messagebox
import json
import asyncio
import aiohttp
import html

class Editor(Tk.Tk):
    LISTSIZE = 40
    NWIDTH = 150
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'

    def __init__(self) -> None: # set the directory to tracker.pyw directory if imported as an external module
        Tk.Tk.__init__(self,None)
        self.title("GBFAL Lookup Editor")
        self.resizable(width=False, height=False) # not resizable
        self.minsize(200, 200)
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        
        self.entries = {}
        self.names = set()
        self.filtered = []
        self.modified = False
        
        try:
            with open("json/data.json", mode="r", encoding="utf-8") as f:
                data = json.load(f)
                for k, d in data.get("npcs",{}).items():
                    if isinstance(d, list):
                        if not d[0]:
                            self.entries[k] = None
                for k, d in data.get("enemies",{}).items():
                    if isinstance(d, list):
                        self.entries[k] = None
                for k, d in data.get("lookup",{}).items():
                    if d is None or d == "help-wanted": continue
                    if "@@" in d:
                        n = d.split("@@", 1)[1].split(" ", 1)[1]
                    else: n = d
                    nt = n.split(" ")
                    i = 0
                    while i < len(nt):
                        if nt[i] in ["/", "N", "R", "SR", "SSR", "n", "r", "sr", "ssr", "sabre", "axe", "spear", "gun", "staff", "melee", "harp", "katana", "bow", "dagger", "fire", "water", "earth", "wind", "light", "dark"]:
                            i += 1
                        else:
                            break
                    n = " ".join(nt[i:])
                    if n == "": continue
                    self.names.add(n)
                    if k in self.entries:
                        self.entries[k] = n
        except Exception as e:
            messagebox.showerror("Error", "Failed to open 'json/data.json'.\nExiting...")
            print(e)
            print("Failed to open GBFAL data.json")
            print("Exiting...")
            exit(0)

        try:
            with open("json/name_data.json", mode="r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise Exception("Invalid JSON structure")
        except Exception as e:
            print(e)
            data = {}
            if "No such file" not in str(e):
                messagebox.showerror("Error", "Failed to open 'json/name_data.json'.\nClose this app and fix it.")

        k_sort = {}
        for k in self.entries:
            if len(k) < 9:
                k_sort["9" + k.zfill(9)] = k
            else:
                k_sort[k] = k
        keys = list(k_sort.keys())
        keys.sort()
        tmp = {}
        for k in keys:
            tmp[k_sort[k]] = self.entries[k_sort[k]]
        self.entries = tmp
        for k, v in data.items():
            if k in self.entries and v is not None:
                self.entries[k] = v
        self.names = set(list(self.names) + list(self.entries.values()))
        if None in self.names: self.names.remove(None)
        self.names = list(self.names)
        self.names.sort()
        self.filtered = self.names
        
        asyncio.run(self.init_enemies())
        
        # ui
        Tk.Label(self, text="Names").grid(row=0, column=0, sticky="w")
        self.search_str = Tk.StringVar()
        self.search = Tk.Entry(self, textvariable=self.search_str)
        self.search.grid(row=0, column=1, sticky="wesn")
        self.search.bind('<Return>', self.filter)
        
        self.nvar = Tk.Variable(value=self.filtered)
        self.nlist = Tk.Listbox(self, listvariable=self.nvar, height=self.LISTSIZE, selectmode=Tk.SINGLE, exportselection=False, width=self.NWIDTH)
        self.nlist.grid(row=1, column=0, rowspan=self.LISTSIZE, columnspan=2, sticky="wesn")
        
        Tk.Button(self, text="Add", command=self.add_name).grid(row=self.LISTSIZE+1, column=0, sticky="wesn")
        Tk.Button(self, text="Del", command=self.del_name).grid(row=self.LISTSIZE+1, column=1, sticky="wesn")
        
        bar = Tk.Scrollbar(self, orient="vertical")
        bar.config(command=self.nlist.yview)
        bar.grid(row=1, column=2, rowspan=self.LISTSIZE, sticky="sn")
        self.nlist.config(yscrollcommand=bar.set)
        
        Tk.Label(self, text="IDs").grid(row=0, column=3, sticky="w")
        keys = list(self.entries.keys())
        self.svar = Tk.Variable(value=keys)
        self.slist = Tk.Listbox(self, listvariable=self.svar, height=self.LISTSIZE, selectmode=Tk.SINGLE, exportselection=False)
        self.slist.grid(row=1, column=3, rowspan=self.LISTSIZE, columnspan=2, sticky="wesn")
        self.slist.bind('<<ListboxSelect>>', self.selected)
        try: self.slist.select_set(0)
        except: pass
        
        Tk.Button(self, text="<<", command=self.previous).grid(row=self.LISTSIZE+1, column=3, sticky="wesn")
        Tk.Button(self, text=">>", command=self.next).grid(row=self.LISTSIZE+1, column=4, sticky="wesn")
        
        bar = Tk.Scrollbar(self, orient="vertical")
        bar.config(command=self.slist.yview)
        bar.grid(row=1, column=5, rowspan=self.LISTSIZE, sticky="sn")
        self.slist.config(yscrollcommand=bar.set)
        
        self.remaining = Tk.Label(self, text="{} nameless Entries".format(list(self.entries.values()).count(None)))
        self.remaining.grid(row=0, column=6, columnspan=5, sticky="w")
        
        self.current = Tk.Label(self, text="")
        self.current.grid(row=1, column=6, columnspan=5, sticky="w")
        self.currentvalue = Tk.Label(self, text="")
        self.currentvalue.grid(row=2, column=6, columnspan=5, sticky="w")
        self.selected()
        
        Tk.Button(self, text="Update name", command=self.update).grid(row=3, column=6, sticky="wesn")
        Tk.Button(self, text="New name", command=self.new_name).grid(row=4, column=6, sticky="wesn")
        Tk.Button(self, text="Edit name", command=self.edit_name).grid(row=5, column=6, sticky="wesn")
        Tk.Button(self, text="Clear", command=self.clear_name).grid(row=6, column=6, sticky="wesn")
        
        Tk.Button(self, text="Save", command=self.save).grid(row=0, column=20, sticky="wesn")

    async def init_enemies(self) -> None:
        try:
            m_count = 0
            async with aiohttp.ClientSession("https://gbf.wiki") as session:
                async with session.get("/index.php?title=Special:CargoExport&tables=enemies&fields=_pageName,icon_s,icon_m,name,element&format=json&limit=30000", headers={'User-Agent':self.USER_AGENT}, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        for e in data:
                            if (e["icon s"] is None and e["icon m"] is None) or e["name"] is None or e["element"] is None: continue
                            if e["icon s"] is not None:
                                id = e["icon s"].split(' ')[2]
                            else:
                                id = e["icon m"].split(' ')[2]
                            if self.entries.get(id, "") is not None: continue
                            element = e["element"].lower()
                            if element == "none": element = "null"
                            l = html.unescape(html.unescape(e["name"].lower().strip())) + " $$" + element
                            if l != self.entries[id]:
                                self.entries[id] = l
                                m_count += 1
            if m_count > 0:
                self.modified = True
                print(m_count, "enemies have been auto-initialized using the wiki")
        except Exception as e:
            print("Failed to access the wiki to retrieve the enemy list:", e)

    def close(self) -> None:
        self.save()
        self.destroy()

    def filter(self, event = None) -> None:
        sstr = self.search_str.get().strip().lower()
        a = self.nlist.curselection()
        if len(a) == 0: a = None
        else: a = a[0]
        if sstr == "":
            try: 
                a = self.names.index(self.filtered[a])
            except:
                a = None
            self.filtered = self.names
        else:
            sstr = sstr.split(" ")
            tmp = []
            for n in self.names:
                f = True
                for s in sstr:
                    if s not in n.lower():
                        f = False
                        break
                if f:
                    tmp.append(n)
            try:
                a = tmp.index(self.filtered[a])
            except:
                a = None
            self.filtered = tmp
        self.nvar.set(self.filtered)
        if a is not None:
            try:
                self.nlist.selection_clear(0, Tk.END)
                self.nlist.select_set(a)
                self.nlist.yview(a)
            except:
                pass

    def save(self) -> None:
        if self.modified:
            if messagebox.askquestion(title="Save", message="Save the changes?") == "yes":
                try:
                    with open('json/name_data.json', mode='w', encoding='utf-8') as outfile:
                        json.dump(self.entries, outfile, separators=(',', ':'), ensure_ascii=False, indent=0)
                    self.modified = False
                    self.remaining.config(text="{} nameless NPCs".format(list(self.entries.values()).count(None)))
                except Exception as e:
                    messagebox.showerror("Error", "An error occured: '{}'".format(e))

    def selected(self, event = None) -> None:
        a = self.slist.curselection()
        if len(a) == 0:
            self.current.config(text="NO ENTRY SELECTED")
            self.currentvalue.config(text="---------------------------- Not Set ----------------------------")
            return
        a = a[0]
        k = list(self.entries.keys())[a]
        self.current.config(text="ID: {}".format(k))
        if self.entries[k] is None: s = "---------------------------- Not Set ----------------------------"
        else: s = self.entries[k]
        self.currentvalue.config(text=s)

    def add_name(self, silent : bool = False, init : str = "") -> None:
        n = askstring('Add a name', 'Input the lookup string', initialvalue=init)
        if n in ["", None]: return None
        n = n.lower()
        if n in self.names:
            if not silent:
                messagebox.showerror("Error", "The name is already in the list")
        else:
            self.names.append(n)
            self.names.sort()
            self.modified = True
            self.filter()
            try:
                a = self.filtered.index(n)
                self.nlist.selection_clear(0, Tk.END)
                self.nlist.select_set(a)
                self.nlist.yview(a)
            except:
                pass
        return n

    def del_name(self) -> None:
        a = self.nlist.curselection()
        if len(a) == 0: return
        a = a[0]
        if a < 0 or a >= len(self.filtered): return
        a = self.names.index(self.filtered[a])
        if messagebox.askquestion(title="Confirm", message="Delete the name: '{}' ?".format(self.names[a])) == "yes":
            del self.names[a]
            self.modified = True
            self.filter()
            try:
                a = max(0, a-1)
                self.nlist.selection_clear(0, Tk.END)
                self.nlist.select_set(a)
                self.nlist.yview(a)
            except:
                pass

    def previous(self) -> None:
        a = self.slist.curselection()
        if len(a) == 0: return
        a = a[0]
        keys = list(self.entries.keys())
        for i in range(len(self.entries)):
            a -= 1
            if a < 0: a = len(self.entries) - 1
            if self.entries[keys[a]] is None:
                break
        self.slist.selection_clear(0, Tk.END)
        self.slist.select_set(a)
        self.slist.yview(a)
        self.selected()

    def next(self) -> None:
        a = self.slist.curselection()
        if len(a) == 0: return
        a = a[0]
        keys = list(self.entries.keys())
        for i in range(len(self.entries)):
            a += 1
            if a >= len(self.entries): a = 0
            if self.entries[keys[a]] is None:
                break
        self.slist.selection_clear(0, Tk.END)
        self.slist.select_set(a)
        self.slist.yview(a)
        self.selected()

    def update(self) -> None:
        a = self.nlist.curselection()
        b = self.slist.curselection()
        a = a[0] if len(a) > 0 else 0
        b = b[0] if len(b) > 0 else 0
        try:
            a = self.filtered[a]
        except:
            return
        try:
            b = list(self.entries.keys())[b]
        except:
            return
        self.modified = True
        self.entries[b] = a
        self.bell()
        self.selected()

    def new_name(self, init : bool = False) -> None:
        b = self.slist.curselection()
        b = b[0] if len(b) > 0 else 0
        try:
            b = list(self.entries.keys())[b]
        except:
            return
        a = self.add_name(silent=True, init=(self.entries[b] if init else ""))
        if a is None: return
        self.entries[b] = a
        self.modified = True
        self.bell()
        self.selected()

    def edit_name(self) -> None:
        self.new_name(init=True)

    def clear_name(self) -> None:
        try: b = self.slist.curselection()[0]
        except: return
        try:
            b = list(self.entries.keys())[b]
        except:
            return
        self.modified = True
        self.entries[b] = None
        self.bell()
        self.selected()

if __name__ == "__main__": # entry point
    Editor().mainloop()