#!/usr/bin/env python

"""
Director: vertani
Supervisor: vertani
Manager: vertani
Brains: vertani
Moral-Support: vertani
Beta-tester: vertani
Author: mountainpenguin

Contact: irc.sharetheremote.org (nick mountainpenguin)
License: GPL v3
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
TO-DO
1. nuke check
2. allow any input (i.e. multiple sources)
3. setup script

NOTES
1.  - if file already exists, check for REPACK | PROPER | REAL etc. (add into dupe_check())
    - get nuke reason for previous release // ignore dirfixes
    - report on StR
    - upload
2.  - How to deal with non-scene filenames?
3.  - install files
    - check imports MultipartPostHandler etc.
    - check rtorrent xmlrpc
    - easy configuration
        @ show_id by show name <- also as seperate script
        @ check username / password
        @ allow human readable time inputs
        @ check paths
        @ check rtorrent configuration?
"""

VERSION = "0.40.5"
##########################################################################################################

# CHANGE THESE APPROPRIATELY USING FULL PATHS WHERE NOT SPECIFIED OTHERWISE
CONFIG_FILE = "strauto.config"
LOG_FILE = "strauto.log" # full or relative path to where strauto will log

##########################################################################################################

##########################################################################################################
# CHANGES TO DO
# clean up files properly if not uploaded

import os
import sys
import subprocess
import threading
import time
import re
import glob
import sys
import urllib
import urllib2
import cookielib
import calendar
import datetime
import traceback
import shutil
import rtorrent
import JSONtimer
import json

class _queue:
    def __init__(self):
        try:
            _QUEUE = open(".queue").read().split("\n")
            self.QUEUE = []
            for i in _QUEUE:
                items = i.split("|-!!!!-|")
                try:
                    self.QUEUE += [(items[0], items[1])]
                except IndexError:
                    pass
        except:
            self.QUEUE = []
            
    def add(self, path):
        self.QUEUE += [(path,time.time())]
        
    def remove(self, path):
        indexes = []
        index = 0
        for queued in self.QUEUE:
            if queued[0] == path:
                indexes += [index]
            index += 1
        indexes.sort()
        indexes.reverse()
        for i in indexes:
            del self.QUEUE[i]
            
    def next(self):
        if len(self.QUEUE) > 0:
            return self.QUEUE[0]
        else:
            return None
        
    def close(self):
        os.remove(".queue")
        queuefile = open(".queue","a")
        for i in self.QUEUE:
            queuefile.write("%s|-!!!!-|%i\n" % (i[0], i[1]))
        queuefile.close()
    
        
        
LOGFILE = open(LOG_FILE, "a")
ERROR = open("error.log","a")
TIMER = JSONtimer.JSONtimer()
UPLOADQUEUE = _queue()
#{"id" : (protocol, timestarted)}
config = open(CONFIG_FILE).read()

announce_url = re.compile("ANNOUNCE_URL = \"(.*?)\"")
username = re.compile("USERNAME = \"(.*?)\"")
password = re.compile("PASSWORD = \"(.*?)\"")
file_destination = re.compile("FILE_DESTINATION = \"(.*?)\"")
torrent_destination = re.compile("TORRENT_DESTINATION = \"(.*?)\"")
watchfilepath = re.compile("WATCHFILEPATH = \"(.*?)\"")
show_id_file = re.compile("SHOW_ID_FILE = \"(.*?)\"")
log_file = re.compile("LOG_FILE = \"(.*?)\"")
xmlrpc_port = re.compile("XMLRPC_PORT = (\d+)")
src_ttl = re.compile("SRC_TTL = (\d+)")
str_ttl_seeded = re.compile("STR_TTL_SEEDED = (\d+)")
str_ttl_unseeded = re.compile("STR_TTL_UNSEEDED = (\d+)")
delay = re.compile("DELAY = (\d+)")

#5020 for 0day stuff, 5010 for strauto

trying = "ANNOUNCE_URL"
try:
    ANNOUNCE_URL = announce_url.findall(config)[0]
    trying = "USERNAME"
    USERNAME = username.findall(config)[0]
    trying = "PASSWORD"
    PASSWORD = password.findall(config)[0]
    trying = "FILE_DESTINATION"
    FILE_DESTINATION = file_destination.findall(config)[0]
    trying = "TORRENT_DESTINATION"
    TORRENT_DESTINATION = torrent_destination.findall(config)[0]
    trying = "WATCHFILEPATH"
    WATCHFILEPATH = watchfilepath.findall(config)[0]
    trying = "SHOW_ID_FILE"
    SHOW_ID_FILE = show_id_file.findall(config)[0]
    trying = "XMLRPC_PORT"
    XMLRPC_PORT = int(xmlrpc_port.findall(config)[0])
    trying = "SRC_TTL"
    SRC_TTL = int(src_ttl.findall(config)[0])
    trying = "STR_TTL_SEEDED"
    STR_TTL_SEEDED = int(str_ttl_seeded.findall(config)[0])
    trying = "STR_TTL_UNSEEDED"
    STR_TTL_UNSEEDED = int(str_ttl_unseeded.findall(config)[0])
    trying = "DELAY"
    DELAY = int(delay.findall(config)[0])
    
    
except IndexError:
    print "Error parsing %s" % trying
    LOGFILE.write("\n(%s) Error parsing %s" % (time.asctime(time.localtime()), trying))
    LOGFILE.flush()
    sys.exit()
except ValueError:
    print "Error parsing %s, number expected, got string instead" % trying
    LOGFILE.write("\n(%s) Error parsing %s, number expected, got string instead" % (time.asctime(time.localtime()), trying))
    LOGFILE.flush()
    sys.exit()

try:
    LOG_FILE = log_file.findall(config)[0]
except IndexError:
    pass

RT = rtorrent.rtorrent(XMLRPC_PORT)

try:
    import MultipartPostHandler
