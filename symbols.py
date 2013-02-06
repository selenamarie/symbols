
import model

import urllib2 as urllib
import re

class Symbol():


    def add(self, url):
        page = urllib.urlopen(url)
        symbols = page.read().split('\n')
        page.close()

        # pull out the module
        for line in symbols:
            # MODULE windows x86 E40644FDC4D040749962D4C8EB8DF3212 firefox.pdb
            m = re.search('^MODULE (\S+) (\S+) (\S+) (\S+)', line)
            if m:
                print m.group(0)

if __name__ == "__main__":
    test = Symbol()
    url = 'http://symbols.mozilla.org/firefox/firefox.pdb/E40644FDC4D040749962D4C8EB8DF3212/firefox.sym'
    test.add(url)
