import json
import mmap
import time

t = time.time()
for i in range(20):
    with open("json/data.json", mode="rb") as f:
        json.load(f)
print(time.time() - t)

t = time.time()
for i in range(20):
    with open("json/data.json", mode="rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            json.load(mm)
print(time.time() - t)