except ImportError:
    print "Getting MultipartPostHandler"
    response = urllib2.urlopen("http://odin.himinbi.org/MultipartPostHandler.py").read()
    open("MultipartPostHandler.py", "w").write(response)
    import MultipartPostHandler
    
try:
    import xmlrpc2scgi as xmlrpc
except ImportError:
    print "Getting xmlrpc2scgi"
    response = urllib2.urlopen("http://libtorrent.rakshasa.no/raw-attachment/wiki/UtilsXmlrpc2scgi/xmlrpc2scgi.py").read()
    open("xmlrpc2scgi.py", "w").write(response)
    import xmlrpc2scgi as xmlrpc

def main():
    try:
        oldlastmod = 0
        oldlastmod_group = 0
        while True:
            original_dir = os.getcwd()
    
            group_lastmod = os.path.getmtime(SHOW_ID_FILE)
            if group_lastmod != oldlastmod_group:
                #parse it
                show_ids = open(SHOW_ID_FILE).read().replace(" ","").replace("\t","").split("\n")
                lineno = 0
                global SHOW_IDS
                SHOW_IDS = []
                for show_id in show_ids:
                    lineno += 1
                    if show_id == "":
                        pass
                    else:
                        if show_id[-1] != ",":
                            print "Error parsing %s on line %i, line must be terminated by a comma" % (SHOW_ID_FILE, lineno)
                            LOGFILE.write("\n(%s) Error parsing %s on line %i, line must be terminated by a comma" % (time.asctime(time.localtime()), SHOW_ID_FILE, lineno))
                            LOGFILE.flush()
                            SUCCESS = "NO"
                            break
                        else:
                            show_id = "".join(list(show_id)[:-1])
                            line = show_id.replace("(","").replace(")", "").replace("\"","").split(",")
                            try:
                                show_id_input = (line[0],line[1], line[2])
                                SHOW_IDS.append(show_id_input)
                                SUCCESS = "YES"
                            except IndexError:
                                print "Error parsing %s on line %i, fields must be seperated by a comma" % (SHOW_ID_FILE, lineno)
                                LOGFILE.write("\n(%s) Error parsing %s on line %i, fields must be seperated by a comma" % (time.asctime(time.localtime()), SHOW_ID_FILE, lineno))
                                LOGFILE.flush()
                                SUCCESS = "NO"
                                break
                        
                if SUCCESS == "YES":
                    print "%s successfully parsed" % SHOW_ID_FILE
                    LOGFILE.write("\n(%s) %s successfully parsed" % (time.asctime(time.localtime()), SHOW_ID_FILE))
                    LOGFILE.flush()
                        
                
                oldlastmod_group = group_lastmod
            
            lastmodified = os.path.getmtime(WATCHFILEPATH)
            if lastmodified != oldlastmod:
                watchfile = open(WATCHFILEPATH).read()
                if watchfile != "" and watchfile != "\n":
                    to_process = watchfile.split("\n")
                    open(WATCHFILEPATH, "w").write("")
                    #for i in to_process:
                    #    #add to QUEUE
                    #    LOGFILE.write("\n\n(%s):\n\tNew Release Detected: %s, adding to queue" % (time.asctime(time.localtime()), i))
                    #    UPLOADQUEUE.add(i)
                    #    LOGFILE.write("\n\tSuccessfully added to queue")
                    #    LOGFILE.flush()
                    #    
                    #open(WATCHFILEPATH,"w").write("")
                    #oldlastmod = os.path.getmtime(WATCHFILEPATH)
                    #
                    #next = True
                    #to_process = []
                    #while next:
                    #    next = UPLOADQUEUE.next()
                    #    if next:
                    #        addtime = next[1]
                    #        if time.time() - addtime > DELAY:
                    #            to_process += [next[0]]
                    #        else:
                    #            break
                        
                    
                    for i in to_process:
                        if i != "":
                            LOGFILE.write("\n\n(%s):\n\tRelease Added from queue: %s" % (time.asctime(time.localtime()), i))
                            LOGFILE.flush()
                            starttime = time.time()
                            #log starttime in .timer
                            name = os.path.basename(i)
                            try:
                                torrent_id = RT.getIDByName(name)
                                LOGFILE.write("\n\tGot torrent_id for SRC: %s" % torrent_id)
                                LOGFILE.flush()
                                TIMER.add_torrent(torrent_id, "SRC", time.time())
                                TIMER.flush()
                            except:
                                LOGFILE.write("\n" + traceback.format_exc())
                                LOGFILE.flush()
                                ERROR.write("\n" + traceback.format_exc())
                                ERROR.flush()
                            
                            process(i)
                            
                            time_taken = time.time() - starttime
                            LOGFILE.write("\n\t>>> PROCESS TOOK %f SECONDS <<<" % time_taken)
                            LOGFILE.flush()
                            os.chdir(original_dir)
            #check TIMER against SRC_TTL, STR_TTL_SEEDED, STR_TTL_UNSEEDED
            toremove = []
            TIMER.flush()
            for id, flags in TIMER.CURRENT.iteritems():
                timealive = time.time() - flags[1]
                protocol = flags[0]
                if protocol == "SRC":
                    if timealive > SRC_TTL:
                        try:
                            name = RT.getNameByID(id)
                            LOGFILE.write("\nid: %s (name: %s) has lived too long, attepting to kill" % (id, name))
                            LOGFILE.flush()
                            RT.remove(id)
                            try:
                                shutil.rmtree("%s/%s" % (FILE_DESTINATION, name))
                            except OSError:
                                os.remove("%s/%s" % (FILE_DESTINATION, name))
                            toremove += [id]
                            LOGFILE.write("\nname: %s has been deleted" % name)
                            LOGFILE.flush()
                        except:
                            tb = traceback.format_exc()
                            toremove += [id]
                            LOGFILE.write("\n" + tb)
                            LOGFILE.flush()
                            ERROR.write("\n" + tb)
                            ERROR.flush()       
                elif protocol == "STR":
                    #get torrent ratio
                    try:
                        ratio = RT.getRatio(id)
                        if ratio > 1000:
                            #SEEDED
                            if timealive > STR_TTL_SEEDED:
                                try:
                                    name = RT.getNameByID(id)
                                    LOGFILE.write("\nid: %s (name: %s) has lived too long, attepting to kill" % (id, name))
                                    LOGFILE.flush()
                                    RT.remove(id)
                                    os.remove("%s/%s" % (FILE_DESTINATION, name))
                                    toremove += [id]
                                    LOGFILE.write("\nname: %s has been deleted" % name)
                                    LOGFILE.flush()
                                except:
                                    tb = traceback.format_exc()
                                    toremove += [id]
                                    LOGFILE.write("\n" + tb)
                                    LOGFILE.flush()
                                    ERROR.write("\n" + tb)
                                    ERROR.flush()     
                        else:
                            #UNSEEDED
                            if timealive > STR_TTL_UNSEEDED:
                                try:
                                    name = RT.getNameByID(id)
                                    LOGFILE.write("\nid: %s (name: %s) has lived too long, attepting to kill" % (id, name))
                                    LOGFILE.flush()
                                    RT.remove(id)
                                    os.remove("%s/%s" % (FILE_DESTINATION, name))
                                    toremove += [id]
                                    LOGFILE.write("\nname: %s has been deleted" % name)
                                    LOGFILE.flush()
                                except:
                                    tb = traceback.format_exc()
                                    toremove += [id]
                                    LOGFILE.write("\n" + tb)
                                    LOGFILE.flush()
                                    ERROR.write("\n" + tb)
                                    ERROR.flush()     
    
                    except:
                        tb = traceback.format_exc()
                        toremove += [id]
                        LOGFILE.write("\n" + tb)
                        LOGFILE.flush()
                        ERROR.write("\n" + tb)
                        ERROR.flush()     
    
                                
            for i in toremove:
                response = TIMER.remove_torrent(i)
                if not response:
                    LOGFILE.write("\nCouldn't remove %s, not in .timer" % i)
                    LOGFILE.flush()
            try:
                TIMER.flush()
            except:
                tb = traceback.format_exc()
                LOGFILE.write("\n%s" % tb)
                LOGFILE.flush()
            
                                        
            time.sleep(5)
            
    except:
        tb = traceback.format_exc()
        if "KeyboardInterrupt" in tb:
            try:
                LOGFILE.close()
                ERROR.close()
                QUEUE.close()
            except:
                pass
            finally:
                print "Caught shutdown signal"
                sys.exit()
        else:
            try:
                ERROR.write("\n%s" % tb)
                ERROR.flush()
            except:
                print tb
            try:
                LOGFILE.close()
                ERROR.close()
                QUEUE.close()
            except:
                pass
            finally:
                print "Unhandled error"
                sys.exit()
                
