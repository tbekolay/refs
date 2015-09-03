#! /usr/bin/env python
#
# Display all records with specified citekey(s).
#
# Cite key can come from command line switches or from a .aux file.  Useful if you
# want to make a reduced .bib file to match a paper, without all the other junk.

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import optparse
import re

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Display all records with specified citekey
::   citekeys from command line or a .aux file'''
p = optparse.OptionParser(usage)
p.add_option('--key', dest='keys', action='append', type='str',
             help='cite key to display (can have multiple of this switch)')
p.add_option('--aux', dest='aux', action='store', type='str',
             help='name of .aux file to parse for keys')
p.add_option('--strings', dest='dumpStrings', action='store_true',
             help='dump the string definitions (abbreviations) as well')
p.add_option('--brief', dest='showBrief', action='store_true',
             help='show the matching records in brief format (default is BibTeX)')
p.set_defaults(keys=[], aux=None, dumpStrings=False, showBrief=False)
(opts, args) = p.parse_args()
globals().update(opts.__dict__)



if len(args) == 0 and sys.stdin.isatty():
    p.print_help()
    sys.exit(0)

# load extra keys from the specified .aux file
if aux:
    f = open(aux, 'r')
    citation = re.compile(r'''^\\citation\{(\w+)\}''')
    for line in f:
        m = citation.match(line)
        if m:
            keys.append( m.group(1) )
keys2 = keys[:]

def action(bib, filename):
    found = []
    for k in keys:
        try:
            be = bib[k]
            found.append(be)
            keys2.remove(k)     # keep track of keys not found
        except:
            pass
    if found:
        for be in found:
            if showBrief:
                if f:
                    print f
                be.brief()
            else:
                be.write()
if args:
    for f in args:
        bib = BibTeX.BibTeX()
        bib.parseFile(f)
        action(bib, f)
else:
    bib = BibTeX.BibTeX()
    bib.parseFile()
    action(bib, None)

if dumpStrings and not showBrief:
    bib.writeStrings()

if keys2:
    print
    for k in keys2:
        print >> sys.stderr, "%s not found" % k
