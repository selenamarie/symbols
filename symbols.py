
from model import *

import urllib2 as urllib
import re

class Symbol():

    def __init__(self):
        self.symboldb = SymbolDB()

    def add(self, url):
        page = urllib.urlopen(url)
        symbols = page.read().split('\n')
        page.close()

        # pull out the module
        for line in symbols:
            # MODULE windows x86 E40644FDC4D040749962D4C8EB8DF3212 firefox.pdb
            m = re.search('^MODULE (\S+) (\S+) (\S+) (\S+)', line)
            if m:
                new_module = Module(os=m.group(1), arch=m.group(2), hexid=m.group(3), name=m.group(4))
                self.symboldb.session.add(new_module)
                self.symboldb.session.commit()

if __name__ == "__main__":
    test = Symbol()
    url = 'http://symbols.mozilla.org/firefox/firefox.pdb/E40644FDC4D040749962D4C8EB8DF3212/firefox.sym'
    test.add(url)
