
from model import *

import urllib2 as urllib
import re

class Symbol():

    def __init__(self):
        self.symboldb = SymbolDB()

    def _add_module(self, m):
        try:
            new_module = Module(os=m.group(1), arch=m.group(2), hexid=m.group(3), name=m.group(4))
            self.symboldb.session.add(new_module)
            self.symboldb.session.commit()
        except:
            return None

        return(new_module.id)

    def _add_file(self, m, mod_id):
        try:
            new = File(number=m.group(1), name=m.group(2), module=mod_id)
            self.symboldb.session.add(new)
            self.symboldb.session.commit()
        except:
            return None

        return(new.id)


    def add(self, url):

    def add(self, url):
        page = urllib.urlopen(url)
        symbols = page.read().split('\n')
        page.close()

        # pull out the module
        for line in symbols:
            # MODULE windows x86 E40644FDC4D040749962D4C8EB8DF3212 firefox.pdb
            m = re.search('^MODULE (\S+) (\S+) (\S+) (\S+)', line)
            if m:
                mod_id = self._add_module(m)
                next
            m = re.search('^FILE (\S+) (\S+)', line)
            if m:
                file_id = self._add_file(m, mod_id)

if __name__ == "__main__":
    test = Symbol()
    url = 'http://symbols.mozilla.org/firefox/firefox.pdb/E40644FDC4D040749962D4C8EB8DF3212/firefox.sym'
    test.add(url)
