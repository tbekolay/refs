#! /usr/bin/env python
#
# Filter bib records that match search criteria
#
# todo:
#   handle tex accent characters, utf-16 etc

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import optparse

startDate = None
endDate = None

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Filter bib records that match search criteria
::   Multiple rules can be applied at the same time '''
p = optparse.OptionParser(usage)
p.add_option('--since', dest='since', action='store', type='str',
             help='start date for selection, format YYYY or MM/YYYY')
p.add_option('--before', dest='before', action='store', type='str',
             help='end date for selection, format YYYY or MM/YYYY')
p.add_option('-i', '--case', dest='caseSens', action='store_true',
             help='make search case sensitive')
p.add_option('--type', dest='type', action='store', type='str',
             help='reference type to search (default all)')
p.add_option('--field', dest='field', nargs=2, action='store', type='str',
             help='field to search (default all) and the value which matches any substring in the specified field')
p.add_option('--hasfield', dest='hasfield', action='store', type='str',
             help='true if specified field is present')
p.add_option('--brief', dest='showBrief', action='store_true',
             help='show the matching records in brief format (default is BibTeX)')
p.add_option('--count', dest='showCount', action='store_true',
             help='show just the number of matching records')
p.set_defaults(since=None, before=None, caseSens=False, type='all', hasfield=None, field=['all', '*'], showBrief=False, showCount=False)
(opts, args) = p.parse_args()
globals().update(opts.__dict__)

if len(args) == 0 and sys.stdin.isatty():
    p.print_help()
    sys.exit(0)

if since:
    startDate = map(int, since.split('/'))
if before:
    endDate = map(int, before.split('/'))


## read the input files
bib = BibTeX.BibTeX()
if args:
    for f in args:
        bib.parseFile(f)
else:
    bib.parseFile()

#print >> sys.stderr,  "looking for <%s> in field <%s>, reftype <%s>" % (field[1], field[0], type)

# search the bibliography for all matches to the field query
l = bib.search(field[0], field[1], type, caseSens)
count = 0
for be in l:
    # check if it has the required field
    if hasfieldpp:
        if not be.getField(hasfield):
            continue

    # check the date range
    if be.afterDate(startDate) and be.beforeDate(endDate):
        count += 1
        if not showCount:
            if showBrief:
                print be
            else:
                be.write()

if showCount:
    print count
