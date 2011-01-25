#!/usr/bin/env python

import json

class JSONtimer:
    def __init__(self):
        self.CURRENT = self._get_current()
    
    def _get_current(self):
        try:
            content = open(".timer.json").read()
        except IOError:
            return {}
        else:
            jsonObject = json.loads(content)
            return jsonObject
    
    def add_torrent(self, torrentid, type, time):
        self.CURRENT[torrentid] = [type, time]
        return True
    
    def remove_torrent(self, torrentid):
        if torrentid in self.CURRENT.keys():
            del self.CURRENT[torrentid]
            return True
        else:
            return False
    
    def flush(self):
        jsonObject = json.dumps(self.CURRENT)
        open(".timer.json","w").write(jsonObject)
        
