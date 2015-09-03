#! /usr/bin/env python
#
# Sort bibliographies in chronological order

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import optparse


## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Sort bibliographies in chronological order'''
p = optparse.OptionParser(usage)
p.add_option('--reverse', dest='reverseSort', action='store_true',
             help='sort into ascending data order (old at top)')
p.add_option('--resolve', dest='resolve', action='store_true',
             help='resolve cross reference entries')
p.set_defaults(reverseSort=False, resolve=False)
(opts, args) = p.parse_args()
globals().update(opts.__dict__)

if len(args) == 0 and sys.stdin.isatty():
	p.print_help()
	sys.exit(0)

count = {}

sortReturn = -1 if reverseSort else 1

def sortByDate(a, b):
	# On input a and b are BibEntry objects
	ay = a.getYear()
	by = b.getYear()
	if ay > by:
		return -sortReturn
	elif ay < by:
		return sortReturn
	else:
		am = a.getMonth()
		bm = b.getMonth()
		if am > bm:
			return -sortReturn
		elif am < bm:
			return sortReturn
		else:
			return 0

outbib = BibTeX.BibTeX()

if args:
	for f in args:
		bib = BibTeX.BibTeX()
		n = bib.parseFile(f)

		sys.stderr.write( "%d records read from %s\n" % (n, f) )

else:
	bib = BibTeX.BibTeX()
	bib.parseFile()

	sys.stderr.write( "%d records read from stdin\n" % len(bib) )

# sort it
bib.sort(sortByDate)

# and output the result
for s in bib:
	s.write()
