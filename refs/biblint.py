#! /usr/bin/env python
#
# Report missing fields and bad values in bibtex records

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import optparse

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Report missing fields and bad values in bibtex records'''
p = optparse.OptionParser(usage)
#p.add_option('--reverse', dest='reverseSort', action='store_true',
#             help='sort into ascending data order (old at top)')
#p.add_option('--resolve', dest='resolve', action='store_true',
#             help='resolve cross reference entries')
#p.set_defaults(reverseSort=False, resolve=False)
(opts, args) = p.parse_args()
globals().update(opts.__dict__)

if len(args) == 0 and sys.stdin.isatty():
	p.print_help()
	sys.exit(0)

## read the input files

if args:
	for f in args:
		bib = BibTeX.BibTeX()
		bib.parseFile(f)
		print "%d records read from %s" % (len(bib), bib.getFilename())

		print
		for be in bib:
			c = be.check()
			if c:
				print "%15s: missing " % (be.getKey()), string.join(c, ', ')
else:
	bib = BibTeX.BibTeX()
	bib.parseFile()
	print "%d records read from %s" % (len(bib), '(stdin)')

	print
	for be in bib:
		c = be.check()
		if c:
			print "%15s: missing " % (be.getKey()), string.join(c, ', ')
