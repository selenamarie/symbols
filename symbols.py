
from model import *

import urllib2 as urllib
import re

class Symbol():

    def __init__(self):
        self.symboldb = SymbolDB()

    def _add_build(self, m):
        try:
            new_module = Module(os=m.group(1), arch=m.group(2), debug_id=m.group(3), name=m.group(4))
            self.symboldb.session.add(new_module)
        except ProgrammingError, e:
            print e
            return None

    def _add_module(self, m):
        try:
            new_module = Module(os=m.group(1), arch=m.group(2), debug_id=m.group(3), name=m.group(4))
            self.symboldb.session.add(new_module)
        except ProgrammingError, e:
            print e
            return None

        return(new_module.id)

    def _add_file(self, m, mod_id):
        try:
            new = File(number=m.group(1), name=m.group(2), module=mod_id)
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e
            return None

        return(new.id)

    def _add_public(self, m, mod_id):
        try:
            new = Function(address=int("0x%s" % m.group(1), 16), size=m.group(2), name=m.group(3), module=mod_id, address_range="[%d, %d)" % (int("0x%s" % m.group(1), 16), int("0x%s" % m.group(1), 16) + int("0x%s" % m.group(2), 16) ))
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e
            return None

    def _add_func(self, m, mod_id):
        try:
            new = Function(address=int("0x%s" % m.group(1), 16), size=m.group(2), parameter_size=m.group(3), name=m.group(4), module=mod_id, address_range="[%d, %d)" % (int("0x%s" % m.group(1), 16), int("0x%s" % m.group(1), 16) + int("0x%s" % m.group(2), 16) ))
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e
            return None

    def _add_line(self, m, file):
        try:
            new = Line(address=int("0x%s" % m.group(1), 16), size=m.group(2), line=m.group(3), filenum=m.group(4), file=file, address_range="[%d, %d)" % (int("0x%s" % m.group(1), 16), int("0x%s" % m.group(1), 16) + int("0x%s" % m.group(2), 16) ))
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e
            return None

    def _add_stack(self, m, module):
        try:
            new = Stackwalk(address=int("0x%s" % m.group(2), 16), stackwalk_data=m.group(0), module=module)
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e
            return None

    def add(self, url):
        page = urllib.urlopen(url)
        symbols = page.read().split('\n')
        page.close()
        module = None
        mod_id = None
        last_func = None
        last_line = None
        last_public = None
        skip = 0

        for line in symbols:
            if line is None:
                break

            m = re.search('^MODULE (\S+) (\S+) (\S+) (\S+)', line)
            if m:
                module = self.symboldb.session.query(Module.id).filter_by(debug_id=m.group(3), name=m.group(4)).first()
                if module:
                    skip = 1
                    break
                mod_id = self._add_module(m)
                continue

            m = re.search('^FILE (\S+) (.*)', line)
            if m:
                file_id = self._add_file(m, mod_id)
                continue

            m = re.search('^FUNC (\S+) (\S+) (\S+) (\S+)', line)
            if m:
                func_id = self._add_func(m, mod_id)
                continue

            # XXX Figure out how to handle ranges for stacks, also non WIN stacks
            m = re.search('^STACK WIN (\S+) (\S+) (\S+) (.*)', line)
            if m:
                stack_id = self._add_stack(m, mod_id)
                continue

            # XXX
            m = re.search('^PUBLIC (\S+) (\S+) (\S+)', line)
            if m:
                continue

            m = re.search('^(\S+) (\S+) (\S+) (\S+)', line)
            if m:
                file_number = self.symboldb.session.query(File.id).filter_by(number=m.group(4), module=mod_id).first()
                line = self._add_line(m, file_number.id)
                continue
            print "bogus: %s" % line

        self.symboldb.session.commit()

    def remove(self, debug_id, name):
        pass

if __name__ == "__main__":
    test = Symbol()

    # urls = ['http://symbols.mozilla.org/firefox/firefox.pdb/E40644FDC4D040749962D4C8EB8DF3212/firefox.sym']
    prefix = 'http://symbols.mozilla.org/firefox/'
    import glob
    urls = []
    for f in glob.glob("/tmp/blahrg/*.txt"):
        pfile = open(f)
        paths = pfile.read().split('\n')
        pfile.close()
        for path in paths:
            if re.search('pd_', path):
                continue
            urls.append(path)

    print len(urls)
    for url in urls:
        #if re.search('js.pdb', url):
        print "Adding %s" % url
        test.add(prefix + url)

