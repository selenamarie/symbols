
from model import *
from config import symbol_url

import urllib2 as urllib
import re
import fileinput
import sys

def addr_range(address, size):
    return "[%d, %d)" % (address, address + size)

class Symbol():

    def __init__(self):
        self.symboldb = SymbolDB()
        self.command = [] # list of SQL to be executed
        self.module = None

    """ Split a symbols file into a few parts and process """
    def add(self, build, symbols):
        search = {
              'MODULE': 'module'
            , 'FILE': 'file'
            , 'FUNC': 'func'
            , 'STACK': 'stack'
            , 'PUBLIC': 'public'
            , '^(\S+) (\S+) (\d+) (\d+)': 'line'
        }
        split = 0

        piles = {}
        for value in search.values():
            piles[value] = []

        for line in symbols:
            for linestart, column in search.iteritems():
                if re.search(linestart, line):
                    split = column
                    break
            piles[split].append(line.rstrip())

        for pile in ['module', 'file', 'func', 'line', 'stack', 'public']:

            print " Pile size for type %s: %s" % (pile, len(piles[pile]))
            method = '_add_' + pile + '_pile'
            inserts = [insert for line in piles[pile] for insert in getattr(self, method)(line)]

            print " Lines to insert for symbol type %s: %s" % (pile, len(inserts))
            method = '_bulk_add_' + pile
            if len(inserts) > 0:
                getattr(self, method)(inserts)

        self.symboldb.session.commit()


    def _get_webpage(self, url):
        """ _get_webpage(self, url)
            takes a URL as an argument and reads the contents of a symbol file
        """
        page = urllib.urlopen(url)
        symbols = page.read().split('\n')
        page.close()
        self.add(symbols)


    def load_symbols(self, build, path):
        symbols_file = open(path, 'r')
        symbols = symbols_file.readlines()
        symbols_file.close()
        self.add(build, symbols)

    def _add_build(self, build):
        parts = build.split("-")[:-1]
        (moz_app_name, moz_app_version, os_name, buildid) = parts("-")[:4]
        if version.endswith("a1"):
            branch = "nightly"
        elif version.endswith("a2"):
            branch = "aurora"
        elif version.endswith("pre"):
            m = versionRE.match(version)
            if m:
                branch = m.group(0)
            else:
                branch = version
        else:
            branch = "release"

        if len(parts) > 4:  # extra buildid, probably
            extras = "-" + "-".join(parts[4:])

        insert = """
            INSERT INTO builds (
                filename,
                moz_app_name,
                moz_app_version,
                buildid,
                os_target,
                extras)
            VALUES (
                %(filename)s,
                %(moz_app_name)s,
                %(moz_app_version)s,
                %(os_name)s,
                %(buildid)s,
                %(extras)s
            )
            RETURNING id
        """

        values = self._exec_and_return(insert %
            { 'filename': build,
              'moz_app_name': moz_app_name,
              'moz_app_version': moz_app_version,
              'buildid': buildid,
              'os_target': os_name,
              'extras': extras
            })

        self.build = values[0]

    def _exec(self, statement):
        try:
            self.symboldb.session.execute(statement)
            self.symboldb.session.commit()
        except ProgrammingError, e:
            print e

    def _exec_and_return(self, statement):
        values = ()
        cursor = self.symboldb.session.connection().cursor()
        try:
            cursor.execute(statement)
            values = cur.fetchone()
            self.symboldb.session.commit()
        except ProgrammingError, e:
            print e
        return values

    """ Insert chunks of file data into Postgres """
    def _bulk_add_module(self, inserts):
        statement = "INSERT into modules (os, arch, debug_id, debug_file) VALUES"
        things = ','.join(["\n (E'%s', E'%s', E'%s', E'%s')" % insert[:] for insert in inserts])
        statement += things

        self._exec(statement)

        for insert in inserts:
            debug_id = insert[2]
            debug_file = insert[3]
            (self.module,) = self.symboldb.session.query(Module.id).filter_by(
                debug_id=debug_id, debug_file=debug_file).first()
            print self.module

    def _bulk_add_file(self, inserts):
        statement = "INSERT into files (number, name, module) VALUES"
        things = ','.join(["(E'%s', '%s', E'%s')" % (insert[0], insert[1], self.module) for insert in inserts])
        statement += things

        self._exec(statement)


    def _bulk_add_public(self, inserts):
        statement = "INSERT into publics (address, parameter_size, name, module) VALUES"
        things = ','.join(["\n (E'%s', E'%s', E'%s', E'%s')" % (insert[0], insert[1], insert[2], self.module) for insert in inserts])
        statement += things

        self._exec(statement)


    def _bulk_add_func(self, inserts):
        statement = "INSERT into functions (address_range, parameter_size, name, module) VALUES"
        things = ','.join(["\n (E'%s', E'%s', E'%s', E'%s')" %
            (addr_range(insert[0],insert[1]), insert[2], insert[3], self.module) for insert in inserts])
        statement += things

        self._exec(statement)


    def _bulk_add_line(self, inserts):
        statement = "INSERT into lines (address_range, line, file, module) VALUES"
        things = ','.join(["\n (E'%s', E'%s', E'%s', E'%s')" %
            (addr_range(insert[0], insert[1]), insert[2], insert[3], self.module) for insert in inserts])
        statement += things
        self._exec(statement)


    def _bulk_add_stack(self, inserts):
        statement = "INSERT into stackdata (type, address_range, address, data, module) VALUES"
        # protect against bogus data only include addresses <= 0xffffffff, symbol dumper has a bug
        non_cfi_values = ','.join(["\n (E'%s', E'%s', E'%s', E'%s', E'%s')" %
            (insert[0], addr_range(insert[1], insert[2]), insert[1], insert[3], self.module) for insert in inserts if insert[1] <= 0xffffffff and insert[0] != "CFI"])
        if non_cfi_values != '':
            statement += non_cfi_values
            self._exec(statement)

        statement = "INSERT into stackdata (type, address_range, address, data, module) VALUES"
        cfi_values = ','.join(["\n (E'%s', Null, E'%s', E'%s', E'%s')" %
            (insert[0], insert[1], insert[3], self.module) for insert in inserts if insert[1] <= 0xffffffff and insert[0] == "CFI"])
        if cfi_values != '':
            statement += cfi_values
            self._exec(statement)


    """ Create little piles of tuples out of the big file """

    def _add_module_pile(self, line):
        # MODULE mac x86_64 761889B42181CD979921A004C41061500 XUL

        m = re.search('^MODULE (\S+) (\S+) (\S+) (.+)', line)
        if m:
            if len(m.groups()) < 3:
                # Bogus symbols file!
                print "skipping %s", line
                skip = 1
                return

            os = m.group(1)
            arch = m.group(2)
            debug_id = m.group(3)
            debug_file = m.group(4)

            yield (os, arch, debug_id, debug_file)

    def _add_file_pile(self, line):
        m = re.search('^FILE (\S+) (.*)', line)
        if m:
            number = int(m.group(1))
            name = m.group(2)
            yield (number, name)

    def _add_func_pile(self, line):
            m = re.search('^FUNC (\S+) (\S+) (\S+) (.+)', line)
            if m:
                address = int(m.group(1), 16)
                size = int(m.group(2), 16)
                parameter_size = int(m.group(3), 16)
                name = m.group(4)
                yield (address, size, parameter_size, name)

    def _add_stack_pile(self, line):
        m = re.search('^STACK WIN ((\S+) (\S+) (\S+) .*)', line)
        if m:
            address = int(m.group(3), 16)
            size = int(m.group(4), 16)
            data = m.group(1)
            yield ("WIN", address, size, data)

        m = re.search('^STACK CFI INIT (\S+) (\S+) (.*)', line)
        if m:
            address = int(m.group(1), 16)
            size = int(m.group(2), 16)
            data = m.group(3)
            # type, address, size, data
            yield ("CFI INIT", address, size, data)

        m = re.search('^STACK CFI ([^I]\S+) (.*)', line)
        if m:
            address = int(m.group(1), 16)
            size = None
            data = m.group(2)
            yield ("CFI", address, size, data)

    def _add_public_pile(self, line):
        m = re.search('^PUBLIC (\S+) (\S+) (.+)', line)
        if m:
            address = int(m.group(1), 16)
            parameter_size = int(m.group(2), 16)
            name = m.group(3)
            yield (address, parameter_size, name)

    def _add_line_pile(self, line):
        m = re.search('^(\S+) (\S+) (\d+) (\d+)', line)
        if m:
            address = int(m.group(1), 16)
            size = int(m.group(2), 16)
            line = int(m.group(3))
            file = int(m.group(4))
            yield (address, size, line, file)


    def remove(self, debug_id, name):
        pass


    """ Leftover """
    def _add_build(self, m):
        try:
            new = Build(os=m.group(1), arch=m.group(2), debug_id=m.group(3), name=m.group(4))
            self.symboldb.session.add(new)
            self.symboldb.session.commit()
        except ProgrammingError, e:
            print e
            return None
        return(new.id)


if __name__ == "__main__":
    test = Symbol()

    import glob
    # If we're dealing with files:
    build = ''
    for line in fileinput.input():
        if build != fileinput.filename():
            build = fileinput.filename()
        line = line.rstrip()
        if not line.endswith(".sym"):
            continue
        print "Working on %s" % line
        test.load_symbols(build, line)

    exit(0)

    # If we're dealing with URLs:
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

