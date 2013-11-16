#!/bin/env python

# Count up the relevant symbols in the symbols directory

import os
import os.path
import sys
import re
from datetime import datetime, timedelta
from optparse import OptionParser
from hurry.filesize import size

nightliesPerBin = 30

versionRE = re.compile("^(\d+\.\d+)")

parser = OptionParser(usage="usage: %prog [options] <symbol path> [symbol indexes to remove]")
parser.add_option("-d", "--dry-run",
                  action="store_true", dest="dry_run", default=False,
                  help="Don't delete anything, just print a list of actions")
parser.add_option("-r", "--remove-these-symbols",
                  action="store_true", dest="remove_symbols",
                  help="Remove specified symbol indexes and their contained symbols")
(options, args) = parser.parse_args()

if not args:
    print >>sys.stderr, "Must specify a symbol path!"
    sys.exit(1)
symbolPath = args[0]

# Cheezy atom implementation, so we don't have to store symbol filenames 
# multiple times.
atoms = []
atomdict = {}


def atomize(s):
    if s in atomdict:
        return atomdict[s]
    a = len(atoms)
    atoms.append(s)
    atomdict[s] = a
    return a


def sortByBuildID(x, y):
    "Sort two symbol index filenames by the Build IDs contained within"
    (a, b) = (os.path.basename(x).split('-')[3],
              os.path.basename(y).split('-')[3])
    return cmp(a, b)

buildidRE = re.compile("(\d\d\d\d)(\d\d)(\d\d)(\d\d)")

def adddefault(d, key, default):
    "If d[key] does not exist, set d[key] = default."
    if key not in d:
        d[key] = default

def addFiles(symbolindex, filesDict):
    """Return a list of atoms representing the symbols in this index file.
Also add 1 to filesDict[atom] for each symbol."""
    l = []
    try:
        sf = open(symbolindex, "r")
        for line in sf:
            a = atomize(line.rstrip())
            l.append(a)
            adddefault(filesDict, a, 0)
            #filesDict[a] += 1
        sf.close()
    except IOError:
        pass
    return l


def getSizeSymbols(symbols, filesDict):
    "Decrement reference count by one for each symbol in this symbol index."
    for a in symbols:
        sizefiles[a] += os.path.getsize(os.path.join(symbolPath,f))



# Look in the path and find any symbols files
builds = {}
buildfiles = {}
sizefiles = {}

print "[1/4] Reading symbol index files..."

# get symbol index files, there's one per build
for f in os.listdir(symbolPath):
    if not (os.path.isfile(os.path.join(symbolPath, f)) and
            f.endswith("-symbols.txt")):
        continue
    # increment reference count of all symbol files listed in the index
    # and also keep a list of files from that index
    buildfiles[f] = addFiles(os.path.join(symbolPath, f), sizefiles)
    # drop -symbols.txt
    parts = f.split("-")[:-1]
    (product, version, osName, buildId) = parts[:4]
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
    # group into bins by branch-product-os[-featurebranch]
    identifier = "%s-%s-%s" % (branch, product, osName)
    if len(parts) > 4:  # extra buildid, probably
        identifier += "-" + "-".join(parts[4:])
    adddefault(builds, identifier, [])
    builds[identifier].append(f)

print "[2/4] Looking for symbols we care about..."

for bin in builds:
    if bin.startswith("release"):
        # count all of these
        for f in builds[bin]:
            getSizeSymbols(buildfiles[f], sizefiles)
    else:
        builds[bin].sort(sortByBuildID)
        if len(builds[bin]) > nightliesPerBin:
            for f in builds[bin][:nightliesPerBin]:
                getSizeSymbols(buildfiles[f], sizefiles)

print size(sum(sizefiles.values()))


