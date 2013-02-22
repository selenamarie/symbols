
from model import *
from config import symbol_url

import urllib2 as urllib
import re
import fileinput

def addr_range(address, size):
    return "[%d, %d)" % (address, address + size)

class Symbol():

    def __init__(self):
        self.symboldb = SymbolDB()

    def _add_build(self, m):
        try:
            new = Build(os=m.group(1), arch=m.group(2), debug_id=m.group(3), name=m.group(4))
            self.symboldb.session.add(new)
            self.symboldb.session.commit()
        except ProgrammingError, e:
            print e
            return None
        return(new.id)

    def _add_module(self, os, arch, debug_id, debug_file):
        try:
            new = Module(os=os, arch=arch,
                         debug_id=debug_id, debug_file=debug_file)
            self.symboldb.session.add(new)
            self.symboldb.session.commit()
        except ProgrammingError, e:
            print e
            return None
        return(new.id)


    def _add_file(self, module, number, name):
        try:
            new = File(number=number, name=name, module=module)
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e
            return None

    def _add_public(self, module, address, parameter_size, name):
        try:
            new = Public(address=address,
                         parameter_size=parameter_size,
                         name=name,
                         module=module)
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e

    def _add_func(self, module, address, size, parameter_size, name):
        try:
            new = Function(parameter_size=parameter_size,
                           name=name,
                           module=module,
                           address_range=addr_range(address, size))
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e

    def _add_line(self, module, address, size, line, file):
        try:
            new = Line(line=line,
                       file=file,
                       module=module,
                       address_range=addr_range(address, size))
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e
            return None

        return(new.id)

    def _add_stack(self, module, type, address, size, data):
        try:
            new = Stackdata(type=type,
                            address_range=addr_range(address, size),
                            data=data,
                            module=module)
            self.symboldb.session.add(new)
        except ProgrammingError, e:
            print e

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

            line = line.rstrip()
            if not line:
                continue

            m = re.search('^MODULE (\S+) (\S+) (\S+) (.+)', line)
            if m:
                os=m.group(1)
                arch=m.group(2)
                debug_id=m.group(3)
                debug_file=m.group(4)
                module = self.symboldb.session.query(Module.id).filter_by(
                    debug_id=debug_id, debug_file=debug_file).first()
                if module:
                    skip = 1
                    break

                mod_id = self._add_module(os, arch, debug_id, debug_file)
                continue

            m = re.search('^FILE (\S+) (.*)', line)
            if m:
                number = int(m.group(1))
                name = m.group(2)
                self._add_file(mod_id, number, name)
                continue

            m = re.search('^FUNC (\S+) (\S+) (\S+) (.+)', line)
            if m:
                address = int(m.group(1), 16)
                size = int(m.group(2), 16)
                parameter_size = int(m.group(3), 16)
                name = m.group(4)
                self._add_func(mod_id, address, size, parameter_size, name)
                continue

            m = re.search('^STACK WIN ((\S+) (\S+) (\S+) .*)', line)
            if m:
                address = int(m.group(3), 16)
                size = int(m.group(4), 16)
                data = m.group(1)
                self._add_stack(mod_id, "WIN", address, size, data)
                continue

            m = re.search('^PUBLIC (\S+) (\S+) (.+)', line)
            if m:
                address = int(m.group(1), 16)
                parameter_size = int(m.group(2), 16)
                name = m.group(3)
                self._add_public(mod_id, address, parameter_size, name)
                continue

            m = re.search('^(\S+) (\S+) (\d+) (\d+)', line)
            if m:
                address = int(m.group(1), 16)
                size = int(m.group(2), 16)
                line = int(m.group(3))
                file = int(m.group(4))
                self._add_line(mod_id, address, size, line, file)
                continue

        self.symboldb.session.commit()

    def remove(self, debug_id, name):
        pass

if __name__ == "__main__":
    test = Symbol()

    import glob
    urls = []
    for line in fileinput.input():
        line = line.rstrip()
        if not line.endswith(".sym"):
            continue
        urls.append(line)

    print len(urls)
    for url in urls:
        #if re.search('js.pdb', url):
        print "Adding %s" % url
        test.add(symbol_url + url)

