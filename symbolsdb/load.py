#!/usr/bin/env python

import os
import urllib2 as urllib
import re
import fileinput
import sys

from model import *
from config import symbol_url


def addr_range(address, size):
    return "[%d, %d)" % (address, address + size)

class Symbol(object):

    def __init__(self):
        self.symboldb = SymbolDB()
        self.command = [] # list of SQL to be executed
        self.module = None
        self.record_types = ['module', 'file', 'func', 'line', 'stack', 'public']
        self.search = {
              'MODULE': 'module'
            , 'FILE': 'file'
            , 'FUNC': 'func'
            , 'STACK': 'stack'
            , 'PUBLIC': 'public'
            , '^(\S+) (\S+) (\d+) (\d+)': 'line'
        }


    def add_symbol_file(self, build, symbols):
        """ Take a list of symbols filesystem paths into a few parts and process """
        for symbol_filename in symbols:
            with open(os.path.join(os.getcwd(), 'fixtures', symbol_filename.rstrip())) as s:
                symbols_list = s.readlines()
                split_records = self.partition_symbol_records(symbols_list)
                for record_type, inserts in self.create_record_inserts(split_records):
                    self.run_record_inserts(record_type, inserts)


    def partition_symbol_records(self, symbols):
        split = 0
        split_records = {}

        for line in symbols:
            for linestart, column in self.search.iteritems():
                if re.search(linestart, line):
                    split = column
                    break
            try:
                split_records[split].append(line.rstrip())
            except KeyError:
                split_records[split] = [line.rstrip()]

        return split_records


    def create_record_inserts(self, split_records):
        """ Generate bulk insert SQL """

        for record_type in self.record_types:
            print " Pile size for type %s: %s" % (record_type, len(split_records[record_type]))

            method = '_add_' + record_type + '_pile'
            inserts = [insert for line in split_records[record_type] for insert in getattr(self, method)(line)]
            print " Lines to insert for symbol type %s: %s" % (record_type, len(inserts))
            yield (record_type, inserts)


    def run_record_inserts(self, partition, inserts):
        """ Execute bulk insert SQL """

        method = '_bulk_add_' + partition
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
        self.add_symbol_file(symbols)


    def load_build_file(self, build, path):
        """ Read in all the lines in a -symbols.txt build file """
        symbols_file = open(path, 'r')
        self.symbols = symbols_file.readlines()
        symbols_file.close()
        self.add_symbol_file(build, self.symbols)


    def _parse_build(self, build):
        """ Parse out information in a build file name """
        extras = ''
        branch = ''

        # Remove '-symbols.txt'
        parts = build.split("-")[:-1]

        # Divide up build data
        (moz_app_name, moz_app_version, os_name, buildid) = parts[:4]
        if moz_app_version.endswith("a1"):
            branch = "nightly"
        elif moz_app_version.endswith("a2"):
            branch = "aurora"
        elif moz_app_version.endswith("pre"):
            m = versionRE.match(version)
            if m:
                branch = m.group(0)
            else:
                branch = version
        else:
            branch = "release"

        # Collect anything extra in build naming; extra buildid, probably
        if len(parts) > 4:
            extras = "-".join(parts[4:])

        return (moz_app_name, moz_app_version, os_name, buildid, extras)


    def _add_build(self, build):
        (moz_app_name, moz_app_version, os_name, buildid, extras) = \
            self._parse_build(build)

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

        values = self._exec_and_return_one(insert % {
            'filename': build,
            'moz_app_name': moz_app_name,
            'moz_app_version': moz_app_version,
            'buildid': buildid,
            'os_name': os_name,
            'extras': extras # Can be an empty string
        })

        self.build = values[0]
        return build

    def _exec(self, statement):
        """ Run a simple SQL statement and try to commit """
        try:
            self.symboldb.session.execute(statement)
            self.symboldb.session.commit()
        except ProgrammingError, e:
            print e


    def _exec_and_return_one(self, statement):
        """ Run a simple SQL statement and return one row"""
        values = ()
        cursor = self.symboldb.session.connection().cursor()
        try:
            cursor.execute(statement)
            values = cur.fetchone()
            self.symboldb.session.commit()
        except ProgrammingError, e:
            print e
        return values


    """ _bulk_add_* helper functions for generating SQL """

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


    """ All _add_*_pile() helper functions read in a line and yield tuples to be
        inserted into Postgres
    """

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
        test.load_build_file(build, line)

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

