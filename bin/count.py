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


# What we think the current release versions are for a few products
current_release = { 'firefox': 26, 'thunderbird': 12, 'xulrunner': 25, 'b2g': 18, 'fennec': 26 }

# Only save the last six months of builds
save_date_6mo = datetime.now() - timedelta(weeks=32)
save_builds = { 'b2g': save_date_6mo, 'firefox': save_date_6mo }

# For moz central and aurora
save_date_6weeks = datetime.now() - timedelta(weeks=6)

# For nightlies
save_date_30days = datetime.now() - timedelta(days=30)

# Betas and release by buildid (omg)
buildids = [line.rstrip() for line in open('builds_201311', 'r')]

versionRE = re.compile("^(\d+\.\d+)")

parser = OptionParser(usage="usage: %prog [options] <symbol path> [symbol indexes to remove]")
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
    for a in symbols:
        full_path = os.path.join(symbolPath, atoms[a])
        if os.path.exists(full_path):
            filesDict[a] += os.path.getsize(full_path)
        else:
           #print "File not found: %s" % full_path
           pass

def getSizePDB(symbols, filesDict):
    for a in symbols:
        filename = atoms[a][:-4]
        filename += ".pdb"
        full_path = os.path.join(symbolPath, filename)
        if os.path.exists(full_path):
            adddefault(filesDict, a, 0)
            filesDict[a] += os.path.getsize(full_path)
        else:
           print "File not found: %s" % full_path


# Look in the path and find any symbols files
builds = {}
buildfiles = {}
sizefiles = {}
sizepdb = {}

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
        build_date = datetime.strptime(buildId[0:12], '%Y%m%d%H%M')
        if build_date < save_date_30days:
            print "Skipping buildId: %s for product: %s" % (buildId, product.lower())
            continue
    elif version.endswith("a2"):
        branch = "aurora"
        build_date = datetime.strptime(buildId[0:12], '%Y%m%d%H%M')
        if build_date < save_date_6weeks:
            print "Skipping buildId: %s for product: %s" % (buildId, product.lower())
            continue
    elif version.endswith("pre"):
        m = versionRE.match(version)
        if m:
            branch = m.group(0)
        else:
            branch = version
    else:
        branch = "release"
        # Only care about the releases which are ESR or current_release-2
        version_parts = version.split('.')
        if product.lower() in current_release:
            if int(version_parts[0]) < (current_release[product.lower()] - 2) and not version.endswith("esr"):
                print "Skipping version: %s for product: %s" % (version, product.lower())
                continue

        # Try to filter out betas and releases that are too old
        if product.lower() == 'firefox' and buildId not in builds:
            print "BETA: Skipping buildId: %s for product: %s" % (buildId, product.lower())
            continue

    # only save last 6 months of builds in our build data structure
    if product.lower() in save_builds:
        save_date = save_builds[product.lower()]
        build_date = datetime.strptime(buildId[0:12], '%Y%m%d%H%M')
        if build_date < save_date:
            print "Skipping buildId: %s for product: %s" % (buildId, product.lower())
            continue


    # group into bins by branch-product-os[-featurebranch]
    identifier = "%s-%s-%s" % (branch, product, osName)
    if len(parts) > 4:  # extra buildid, probably
        identifier += "-" + "-".join(parts[4:])
    print identifier, ": ", f
    adddefault(builds, identifier, [])
    builds[identifier].append(f)

print "[2/4] Looking for symbols we care about..."

for bin in builds:
    if bin.startswith("release"):
        # count all of these
        for f in builds[bin]:
            getSizeSymbols(buildfiles[f], sizefiles)
            #getSizePDB(buildfiles[f], sizepdb)
    else:
        builds[bin].sort(sortByBuildID)
        if len(builds[bin]) > nightliesPerBin:
            for f in builds[bin][:nightliesPerBin]:
                getSizeSymbols(buildfiles[f], sizefiles)
                #getSizePDB(buildfiles[f], sizepdb)

print "Total builds found: %i" % len(builds)
print "Total files found: %i" % len(sizefiles)
print "Total files found with .pdb: %i" % len(sizepdb)
print "Size of files: %s" % size(sum(sizefiles.values()))



