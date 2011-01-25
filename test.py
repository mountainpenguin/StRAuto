# try to get pretime

path = "/home/torrent/torrents/downloading/%s" % raw_input("Search: ")
import urllib2, re, time, sys, os, calendar
LOGFILE = sys.stdout
VERSION = "pretime testing"
air_date = "None"

attempt = False
if attempt == False:
    LOGFILE.write("\n\tGetting pre_time: attempting main page (pre.scenedb.org)")
    LOGFILE.flush()
    prescene_url = "http://pre.scenedb.org/"
    prescenere = re.compile("\<tr\>\<td\>(\d+-\d+-\d+ \d+:\d+)\<\/td\>\<td class=.*?title=\"%s\"\>%s\<\/a\>\<\/td\>" % (os.path.basename(path), os.path.basename(path)))
    
    try:
        prescene_response = urllib2.urlopen(prescene_url,timeout=10).read()
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
            orly_url2 = "http://orlydb.com/?q=%s" % os.path.basename(path)
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
    release_desc = "Autouploaded by StRAuto v%s\nFilename: %s\nAir Date: %s" % (VERSION, os.path.basename(path), air_date)
    LOGFILE.write("\n\tCouldn't get pre_time")
    LOGFILE.flush()

elif attempt == True:
    pre_time_time = calendar.timegm(time.strptime(pre_time, "%Y-%m-%d %H:%M:%S"))
    current_time = time.time()
    seconds = current_time - pre_time_time
    time_diff = ""
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

    release_desc = "Autouploaded by StRAuto v%s\nFilename: %s\nAir Date: %s\nUploaded %s after pre" % (VERSION, os.path.basename(path), air_date, time_diff)
