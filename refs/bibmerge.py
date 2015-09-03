#! /usr/bin/env python
#
# Fuzzy merge of bibliographies.
#
# A hiearchy of matching tests is implemented:
#
#	Reference type
#	Year of publication
#	Month of publication (if known)
#	Volume number (if article type)
#	Page numbers (if known)
#	Author surnames
#	Fuzzy match on title exclusing white space and punctuation characters,
#	  using Levenstein distance
#
# Really useful when you are jointly writing a paper and the authors have partially
# overlapping bib files with different cite key conventions.

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import optparse

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Fuzzy merge of bibliographies.'''
p = optparse.OptionParser(usage)
p.add_option('--dthresh', dest='dthresh', action='store', type='int',
             help='set the fuzzy match tolerance (Levenstein distance) for title string')
p.add_option('--showdup', dest='showdup', action='store_true',
             help='show information about proposed duplicates')
p.add_option('-v', '--verbose', dest='verbose', action='store_true',
             help='print some extra information')
p.set_defaults(dthresh=2, showdup=False, verbose=False)
(opts, args) = p.parse_args()
globals().update(opts.__dict__)

if len(args) == 0 and sys.stdin.isatty():
	p.print_help()
	sys.exit(0)


unique = BibTeX.BibTeX()
dupcount = 0

def action(bib, filename):
    global dupcount, unique

    if verbose:
        print >> sys.stderr,  "%d records read from %s" % (len(bib), filename)

    # for each new bib entry
    for be in bib:
        # check against all existing
        for ub in unique:
            if be.match(ub, dthresh=dthresh):
                if verbose:
                    print >> sys.stderr,  " -[%s] %s" % (be.getKey(), be)
                dupcount += 1
                if showdup:
                    print >> sys.stderr, "============================="
                    ub.write(sys.stderr)
                    print >> sys.stderr, "---------- duplicate from %s" % bib.getFilename()
                    be.write(sys.stderr)
                break
        else:
            if verbose:
                print >> sys.stderr,  " +[%s] %s" % (be.getKey(), be)
            unique.insertEntry(be)

## read the input files
bib = BibTeX.BibTeX()
if args:
	for f in args:
		bib = BibTeX.BibTeX()
		bib.parseFile(f)
		action(bib, f)
else:
	bib = BibTeX.BibTeX()
	bib.parseFile()
	action(bib, '(stdin)')


print >> sys.stderr,  "New bib has %d records, %d duplicates found" % (len(unique), dupcount)

unique.write()