def process(path):
    #unrar
    #make torrent of path + .avi or .mkv
    #upload torrent
    #move file into main downloading folder
    #move torrent file into watch dir
    
    #get info for path
    cookiejar = cookielib.CookieJar()
    STR = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar), MultipartPostHandler.MultipartPostHandler)
    sysname, nodename, release, version, machine = os.uname()
    pythonversion = sys.version.split(" \n")[0].split(",")[0] + ")"
    STR.addheaders=[("User-agent", "StrAuto %s (%s %s) Python %s" % (VERSION, sysname, machine, pythonversion))]
    STR.open("http://sharetheremote.org/login.php")
    time.sleep(1)
    STR.open("http://sharetheremote.org/login.php", urllib.urlencode({"username":USERNAME, "password":PASSWORD, "login":"Log+In!"}))
    LOGFILE.write("\n\tLogged in (dupecheck 1)")
    LOGFILE.flush()
    
    ## USE upload.php?auto_fill for this
    for show in SHOW_IDS:
        if re.compile(show[0], re.I).match(os.path.basename(path)):
            show_id = show[1]
            LOGFILE.write("\n\tGot show_id %s (dupecheck 1)" % show_id)
            LOGFILE.flush()
            
    LOGFILE.write("\n\tGetting info from http://sharetheremote.org/upload.php?action=auto_fill&name=%s" % os.path.basename(path))
    LOGFILE.flush()
    
    json_info = STR.open("http://sharetheremote.org/upload.php?action=auto_fill&name=%s" % os.path.basename(path)).read()
    jsonObject = json.loads(json_info)
    LOGFILE.write("\n\t***DEBUG***\n\t%s\n\t***END DEBUG***" % json_info)
    LOGFILE.flush()
    if "confirm" not in jsonObject.keys():
        LOGFILE.write("\n\tJson information not confirmed, cancelling upload")
        LOGFILE.flush()
    episode = str(jsonObject["info"]["attr"][1])
    season = str(jsonObject["info"]["attr"][0])
    tor_res = jsonObject["info"]["res"]
    if tor_res == "":
        tor_res = "SD"
    try:
        subgroup_id = jsonObject["confirm"][0]["SubGroupID"]
        LOGFILE.write("\n\tGot season, episode, tor_res, subgroup_id: %s, %s, %s, %s (dupecheck 1)" % (season, episode, tor_res, subgroup_id))
        LOGFILE.flush()
    except IndexError:
        LOGFILE.write("\n\tCouldn't get JSON information, cancelling upload")
        LOGFILE.flush()
        STOP = True
    else:
        STOP = dupe_check(STR, subgroup_id, season, episode, tor_res)

    if STOP == False:
        result_unrar = unrar(path)
        ##########TESTING################
        #os.chdir("/home/hd1/mountainpenguin/torrents/downloading")
        #result_unrar = os.path.basename(path)
        #################################
        if result_unrar != None:
            result_mktorrent = mktorrent(path, result_unrar)
            if result_mktorrent != None:
                response = upload(path, result_mktorrent)
                if response == "OK":
                    LOGFILE.write("\n\tSleeping to wait for rtorrent to add torrent")
                    LOGFILE.flush()
                    time.sleep(10)
                    try:
                        torrent_id = RT.getIDByName(result_unrar)
                        LOGFILE.write("\n\tGot torrent_id for STR: %s" % torrent_id)
                        LOGFILE.flush()
                        TIMER.add_torrent(torrent_id, "STR", time.time())
                        TIMER.flush()
                    except:
                        LOGFILE.write("\n" + traceback.format_exc())
                        LOGFILE.flush()
    
