import tkinter as Tk
from tkinter.simpledialog import askstring, messagebox
import json

class Editor(Tk.Tk):
    LISTSIZE = 40
    NWIDTH = 150

    def __init__(self) -> None: # set the directory to tracker.pyw directory if imported as an external module
        Tk.Tk.__init__(self,None)
        self.title("GBFAL Nameless NPC Editor")
        self.resizable(width=False, height=False) # not resizable
        self.minsize(200, 200)
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        
        self.data = {}
        self.npcs = {}
        self.names = set()
        self.modified = False
        
        try:
            with open("json/data.json", mode="r", encoding="utf-8") as f:
                self.data = json.load(f)
                for k, d in self.data.get("npcs",{}).items():
                    if isinstance(d, list):
                        if not d[0]:
                            self.npcs[k] = None
                for k, d in self.data.get("lookup",{}).items():
                    if "@@" in d:
                        n = d.split("@@", 1)[1].split(" ", 1)[1]
                    else: n = d
                    nt = n.split(" ")
                    i = 0
                    while i < len(nt):
                        if nt[i] in ["N", "R", "SR", "SSR", "sabre", "axe", "spear", "gun", "staff", "melee", "harp", "katana", "bow", "dagger"]:
                            i += 1
                        else:
                            break
                    n = " ".join(nt[i:-1])
                    if n == "": continue
                    self.names.add(n)
                    if k in self.npcs:
                        self.npcs[k] = n
        except Exception as e:
            print(e)
            print("Failed to open GBFAL data.json")
            print("Exiting...")
            exit(0)

        self.names = list(self.names)
        self.names.sort()
        
        # ui
        Tk.Label(self, text="Names").grid(row=0, column=0, sticky="w")
        self.nvar = Tk.Variable(value=self.names)
        self.nlist = Tk.Listbox(self, listvariable=self.nvar, height=self.LISTSIZE, selectmode=Tk.SINGLE, width=self.NWIDTH)
        self.nlist.grid(row=1, column=0, rowspan=self.LISTSIZE, columnspan=2, sticky="wesn")
        
        Tk.Button(self, text="Add", command=self.add_name).grid(row=self.LISTSIZE+1, column=0, sticky="wesn")
        Tk.Button(self, text="Del", command=self.del_name).grid(row=self.LISTSIZE+1, column=1, sticky="wesn")
        
        bar = Tk.Scrollbar(self, orient="vertical")
        bar.config(command=self.nlist.yview)
        bar.grid(row=1, column=2, rowspan=self.LISTSIZE, sticky="sn")
        
        Tk.Label(self, text="NPCs").grid(row=0, column=3, sticky="w")
        knpc = list(self.npcs.keys())
        knpc.sort()
        self.svar = Tk.Variable(value=knpc)
        self.slist = Tk.Listbox(self, listvariable=self.svar, height=self.LISTSIZE, selectmode=Tk.SINGLE)
        self.slist.grid(row=1, column=3, rowspan=self.LISTSIZE, columnspan=2, sticky="wesn")
        self.slist.bind('<<ListboxSelect>>', self.npc_selected)
        try: self.slist.select_set(0)
        except: pass
        
        Tk.Button(self, text="<<", command=self.previous_npc).grid(row=self.LISTSIZE+1, column=3, sticky="wesn")
        Tk.Button(self, text=">>", command=self.next_npc).grid(row=self.LISTSIZE+1, column=4, sticky="wesn")
        
        bar = Tk.Scrollbar(self, orient="vertical")
        bar.config(command=self.slist.yview)
        bar.grid(row=1, column=5, rowspan=self.LISTSIZE, sticky="sn")
        
        self.remaining = Tk.Label(self, text="{} nameless NPCs".format(list(self.npcs.values()).count(None)))
        self.remaining.grid(row=0, column=6, columnspan=5, sticky="w")
        
        self.current = Tk.Label(self, text="")
        self.current.grid(row=1, column=6, columnspan=5, sticky="w")
        self.currentvalue = Tk.Label(self, text="")
        self.currentvalue.grid(row=2, column=6, columnspan=5, sticky="w")
        self.slist.event_generate("<<ListboxSelect>>")
        
        Tk.Button(self, text="Update name", command=self.update_npc).grid(row=3, column=6, sticky="wesn")
        
        Tk.Button(self, text="Save", command=self.save).grid(row=0, column=20, sticky="wesn")

    def close(self) -> None:
        self.destroy()

    def save(self) -> None:
        self.remaining.config(text="{} nameless NPCs".format(list(self.npcs.values()).count(None)))

    def npc_selected(self, event) -> None:
        a = self.slist.curselection()
        if len(a) == 0:
            self.current.config(text="")
            return
        a = a[0]
        k = list(self.npcs.keys())[a]
        self.current.config(text="ID: {}".format(k))
        if self.npcs[k] is None: s = "Not Set"
        else: s = self.npcs[k]
        self.currentvalue.config(text=s)

    def add_name(self) -> None:
        n = askstring('Add a name', 'Input a NPC tag')
        if n in ["", None]: return
        if n in self.names:
            messagebox.showerror("Error", "The name is already in the list")
        else:
            self.names.append(n)
            self.names.sort()
            i = self.names.index(n)
            self.nvar.set(self.names)
            self.nlist.selection_clear(0, Tk.END)
            self.nlist.select_set(i)
            self.nlist.yview(i)

    def del_name(self) -> None:
        a = self.nlist.curselection()
        if len(a) == 0: return
        a = a[0]
        if a < 0 or a >= len(self.names): return
        if messagebox.askquestion(title="Confirm", message="Delete the entry: '{}' ?".format(self.names[a])) == "yes":
            self.names = self.names[:a] + self.names[a+1:]
            self.nvar.set(self.names)
            self.nlist.selection_clear(0, Tk.END)
            self.nlist.select_set(max(0, a-1))

    def previous_npc(self) -> None:
        a = self.slist.curselection()
        if len(a) == 0: return
        a = a[0]
        i = a
        keys = list(self.npcs.keys())
        while True:
            i -= 1
            if i < 0: i = len(self.npcs) - 1
            if self.npcs[keys[i]] is None:
                break
            if a == i:
                return
        self.slist.selection_clear(0, Tk.END)
        self.slist.select_set(i)
        self.slist.yview(i)
        self.slist.event_generate("<<ListboxSelect>>")

    def next_npc(self) -> None:
        a = self.slist.curselection()
        if len(a) == 0: return
        a = a[0]
        i = a
        keys = list(self.npcs.keys())
        while True:
            i += 1
            if i >= len(self.npcs): i = 0
            if self.npcs[keys[i]] is None:
                break
            if a == i:
                return
        self.slist.selection_clear(0, Tk.END)
        self.slist.select_set(i)
        self.slist.yview(i)
        self.slist.event_generate("<<ListboxSelect>>")

    def update_npc(self) -> None:
        a = self.nlist.curselection()
        b = self.slist.curselection()
        a = a[0] if len(a) > 0 else 0
        b = b[0] if len(b) > 0 else 0
        try:
            a = self.names[a]
        except:
            return
        try:
            b = list(self.npcs.keys())[b]
        except:
            return
        
        print(a, b)

if __name__ == "__main__": # entry point
    Editor().mainloop()