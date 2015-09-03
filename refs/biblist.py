#! /usr/bin/env python
#
# List bibtex file in human readable format

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import optparse

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Display bibtex file in human readable format'''
p = optparse.OptionParser(usage)
p.add_option('--brief', dest='showBrief', action='store_true',
             help='brief listing (one line per entry)')
p.add_option('--abbrev', dest='resolveAbbrevs', action='store_true',
             help='resolve abbreviations from defined strings')
#p.add_option('--resolve', dest='resolve', action='store_true',
#             help='resolve cross reference entries')
p.set_defaults(showBrief=False, resolveAbbrevs=False)
(opts, args) = p.parse_args()
globals().update(opts.__dict__)

if len(args) == 0 and sys.stdin.isatty():
	p.print_help()
	sys.exit(0)

## read the input files
bib = BibTeX.BibTeX()
if args:
	for f in args:
		bib.parseFile(f)
else:
	bib.parseFile()

# resolve cross refs and abbreviations
bib.resolveCrossRef()
if resolveAbbrevs:
	bib.resolveAbbrev()

# output the readable text
for be in bib:
	if showBrief:
		be.brief()
	else:
		be.display()
	print