def unrar(path):
    print "Unrar-ing"
    LOGFILE.write("\n\tStarting to unrar: ")
    LOGFILE.flush()
    os.chdir(path)
    output = None
    all_files = os.listdir(".")
    if os.path.basename(path) + ".rar" in all_files:
        LOGFILE.write(os.path.basename(path) + ".rar")
        LOGFILE.flush()
        p = subprocess.Popen(["unrar", "e", "%s" % os.path.basename(path) + ".rar"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p.communicate()
        if output[1] != "":
            print "There was an error whist unraring"
            print output[1]
            LOGFILE.write("\n\tError whilst extracting:\n************************\n")
            LOGFILE.write(output[1])
            LOGFILE.write("\n************************")
            LOGFILE.flush()
            return None
        base_path = os.path.basename(path)
    elif os.path.basename(path).lower() + ".rar" in all_files:
        LOGFILE.write(os.path.basename(path).lower() + ".rar")
        LOGFILE.flush()
        p = subprocess.Popen(["unrar", "e", "%s" % (os.path.basename(path).lower() + ".rar")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p.communicate()
        
        if output[1] != "":
            print "There was an error whist unraring"
            print output[1]
            LOGFILE.write("\n\tError whilst extracting:\n************************\n")
            LOGFILE.write(output[1])
            LOGFILE.write("\n************************")
            LOGFILE.flush()
            return None
        base_path = os.path.basename(path).lower()
    else:
        #check for part01 / r00 / .001
        for file in all_files:
            if "part01" in file:
                LOGFILE.write(file)
                LOGFILE.flush()
                p = subprocess.Popen(["unrar", "e", file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output = p.communicate()
                if output[1] != "":
                    print "There was an error whist unraring"
                    print output[1]
                    LOGFILE.write("\n\tError whilst extracting:\n************************\n")
                    LOGFILE.write(output[1])
                    LOGFILE.write("\n************************")
                    LOGFILE.flush()
                    return None
            elif ".r00" in file:
                LOGFILE.write(file)
                LOGFILE.flush()
                p = subprocess.Popen(["unrar", "e", file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output = p.communicate()
                if output[1] != "":
                    print "There was an error whist unraring"
                    print output[1]
                    LOGFILE.write("\n\tError whilst extracting:\n************************\n")
                    LOGFILE.write(output[1])
                    LOGFILE.write("\n************************")
                    LOGFILE.flush()
                    return None
            elif ".001" in file:
                LOGFILE.write(file)
                LOGFILE.flush()
                p = subprocess.Popen(["unrar", "e", file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output = p.communicate()
                if output[1] != "":
                    print "There was an error whist unraring"
                    LOGFILE.write("\n\tError whilst extracting:\n************************\n")
                    LOGFILE.write(output[1])
                    LOGFILE.write("\n************************")
                    LOGFILE.flush()
                    print output[1]
                    return None
            else:
                pass

        if output == None:
            LOGFILE.write("\n\tCouldn't find a suitable RAR archive")
            LOGFILE.flush()
            print "Can't find .rar archive"
            return None
        
        elif "already exists" in output[0]:
            LOGFILE.write("\n\tRAR already extracted, continuing")
            LOGFILE.flush()
            print "RAR already extracted, continuing"
            output = "CONTINUE"
        
    if "All OK" in output[0] or output == "CONTINUE":
        print "Unraring successful"
        LOGFILE.write("\n\tUn-RAR successful")
        LOGFILE.flush()
        #Extracting from cops.s22e24.hdtv.xvid-2hd.rar\n\nExtracting  cops.s22e24.hdtv.xvid-2hd.avi
        avi = glob.glob("*.avi")
        mkv = glob.glob("*.mkv")
        if len(avi) > 0:
            for i in avi:
                if "sample" not in i.lower():
                    LOGFILE.write("\n\tDetected file: %s, renaming to %s" % (i, os.path.basename(path) + ".avi"))
                    LOGFILE.flush()
                    os.rename(i, os.path.basename(path) + ".avi")
                    return os.path.basename(path) + ".avi"
        if len(mkv) > 0:
            for i in mkv:
                if "sample" not in i.lower():
                    LOGFILE.write("\n\tDetected file: %s, renaming to %s" % (i, os.path.basename(path) + ".mkv"))
                    LOGFILE.flush()
                    os.rename(i, os.path.basename(path) + ".mkv")
                    return os.path.basename(path) + ".mkv"
        else:
            print "Couldn't find any .avi or .mkv files"
            LOGFILE.write("\n\tCouldn't find any .avi or .mkv files")
            LOGFILE.flush()
        
def mktorrent(path, file):
    if os.path.exists(file):
        print "Creating torrent"
        LOGFILE.write("\n\tCreating torrent")
        LOGFILE.flush()
        p = subprocess.Popen(["mktorrent", "-a", ANNOUNCE_URL, "-p", "-o", path + ".torrent", file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p.communicate()
        print "Moving .avi file to %s" % FILE_DESTINATION
        LOGFILE.write("\n\tMoving %s to %s" % (file, FILE_DESTINATION))
        LOGFILE.flush()
        os.rename(file, "%s/%s" % (FILE_DESTINATION, file))
        if output[1] != "":
            print "There was an error whilst creating the torrent"
            print output[1]
            LOGFILE.write("\n\tThe was an error whilst creating the torrent:\n************************\n")
            LOGFILE.write(output[1])
            LOGFILE.write("\n************************")
            LOGFILE.flush()
        else:
            LOGFILE.write("\n\tTorrent created successfully: %s" % path + ".torrent")
            LOGFILE.flush()
            return path + ".torrent"
    else:
        print "Path doesn't exist"


def dupe_check(STR, subgroup_id, season, episode, tor_res):
    STOP = False
    if subgroup_id == None:
        return False
    else:
        subgroup_html = STR.open("https://ssl.sharetheremote.org/torrents.php?subgroupid=%s" % subgroup_id).read()
        inrange_html = subgroup_html.split("<td width=\"80%\"><strong>Torrents</strong></td>")[1].split("<table id=\"crew\">")[0]
        if tor_res == "SD":
            check = "<strong>Standard Definition</strong></td>"
        elif tor_res == "720p":
            check = "<strong>High Definition - 720p</strong></td>"
        elif tor_res == "1080p":
            check = "<strong>High Definition - 1080p</strong></td>"
        elif tor_res == "1080i":
            check = "<strong>High Definition - 1080i</strong></td>"
        else:
            return True
        
        if check in inrange_html:
            return True
        else:
            return False
        
def upload(path, torrent):
    print "Uploading torrent"
    if os.path.exists(os.path.basename(torrent)):
        torrent = os.path.basename(torrent)
    else:
        os.chdir(os.path.dirname(torrent))
        if os.path.exists(os.path.basename(torrent)):
           torrent = os.path.basename(torrent)       
    cookiejar = cookielib.CookieJar()
    STR = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar), MultipartPostHandler.MultipartPostHandler)
    sysname, nodename, release, version, machine = os.uname()
    pythonversion = sys.version.split(" \n")[0].split(",")[0] + ")"
    STR.addheaders=[("User-agent", "StrAuto %s (%s %s) Python %s" % (VERSION, sysname, machine, pythonversion))]
    STR.open("http://sharetheremote.org/login.php")
    time.sleep(1)
    STR.open("http://sharetheremote.org/login.php", urllib.urlencode({"username":USERNAME, "password":PASSWORD, "login":"Log+In!"}))
    
    #work out upload data
    for show in SHOW_IDS:
        if re.compile(show[0], re.I).match(os.path.basename(path)):
            show_id = show[1]
            imdb_id_backup = show[2]
            LOGFILE.write("\n\tGot show_id: %s" % show_id)
            LOGFILE.flush()
            
    try:
        json_autofill = STR.open("http://sharetheremote.org/upload.php?action=auto_fill&name=%s" % os.path.basename(path)).read()
        
        #show, year, tags, image, show_desc
        
#        <input type="text" id="title" name="show" size="60" 
#value="Anthony Bourdain: No Reservations"  />
        try:
            jsonObject = json.loads(json_autofill)
            
            #{"info":
            #    {"type":0,
            #     "attr":[4,2],
            #        "source":"HDTV",
            #        "res":"720p",
            #        "codec":"X264",
            #        "scene":"DIMENSION",
            #        "name":"Gossip Girl"
            #    },"confirm":[
            #        {"IMDbSearch":"\"Gossip Girl\" (2007)",
            #         "ShowIMDb":"0397442",
            #         "SubGroupIMDb":null,
            #         "Name":"Gossip Girl",
            #         "ShowID":"299",
            #         "Image":"http:\/\/ptpimg.me\/5n9m8m.png",
            #         "body":null,
            #         "GroupID":"661",
            #         "Year":"2007",
            #         "SubGroupID":null,
            #         "Title":null}]
            #}
            
            info = jsonObject["info"]
            confirm = jsonObject["confirm"][0]
            
            LOGFILE.write("\n\tChecking show_id is correct")
            LOGFILE.flush()
            showidcheck = confirm["ShowID"]
            if showidcheck == show_id:
                STOP = False
            else:
                LOGFILE.write("\n\tGot show_id: %s which doesn't match with expected value: %s, aborting" % (showidcheck, show_id))
                LOGFILE.flush()
                STOP = True
            if not STOP:
                show = info["name"]
                #show = showre.findall(html)[0]
                LOGFILE.write("\n\tGot show name: %s" % show)
                year = confirm["Year"]
                if year:
                #year = yearre.findall(html)[0]
                    LOGFILE.write("\n\tGot year: %s" % year)
                else:
                    year = str(time.localtime().tm_year)
                    LOGFILE.write("\n\tNo year, using: %s" % year)
                #tags = tagsre.findall(html)[0]
                #LOGFILE.write("\n\tGot tags: %s" % tags)
                image = confirm["Image"]
                #image = imagere.findall(html)[0]
                LOGFILE.write("\n\tGot image url: %s" % image)
                #show_desc = show_descre.findall(html)[0]
                #LOGFILE.write("\n\tGot show_desc")
                #LOGFILE.flush()
                tor_res = info["res"]
                if tor_res == "":
                    tor_res = "SD"
                LOGFILE.write("\n\tGot tor_res: %s" % tor_res)
                format = info["codec"]
                LOGFILE.write("\n\tGot format: %s" % format)
                media = info["source"]
                LOGFILE.write("\n\tGot media: %s" % media)
                
                LOGFILE.flush()
                
                imdb_id = confirm["ShowIMDb"]
                if imdb_id == None:
                    imdb_id = imdb_id_backup
                LOGFILE.write("\n\tGot imdb_id: %s" % imdb_id)
                
                season = str(info["attr"][0])
                episode = str(info["attr"][1])
                LOGFILE.write("\n\tGot season, episode: %s, %s" % (season, episode))
                group_id = confirm["GroupID"]
                LOGFILE.write("\n\tGot group_id: %s" % group_id)
                subgroup_id = confirm["SubGroupID"]
                LOGFILE.write("\n\tGot subgroup_id: %s" % subgroup_id)
                
                LOGFILE.flush()
                
                
                
                
                LOGFILE.write("\n\tDupe Checking")
                LOGFILE.flush()
                
                STOP = dupe_check(STR, subgroup_id, season, episode, tor_res)
    
                if STOP == False:
                    #show_name.SxxEyy.???.media.format-scene_group
    
                    #http://sharetheremote.org/upload.php?action=imdb_get&imdbid=0397442&type=show&&season=4&episode=1
                    LOGFILE.write("\n\tGetting episode title from http://sharetheremote.org/upload.php?action=imdb_get&imdbid=%s&type=show&&season=%s&episode=%s" % (imdb_id, season, episode))
                    LOGFILE.flush()
                    jsonResponse = STR.open("http://sharetheremote.org/upload.php?action=imdb_get&imdbid=%s&type=show&&season=%s&episode=%s" % (imdb_id, season, episode)).read()
                    try:
                        jsonObject = json.loads(jsonResponse)
                    #{"SubGroupIMDb":"1635985","plot":"","title":"Belles de Jour","show":"Gossip Girl"}
                        ep_info = jsonObject["plot"]
                        ep_title = jsonObject["title"]
                        if ep_title == "":
                            ep_title = "Episode %s" % episode
                    except ValueError:
                        ep_info = ""
                        ep_title = "Episode %s" % episode

                    attempt = False
                    if attempt == False:
                        LOGFILE.write("\n\tGetting pre_time: attempting main page (pre.scenedb.org)")
                        LOGFILE.flush()
                        prescene_url = "http://pre.scenedb.org/"
                        prescenere = re.compile("\<tr\>\<td\>(\d+-\d+-\d+ \d+:\d+)\<\/td\>\<td class=.*?title=\"%s\"\>%s\<\/a\>\<\/td\>" % (os.path.basename(path), os.path.basename(path)))
                        
                        try:
                            prescene_response = urllib2.urlopen(prescene_url,timeout=10).read().replace("</tr>","</tr>\n")
                        except urllib2.URLError:
                            LOGFILE.write("\n\tGot timeout from pre.scenedb.org")
                            LOGFILE.flush()
                            attempt = False
                        else:
                            try:
                                pre_time = prescenere.findall(prescene_response)[0]
                                LOGFILE.write("\n\tGot pre_time: %s" % pre_time)
                                LOGFILE.write("\n\tFormatting pre_time")
                                LOGFILE.flush()
                                #convert to standard format
                                #prescene is +5 to dup3.me
                                pre_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(calendar.timegm(time.strptime(pre_time, "%d-%m-%y %H:%M")) - (60*60)))
                                LOGFILE.write("\n\tFormatted pre_time to: %s" % pre_time)
                                LOGFILE.flush()
                                attempt = True
                            except IndexError:
                                attempt = False
                                
                            if attempt == False:
                                LOGFILE.write("\n\tGetting pre_time: main page failed")
                                prescene_url2 = "http://pre.scenedb.org/?preq=%s" % os.path.basename(path)
                                LOGFILE.write("\n\tGetting pre_time: attempting search")
                                LOGFILE.flush()
                                
                                prescene_response = urllib2.urlopen(prescene_url2).read()
                                try:
                                    pre_time = prescenere.findall(prescene_response)[0]
                                    LOGFILE.write("\n\tGot pre_time: %s" % pre_time)
                                    LOGFILE.write("\n\tFormatting pre_time")
                                    LOGFILE.flush()
                                    #convert to standard format
                                    pre_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(calendar.timegm(time.strptime(pre_time, "%d-%m-%y %H:%M")) - (60*60)))
                                    LOGFILE.write("\n\tFormatted pre_time to: %s" % pre_time)
                                    LOGFILE.flush()
                                    attempt = True
                                except IndexError:
                                    LOGFILE.write("\n\tGetting pre_time: Search failed")
                                    LOGFILE.flush()
                                    attempt = False
                                    
                                
                    if attempt == False:
                        LOGFILE.write("\n\tGetting pre_time: attempting main page (dup3.me)")
                        LOGFILE.flush()
                        dup_url = "http://dup3.me"
                        #2010-08-10 09:40:24 <img width="10px" height="10px" title="NUKELESS" border="0" src="http://pic.leech.it/i/b16ec/278f049lwq43.png" alt="NONUKESTATUS" /> <a class="fis" href="#"><img width="10px" height="10px" border="0" src="http://pic.leech.it/i/386bd/348de322ps0tt.png" alt="File Count: 82 files | File size: 3772.0 MB" /><span>File Count: 82 files | File size: 3772.0 MB</span></a> <img width="10px" height="10px" title="NO VIDEO INFO" alt="NOVIDEOINFO" border="0" src="http://pic.leech.it/i/89ebd/717ec658rdvav.png" /> <img width="10px" height="10px" title="NO MP3 INFO" alt="NOAUDIOINFO" border="0" src="http://pic.leech.it/i/e00a9/87f4eb2stqgy.png" /> <img width="10px" height="10px" title="NO NFO" alt="NONFO" border="0" src="http://pic.leech.it/i/c3d71/0325a7a8dfxut.png" /> <img width="10px" height="10px" title="NO SFV" alt="NOSFV" border="0" src="http://pic.leech.it/i/944fb/b2a2aca1uqn9s.png" /> <img width="10px" height="10px" title="NO M3U" alt="NOM3U" border="0" src="http://pic.leech.it/i/2681c/fb3094dsotis.png" /> <a id="nostyle" href="?cat=DVDR">DVDR   </a> Happy.Family.2010.iTALiAN.COMPLETE.PAL.DVDR-<a id="nostyle" href="?group=BBZ&cat=DVDR">BBZ</a>
                        dupre = re.compile("(\d+-\d+-\d+ \d+:\d+:\d+) \<img width=\"10px\" height=\"10px\" title=.*? border=.*? src=\"http:.*? alt=\".*? \/\> .*? %s\<a id=\"nostyle\" href=\"\?group=%s&cat=.*?\"\>%s\<\/a\>" % (os.path.basename(path).split("-")[0] + "-", os.path.basename(path).split("-")[1], os.path.basename(path).split("-")[1]))
                        #dupre = re.compile("(\d+-\d+-\d+ \d+:\d+:\d+) \<img width=\"10px\" height=\"10px\" title=.*? border=.*? src=\"http:.*? alt=\".*? \/\> .*? %s\<a id=\"nostyle\" href=\"?group=" % (os.path.basename(path).split("-")[0] + "-"))
                        try:
                            dup_response = urllib2.urlopen(dup_url,timeout=10).read()
                        except urllib2.URLError:
                            LOGFILE.write("\n\tGot timeout from dup3.me")
                            LOGFILE.flush()
                            attempt = False
                        else:
                            try:
                                pre_time = dupre.findall(dup_response)[0]
                                LOGFILE.write("\n\tGot pre_time: %s" % pre_time)
                                LOGFILE.flush()
                                attempt = True
                            except IndexError:
                                attempt = False
                                
                            if attempt == False:
                                LOGFILE.write("\n\tGetting pre_time: main page failed")
                                dup_url2 = "http://dup3.me/index.php?s=%s&cat=" % os.path.basename(path)
                                LOGFILE.write("\n\tGetting pre_time: attempting search")
                                LOGFILE.flush()
                            #2010-08-10 09:40:24 <img width="10px" height="10px" title="NUKELESS" border="0" src="http://pic.leech.it/i/b16ec/278f049lwq43.png" alt="NONUKESTATUS" /> <a class="fis" href="#"><img width="10px" height="10px" border="0" src="http://pic.leech.it/i/386bd/348de322ps0tt.png" alt="File Count: 82 files | File size: 3772.0 MB" /><span>File Count: 82 files | File size: 3772.0 MB</span></a> <img width="10px" height="10px" title="NO VIDEO INFO" alt="NOVIDEOINFO" border="0" src="http://pic.leech.it/i/89ebd/717ec658rdvav.png" /> <img width="10px" height="10px" title="NO MP3 INFO" alt="NOAUDIOINFO" border="0" src="http://pic.leech.it/i/e00a9/87f4eb2stqgy.png" /> <img width="10px" height="10px" title="NO NFO" alt="NONFO" border="0" src="http://pic.leech.it/i/c3d71/0325a7a8dfxut.png" /> <img width="10px" height="10px" title="NO SFV" alt="NOSFV" border="0" src="http://pic.leech.it/i/944fb/b2a2aca1uqn9s.png" /> <img width="10px" height="10px" title="NO M3U" alt="NOM3U" border="0" src="http://pic.leech.it/i/2681c/fb3094dsotis.png" /> <a id="nostyle" href="?cat=DVDR">DVDR   </a> Happy.Family.2010.iTALiAN.COMPLETE.PAL.DVDR-<a id="nostyle" href="?group=BBZ&cat=DVDR">BBZ</a> 
                                dup_response = urllib2.urlopen(dup_url2).read()
                                try:
                                    pre_time = dupre.findall(dup_response)[0]
                                    LOGFILE.write("\n\tGot pre_time: %s" % pre_time)
                                    LOGFILE.flush()
                                    attempt = True
                                except IndexError:
                                    LOGFILE.write("\n\tGetting pre_time: Search failed")
                                    LOGFILE.flush()
                                    attempt = False
                                    
                    if attempt == False:
                        orly_url = "http://orlydb.com"
                        orlyre = re.compile("\<span class=\"timestamp\"\>(\d+-\d+-\d+ \d+:\d+:\d+)\<\/span\>\n.*?\<span class=\"section\"\>.*?\n.*?\<span class=\"release\"\>%s\<\/span\>" % os.path.basename(path), re.DOTALL | re.I)
                        
                        LOGFILE.write("\n\tGetting pre_time: attempting main page (orlydb.com)")
                        LOGFILE.flush()
                        try:
                            orlyresponse = urllib2.urlopen(orly_url,timeout=10).read()
                        except urllib2.URLError:
                            LOGFILE.write("\n\tGot timeout from orlydb.com")
                            LOGFILE.flush()
                            attempt = False
                        else:
                            responses = orlyresponse.split("<div>")
                            attempt = False
                            for response in responses:
                                try:
                                    pre_time = orlyre.findall(response)[0]
                                    LOGFILE.write("\n\tGot pre_time: %s" % pre_time)
                                    LOGFILE.flush()
                                    attempt = True
                                except IndexError:
                                    pass
                        
                            if attempt == False:
                                attempt = False
                                LOGFILE.write("\n\tGetting pre_time: main page failed")
                                orly_url2 = "http://orlydb.com/?q=%s" % os.path.basename(path).replace("-","%20")
                                LOGFILE.write("\n\tDEBUG: %s" % orly_url2)
                                LOGFILE.flush()
                                orlyre2 = re.compile("\<span class=\"timestamp\"\>(\d+-\d+-\d+ \d+:\d+:\d+)\<\/span\>.*?\<span class=\"section\"\>.*?\<span class=\"release\"\>(.*?)\<\/span\>", re.DOTALL | re.I)
                        
                                LOGFILE.write("\n\tGetting pre_time: attempting search")
                                LOGFILE.flush()
                                orlyresponse = urllib2.urlopen(orly_url2).read()
                                try:
                                    pretimeres = orlyre2.findall(orlyresponse)[0]
                                    if pretimeres[1] == os.path.basename(path):
                                        pre_time = pretimeres[0]
                                        #2010-04-04 07:29:02
                                        LOGFILE.write("\n\tGot pre_time: %s" % pre_time)
                                        LOGFILE.flush()
                                        attempt = True
                                except IndexError:
                                    LOGFILE.write("\n\tGetting pre_time: Search failed")
                                    LOGFILE.flush()
                                    
                    if attempt == False:
                        release_desc = "Autouploaded by StRAuto v%s\nFilename: %s" % (VERSION, os.path.basename(path))
                        LOGFILE.write("\n\tCouldn't get pre_time")
                        LOGFILE.flush()
                    
                    elif attempt == True:
                        pre_time_time = calendar.timegm(time.strptime(pre_time, "%Y-%m-%d %H:%M:%S"))
                        current_time = time.time()
                        seconds = current_time - pre_time_time
                        time_diff = ""
                        if seconds < 0:
                            time_diff = "Less than 1 minute"
                        else:
                            if seconds > 604800:
                                weeks = int(seconds / 604800)
                                time_diff += "%i weeks, " % weeks
                                seconds = seconds - (weeks * 604800)
                            if seconds > 86400:
                                days = int(seconds / 86400)
                                time_diff += "%i days, " % days
                                seconds = seconds - (days * 86400)
                            if seconds > 3600:
                                hours = int(seconds / 3600)
                                time_diff += "%i hours, " % hours
                                seconds = seconds - (hours * 3600)
                            if seconds > 60:
                                minutes = int(seconds / 60)
                                time_diff += "%i minutes, " % minutes
                                seconds = seconds - (minutes * 60)
                            time_diff += "%i seconds" % seconds
                        LOGFILE.write("\n\tCalculated time_diff: %s" % time_diff)
                        LOGFILE.flush()
                    
                        release_desc = "Autouploaded by StRAuto v%s\nFilename: %s\nUploaded %s after pre" % (VERSION, os.path.basename(path), time_diff)
    
            #<div>
            #    <span class="timestamp">2010-03-29 03:21:15</span>
            #
            #    <span class="section"><a href="/s/tv-xvid">TV-XVID</a></span>
            #    <span class="release">The.Pacific.Pt.III.HDTV.XviD-NoTV</span>
            #</div>
    
                     
                    #show, ep_title, year, season, episode, scene_group, format, resolution, resolution_options, media, tags, image, show_desc, release_desc
                    print "torrent:", torrent
                    
                    LOGFILE.write("\n\tDupe Checking Again")
                    LOGFILE.flush()
                    
                    STOP = dupe_check(STR, subgroup_id, season, episode, tor_res)
                        
                    if STOP == False:
                        
                        #get auth
                        upload_html = STR.open("http://sharetheremote.org/upload.php").read()
                        auth = re.findall("\<input type=\"hidden\" name=\"auth\" value=\"(.*?)\" \/\>", upload_html)[0]
                        
                        post_data = {
                            "submit":"true",
                            "auth":auth,
                            "file_input":open(torrent, "rb"),
                            "category":"Season",
                            "releasetype":"Episode",
                            "show":show,
                            "season":season,
                            "episode":episode,
                            "scene":"on",
                            "title":ep_title,
                            "year":year,
                            "format":format,
                            "resolution":tor_res,
                            "media":media,
                            "image":image,
                            "subgroup_desc":ep_info,
                            "torrent_desc":release_desc,
                        }
                                                
                        LOGFILE.write("\n\t*** DEBUG ***\n\tpost_data : %s\n\t*** END DEBUG***" % repr(post_data))
                        LOGFILE.flush()
                        """
                        {
                        'category': 'Season', 
                        'media': 'HDTV',
                        'episode': '2',
                        'show': 'Supernatural',
                        'subgroup_desc': 'Sam investigates a case about missing babies whose parents are being murdered. At one of the crime scenes...',
                        'file_input': <open file 'Supernatural.S06E02.HDTV.XviD-2HD.torrent', mode 'rb' at 0xeb0a150>,
                        'format': 'XviD',
                        'title': 'Two and a Half Men',
                        'releasetype': 'Episode',
                        'scene': 'on',
                        'submit': 'true',
                        'auth': '350f91c88212f8df3323855070f45766',
                        'torrent_desc': 'Autouploaded by StRAuto v0.40.0\nFilename: Supernatural.S06E02.HDTV.XviD-2HD\nUploaded 7 hours, 52 minutes, 55 seconds after pre',
                        'season': '6',
                        'year': None,
                        'resolution': 'SD',
                        'image': 'http://i43.tinypic.com/i38kfb.jpg'}
                        """
                        url = "http://sharetheremote.org/upload.php"
                    
                        ###############DEBUGGING##################
                        response = STR.open(url, post_data)
                        html = response.read()
                        #html = "test"
                        ##########################################
                        
                        errorre = re.compile("\<p style=\"color: red;text-align:center;\"\>(.*?)\<\/p\>")
                        try:
                            errorcheck = errorre.findall(html)[0]
                            print "Error uploading: %s" % errorcheck
                            LOGFILE.write("\n\tError uploading:\n************************\n")
                            LOGFILE.write(errorcheck)
                            LOGFILE.write("\n" + repr(post_data))
                            LOGFILE.write("\n************************")
                            LOGFILE.flush()
                        except IndexError:
                            print "Uploaded successfully"
                            LOGFILE.write("\n\tUploaded successfully")
                            LOGFILE.flush()
                            print "Moving %s file to %s" % (torrent, TORRENT_DESTINATION)
                            os.rename(torrent, "%s/%s" % (TORRENT_DESTINATION, torrent))
                            LOGFILE.write("\n\tMoving %s to %s" % (torrent, TORRENT_DESTINATION))
                            LOGFILE.flush()
                            return "OK"
                        
                    else:
                        LOGFILE.write("\n\tDupe found, stopping upload")
                        LOGFILE.flush()

        except (IndexError,TypeError):
            print "Show information couldn't be found"
            tb = traceback.format_exc()
            LOGFILE.write("\n\tShow information couldn't be found")
            LOGFILE.write("\n\t%s" % tb)
            LOGFILE.flush()
            ERROR.write("\n" + tb)
            ERROR.flush()
            
    except NameError:
        print "Show couldn't be found"
        tb = traceback.format_exc()
        LOGFILE.write("\n\tShow couldn't be found")
        LOGFILE.write("\n\t%s" % tb)
        LOGFILE.flush()
        ERROR.write("\n" + tb)
        ERROR.flush()

        
if __name__ == "__main__":
    main()
