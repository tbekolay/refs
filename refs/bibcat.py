#! /usr/bin/env python
#
# Concatenate bib file(s) to stdout.  Each file is parsed then the BibTeX
# records are regenerated.
#

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import optparse

resolve = False


## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Concatenate bib file(s) to stdout.
::   Each file is parsed then the BibTeX records are regenerated'''
p = optparse.OptionParser(usage)
p.add_option('--ignore', dest='ignore', action='store_true',
             help='ignore duplicate items')
p.add_option('--nostrings', dest='dumpStrings', action='store_false',
             help='dump string definitions')
p.add_option('-v', '--verbose', dest='verbose', action='store_true',
             help='print some extra information')
p.add_option('--resolve', dest='resolve', action='store_true',
             help='resolve cross reference entries')
p.set_defaults(ignore=False, dumpStrings=True, verbose=False, resolve=False)
(opts, args) = p.parse_args()
globals().update(opts.__dict__)

if len(args) == 0 and sys.stdin.isatty():
    p.print_help()
    sys.exit(0)

## read the input files
bib = BibTeX.BibTeX()
if args:
    for f in args:
        nbib = bib.parseFile(f, ignore=ignore)
        if verbose:
            sys.stderr.write( "%d entries read from %s\n" % (len(bib), f) )
else:
    nbib = bib.parseFile()
    if verbose:
        sys.stderr.write( "%d entries read from stdin\n" % (len(bib),) )

if resolve:
    bib.resolveAbbrev()

if verbose:
    sys.stderr.write( "%d abbreviations to write\n" % len(outbib.getAbbrevs()) )
    sys.stderr.write( "%d entries to write\n" % len(outbib) )
if dumpStrings:
    bib.writeStrings()
bib.write(resolve=resolve)
