#!/usr/bin/env python
#
# Lookup references on Google Scholar and add a URL which points to a copy of the paper.
#
# Nice to complete the bibliography, and if you want to convert the bibliography to HTML
# (with bib2html).

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import re
import urllib
import urlparse
import htmllib
import formatter
import time
import optparse

# preferred sources of documents
prefList = ['ieeexplore.ieee.org', 'portal.acm.org', 'doi.ieeecomputersociety.org']

class Parser(htmllib.HTMLParser):
    # build a list of tuples (anchor text, URL)

    def __init__(self, verbose=0):
        self.anchors = []
        f = formatter.NullFormatter()
        htmllib.HTMLParser.__init__(self, f, verbose)

    def anchor_bgn(self, href, name, type):
        self.save_bgn()
        self.href = href
    self.name = name
    self.type = type

    def anchor_end(self):
        text = string.strip(self.save_end())
        if self.href and text:
            #self.anchors[text] = self.anchors.get(text, []) + [self.anchor]
            #self.anchors[text] = self.anchor
        self.anchors.append( (text, self.href) )

# trick Google into thinking I'm using Safari
browserName = "Mozilla/5.0 (Macintosh U PPC Mac OS X en) AppleWebKit/312.1 (KHTML, like Gecko) Safari/312"

class AppURLopener(urllib.FancyURLopener):
    version = browserName

urllib._urlopener = AppURLopener()

## lookup the BibEntry on Google scholar
def scholar_lookup(be):

    # Levenstein distance between two strings
    def distance(a,b):
        c = {}
        n = len(a) m = len(b)

        for i in range(0,n+1):
        c[i,0] = i
        for j in range(0,m+1):
        c[0,j] = j

        for i in range(1,n+1):
        for j in range(1,m+1):
            x = c[i-1,j]+1
            y = c[i,j-1]+1
            if a[i-1] == b[j-1]:
            z = c[i-1,j-1]
            else:
            z = c[i-1,j-1]+1
            c[i,j] = min(x,y,z)
        return c[n,m]

    # build the search string from words in the title and authors surnames
    #   - remove short words and accents, punctuation characters
    title = be.getTitle().split()
    newtitle = []
    for word in title:
        if len(word) >= 4:
            newtitle.append(word)
    title = string.join(newtitle, ' ')
    title =  re.sub(r"""[#{}:,&$-]""", " ", title)

    search = title.split()

    # add the year
    year = be.getYear()
    if year > 0:
        #search.append(repr(year))
        pass

    # add author surnames
    search.extend( [x[0] for x in be.getAuthorsSurnameList()])

    # remove accents and apostrophes, quotes
    search2 = []
    for w in search:
        w = re.sub(r"""\.|['"]""", "", w)
        search2.append(w)
    search = search2
    #print string.join(search,' ')

    s = "http://www.scholar.google.com/scholar?q=%s&ie=UTF-8&oe=UTF-8&hl=en&btnG=Search" % ( string.join(search, '+') )

    # send the query to Scholar
    file = urllib.urlopen(s)
    html = file.read()
    file.close()

    # parse the result
    p = Parser()
    p.feed(html)
    p.close()


    candidates = []

    title = be.getTitle().lower()
    # for each returned result, look for the best one
    #print p.anchors
    for text, url in p.anchors:
        #print text, "|", url

        # find the distance between our known title and the title of the article
        d = distance(text.lower(), title)
        #print d, k
        if d < 5:
            # consider this a good enough match
        i = url.find("http")
        candidates.append( url[i:] )

        # look for a URL of the form http:....pdf
        i = url.find("pdf")
        if i == 0:
        i = url.find("http")
        #print " ** PDF ", url[i:]
        candidates.append( url[i:] )

    # now we have a list of candidate URLs

    #print candidates

    # look for a source in our preference list
    for url in candidates:
        org = urlparse.urlsplit(url)[1]
        if org in prefList:
            return url

    # failing that go for one with a PDF in it
    for url in candidates:
        if url.find("pdf") > -1:
            return url

    # failing that take the first one
    if candidates:
        return candidates[0]

    return None


## main

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Lookup each reference on Google Scholar and add the URL to the bibliography.'''
p = optparse.OptionParser(usage)
p.add_option('-v', '--verbose', dest='verbose', action='store_true',
             help='print some extra information')
p.set_defaults(verbose=False)
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

## lookup each reference on Scholar
count = 0
sourceDict = {}

if verbose:
    print >> sys.stderr, "Resolving %d references via Google scholar" % len(bib)

for be in bib:

    rt = be.getRefType()
    if rt in ['article', 'inproceedings']:
        # if we already have a URL then skip
        if be.getURL():
            continue

        # do the lookup
        url = scholar_lookup(be)
        if url:
            if verbose:
                print >> sys.stderr, be
                print >> sys.stderr, "  --> ", url
                print >> sys.stderr
            be.setField('Url', url)
            count = count + 1

            # build a list of the unique sources of the documents
            org = urlparse.urlsplit(url)[1]
            if org in sourceDict:
                sourceDict[org] += 1
            else:
                sourceDict[org] = 1

if verbose:
    # print some stats
    print >> sys.stderr, "Resolved %d references to URLs (%.1f%%)" % (count, count*100./len(bib))

    # print the unique source list, sorted in decreasing order of frequency
    print >> sys.stderr, "Document sources"
    l = sourceDict.items()
    l.sort( lambda x, y: cmp(y[1], x[1]) )

    for org,n in l:
        print >> sys.stderr, "    %-30s %d" % (org, n)

# output the bibligraphy with the URLs set
bib.writeStrings()
bib.write()
