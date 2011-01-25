#!/usr/bin/env python

import rtorrent
import json
import time

RT = rtorrent.rtorrent(5000)

torrents = RT.getTorrentList()

timer = json.loads(open(".timer.json").read())

for id, name in torrents.iteritems():
    if id not in timer.keys():
        print "%s: " % name
        ttl = raw_input("Insert timer: ")
        if ttl == ".":
            ttl = "432000"
        try:
            ttl = int(ttl)
        except ValueError:
            continue
        else:
            fakestart = time.time() + ttl - 1209600
            timer[id] = ["SRC",fakestart]
            print timer[id]

jsonObject = json.dumps(timer)
open(".timer.json.blah","w").write(jsonObject)

