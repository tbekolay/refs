#! /usr/bin/env python
#
# Convert bib file(s) to dvi
#
# TODO
#   handle resolve switch if command line files are given


import Bibliography
import BibEntry
import BibTeX
import string
import sys
import os
import optparse

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Convert bib file(s) to dvi'''
p = optparse.OptionParser(usage)
p.add_option('--xdvi', dest='xdvi', action='store_true',
             help='launch xdvi when done')
p.add_option('--bibstyle', dest='bibstyle', action='store', type='str',
             help='specify a bibliography style file')
p.set_defaults(xdvi=False, bibstyle='ieeetr', resolve=False)
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

if args:
    # a list of files is given, temp file is the same root name as the first argument
    texfile = args[0]
    texfile = texfile[0:string.rindex(texfile, '.bib')]
    bibfiles = ','.join( [os.path.splitext(x)[0] for x in args] )
else:
    # input from stdin, use stdin as the root filename
    texfile = 'stdin'
    fp = open(texfile+'.bib', 'w')
    bib.write(file=fp,resolve=resolve)
    fp.close()
    bibfiles = 'stdin'

print "Saving to", texfile


## create the latex source file
tex = open("%s.tex" % texfile, "w")

tex.write(
r"""\documentclass{article}
\begin{document}
""")

# write the cite keys
for be in bib:
    tex.write("\\nocite{%s}\n" % be.getKey())

# add the bibliog commands
tex.write(
r"""\bibliographystyle{%s}
\bibliography{strings,%s}
\end{document}
""" % (bibstyle, bibfiles) )
tex.close()

os.system("pslatex %s" % texfile)
os.system("bibtex %s" % texfile)
os.system("pslatex %s" % texfile)

if xdvi and os.getenv('DISPLAY'):
    os.system("xdvi %s" % texfile)
