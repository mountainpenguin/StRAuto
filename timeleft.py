#!/usr/bin/env python

import sys
import json
import time
import rtorrent
RT = rtorrent.rtorrent(5000)

timer = json.loads(open(".timer.json").read())

config = open("strauto.config").read()
SRC_TTL = int(config.split("SRC_TTL = ")[1].split("\n")[0])
STR_TTL_SEEDED = int(config.split("STR_TTL_SEEDED = ")[1].split("\n")[0])
STR_TTL_UNSEEDED = int(config.split("STR_TTL_UNSEEDED = ")[1].split("\n")[0])

db = {}
for id in timer.keys():
    try:
        name = RT.getNameByID(id)
    except:
        print "ID: %s doesn't exist" % id
        continue
    type = timer[id][0]
    added = timer[id][1]
    if type == "SRC":
        timediff = time.time() - added
        timeleft = SRC_TTL - timediff
    elif type == "STR":
        timediff = time.time() - added
        ratio = RT.getRatio(id)
        if ratio > 1:
            timeleft = STR_TTL_SEEDED - timediff
        else:
            timeleft = STR_TTL_UNSEEDED - timediff

    seconds = timeleft + 1 - 1
    toprint = ""
    if seconds > 604800:
        weeks = seconds / 604800
        seconds = seconds % 604800
        toprint += "%iw " % weeks
    if seconds > 86400:
        days = seconds / 86400
        seconds = seconds % 86400
        toprint += "%id " % days
    if seconds > 3600:
        hours = seconds / 3600
        seconds = seconds % 3600
        toprint += "%ih " % hours
    if seconds > 60:
        minutes = seconds / 60
        seconds = seconds % 60
        toprint += "%im " % minutes
    toprint += "%is" % seconds
    db[id] = [name, toprint, timeleft]

dbitems = db.items()
sorteditems = sorted(dbitems, key=lambda x: x[1][2])

#split into 4 hour "chunks"
time_sec = 0
count = 0
count2 = 1
interval = 14400
current = 0

coords = [] # (x,y)
print len(sorteditems)
while count + 1 < len(sorteditems):
    while True:
        try:
            item = sorteditems[count]
        except IndexError:
            break
        if item[1][2] < time_sec + interval:
#            print item[1][0], item[1][1], item[1][2], time_sec + interval, count
#            raw_input()
            current += 1
            count += 1
        else:
            if current != 0:
                print "<%ih : %i deletions scheduled" % ((count2*4),current)
                coords += [(count2*4,current)]
            current = 0
            count2 += 1
            time_sec += interval
            break
if current != 0:
    print "<%ih : %i deletions scheduled" % ((count2*4),current)
    coords += [(count2*4,current)]

print "First item to be deleted: %s in %s (%ih)" % (sorteditems[0][1][0], sorteditems[0][1][1], sorteditems[0][1][2]/60/60)
print "Last item to be deleted: %s in %s (%ih)" % (sorteditems[-1][1][0], sorteditems[-1][1][1], sorteditems[-1][1][2]/60/60)

#coords_actual = []
#firstx = coords[0][0]
#for i in coords:
#    coords_actual += [(i[0]-firstx,i[1])]

##coords_sorted = sorted(coords_actual, key=lambda x: x[1])

##coords_sorted.reverse()
#yvalues = {}
#for i in coords_actual:
#    if i[1] in yvalues.keys():
#        yvalues[i[1]] += [i[0]]
#    else:
#        yvalues[i[1]] = [i[0]]
#
#ykeys = yvalues.keys()
#ykeys.sort()
#ykeys.reverse()
#
#for yvalue in ykeys:
#    xvalues = yvalues[yvalue]
#    xvalues.sort()
#    for i in range(xvalues[-1]):
#        testvalue = i+1
#        if testvalue not in xvalues:
#            sys.stdout.write(" ")
#        else:
#            sys.stdout.write("*")
#    sys.stdout.write("\n")
#    sys.stdout.flush()
