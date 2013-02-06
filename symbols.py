
from model import *

import urllib2 as urllib
import re

class Symbol():

    def __init__(self):
        self.symboldb = SymbolDB()

    def _add_module(self, m):
        try:
            new_module = Module(os=m.group(1), arch=m.group(2), debug_id=m.group(3), name=m.group(4))
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

    def _add_func(self, m, mod_id):
        try:
            new = Func(address=m.group(1), size=m.group(2), line=m.group(3), filenum=m.group(4), module=mod_id)
            self.symboldb.session.add(new)
            self.symboldb.session.commit()
        except:
            return None

    def _add_line(self, m, file):
        try:
            new = File(address=m.group(1), size=m.group(2), line=m.group(3), filenum=m.group(4), file=file)
            self.symboldb.session.add(new)
            self.symboldb.session.commit()
        except:
            return None

    def _add_stack(self, m, module):
        try:
            new = Stackwalk(address=m.group(2), stackwalk_data=m.group(4), module=module)
            self.symboldb.session.add(new)
            self.symboldb.session.commit()
        except:
            return None


    def add(self, url):
        page = urllib.urlopen(url)
        symbols = page.read().split('\n')
        page.close()

        for line in symbols:
            if line is None:
                break

            m = re.search('^MODULE (\S+) (\S+) (\S+) (\S+)', line)
            if m:
                module = self.symboldb.session.query(Module.id).filter_by(debug_id=m.group(3), name=m.group(4)).first()
                if module:
                    break
                mod_id = self._add_module(m)
                continue

            m = re.search('^FILE (\S+) (\S+)', line)
            if m:
                file_id = self._add_file(m, mod_id)
                continue

            m = re.search('^FUNC (\S+) (\S+) (\S+) (\S+)', line)
            if m:
                func_id = self._add_func(m, mod_id)
                continue

            m = re.search('^STACK WIN (\S+) (\S+) (\S+) (.*)', line)
            if m:
                stack_id = self._add_stack(m, mod_id)
                continue

            m = re.search('^(\S+) (\S+) (\S+) (\S+)', line)
            if m:
                file_number = self.symboldb.session.query(File.id).filter_by(number=m.group(4), module=mod_id).first()
                line = self._add_line(m, file_number.id)
                continue
            print "bogus: %s" % line

if __name__ == "__main__":
    test = Symbol()
    url = 'http://symbols.mozilla.org/firefox/firefox.pdb/E40644FDC4D040749962D4C8EB8DF3212/firefox.sym'
    test.add(url)
