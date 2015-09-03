#! /usr/bin/env python
#
# Display a summary of the reference types

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import optparse

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Display a summary of the reference types'''
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
bib = BibTeX.BibTeX()
if args:
    for f in args:
        bib.parseFile(f)
else:
    bib.parseFile()

count = {}
urlCount = 0


for be in bib:
    t = be.getRefType()
    if be.getField('Url'):
        urlCount += 1
    if t in count:
        count[t] += 1
    else:
        count[t] = 1

for k in count:
    print "  %15s: %4d" % (k, count[k])

if urlCount > 0:
    print "  %d with URL links" % urlCount
