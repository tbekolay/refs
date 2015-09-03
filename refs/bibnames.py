#! /usr/bin/env python
#
# Display a list of authors and their occurrence in the bibfiles
#
# each output line is of the form:
#
#   Surname,I  N
#
# where I is their initial and N is the number of occurrences.  This can be
# fed throug sort -n -r +1 to get a list of authors in descending order
# of occurrence.  Figure out who is your favourite co-author!

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import getopt
import optparse

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Display a list of authors and their occurrence'''
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

# Build a list of unique names: Surname,Initial and update occurrence
nameList = {}
for be in bib:
    surnames = be.getAuthorsSurnameList()
    if surnames:
        for s in surnames:
            s = ','.join(s)
            if s in nameList:
                nameList[s] += 1
            else:
                nameList[s] = 1

# display names and occurrence.
for s,v in  nameList.iteritems():
    print s, v
