# Bibliography entry class
#   - holds all information about one bibliographic item
#   - provides methods for manipulating/setting/representing that information
#
# TODO:
#    __repr__ method needs to do a better job depending on the reference type,
#    similar logic is required in bib2html (but it's not their either...)
#

import logging
import re
import string
import sys
import warnings

from .compat import is_integer, is_iterable, is_string, range
from .utils import english_join, fuzzy_match, mogrify


class BibEntry(object):

    months = ('January',
              'February',
              'March',
              'April',
              'May',
              'June',
              'July',
              'August',
              'September',
              'October',
              'November',
              'December')

    validtypes = ('article',
                  'book',
                  'booklet',
                  'inbook',
                  'incollection',
                  'inproceedings',
                  'manual',
                  'mastersthesis',
                  'misc',
                  'phdthesis',
                  'proceedings',
                  'techreport',
                  'unpublished')

    allfields = ('_Reftype',
                 'Address',
                 'Author',
                 'Booktitle',
                 'Chapter',
                 'Edition',
                 'Editor',
                 'Howpublished',
                 'Institution',
                 'Journal',
                 'Month',
                 'Number',
                 'Organization',
                 'Pages',
                 'Publisher',
                 'School',
                 'Series',
                 'Title',
                 'Type',
                 'Volume',
                 'Year',
                 'Note',
                 'Code',
                 'Url',
                 'Crossref',
                 'Annote',
                 'Abstract',
                 'Date-added',
                 'Date-modified',
                 'Read')

    def __init__(self, key, bib):
        self.key = key
        self.fieldDict = {}
        self.bibliography = bib
        logging.debug("New entry %s", key)

    def __str__(self):
        r = '"%s"; ' % self.title
        try:
            r += self.author_names
        except:
            try:
                r += "eds. %s" % self.editors_names
            except:
                pass
        month = self.month_name
        year = self.year
        book = self.booktitle
        if book:
            r += ", %s" % book
        if month:
            r += ", %s" % month
            if year > 0:
                r += " %s" % year
        elif year > 0:
            r += ", %s" % year
        r += '.'
        return r

    def brief(self):
        return str(self)

    def display(self):
        r = "%12s: %s" % ("CiteKey", self.key)
        for k in self.fieldDict:
            if k[0] == '_':
                continue
            if k == 'Author':
                r += "%12s: %s" % (k, self.authors)
            else:
                r += "%12s: %s" % (k, self.fieldDict[k])
        return r

    def __getitem__(self, i):
        if is_string(i):
            return self.fieldDict[i]
        else:
            raise KeyError

    def check(self):
        keys = list(self.fieldDict)
        missing = []
        reftype = self.reftype
        if reftype not in alltypes:
            raise AttributeError("[%s] Bad reference type '%s'" % (
                self.key, reftype))
        for k in required_fields[self.reftype]:
            if k not in keys:
                missing.append(k)
        return missing

    def get(self, field, default=None):
        if field in self.fieldDict:
            return self.fieldDict[field]
        return default

    @property
    def title(self):
        if 'Title' in self.fieldDict:
            title = self.fieldDict['Title']
            title = re.sub(r"""[{}]""", "", title)
            title = title.strip('.,\'"')
            return title
        return ""

    @property
    def url(self):
        return self.get('Url', "")

    @property
    def author_list(self):
        return self.get('Author', [])

    @property
    def authors(self):
        return english_join(self.author_list)

    def surname(self, author):
        # remove LaTeX accents
        def chg(mo):
            return mo.group(mo.lastindex)

        re_accent = re.compile(r'''\\[.'`^"~=uvHcdb]\{(.)\}|\t\{(..)\}''')
        author = re_accent.sub(chg, author)

        # "surname, first names"
        m = re.search(r"""^([^,]*),(.*)""", author)
        if m:
            return [m.group(1), m.group(2).lstrip()[0]]

        # "first names surname"

        # take the last component after dot or space
        m = re.search(r"""(.*?)([^\. \t]*)$""", author)
        if m:
            return [m.group(2), m.group(1)[0]]

        return ""

    @property
    def author_surnames_list(self):
        if 'Author' in self.fieldDict:
            return [self.surname(l) for l in self.fieldDict['Author']]
        return []

    @property
    def author_surnames(self):
        l = self.author_surnames_list
        try:
            return english_join([x[0] for x in l])
        except:
            return ""

    @property
    def author_names(self):
        l = self.author_surnames_list
        l = ["%s. %s" % (x[1], x[0]) for x in l]
        return english_join(l)

    @property
    def editor_surnames_list(self):
        if 'Editor' in self.fieldDict:
            return [self.surname(l) for l in self.fieldDict['Editor']]
        return []

    @property
    def editor_names(self):
        return english_join(["%s. %s" % (x[1], x[0])
                             for x in self.editor_surnames_list])

    @property
    def booktitle(self):
        return self.get('Booktitle', "")

    @property
    def volume(self):
        return self.get('Volume', -1)

    @property
    def number(self):
        return self.get('Number', -1)

    @property
    def pages(self):
        return self.get('Pages', "")

    def after(self, year, month=None):
        """True if the entry occurs after the specified date."""
        if month is None:
            return self.year >= year
        if self.year > year:
            return True
        return self.year == year and self.month >= month

    def before(self, year, month=None):
        """True if the entry occurs before the specified date."""
        if month is None:
            return self.year < year
        if self.year < year:
            return True
        return self.year == year and self.month < month

    @property
    def year(self):
        return self.get('_year', -1)

    @year.setter
    def year(self, value):
        self.fieldDict['Year'] = value
        # remove all text like "to appear", just leave the digits
        year = ''.join([c for c in value if c.isdigit()])
        try:
            self.fieldDict['_year'] = int(year)
        except ValueError:
            warnings.warn("[%s] cannot parse year; got '%s'", self.key, value)
            self.fieldDict['_year'] = -1

    @property
    def month(self):
        """Month is an ordinal in range 1 to 12."""
        return self.get('_month', -1)

    @month.setter
    def month(self, value):
        # the Month entry has the original string from the file if it is of
        # nonstandard form, else is None.
        # the hidden entry _month has the ordinal number
        self.fieldDict['Month'] = value
        month = mogrify(value)
        for monthname in self.months:
            if (month.lower() in monthname.lower()
                    or month.find(monthname) >= 0):
                self.fieldDict['_month'] = self.months.index(monthname) + 1
            warnings.warn("[%s] cannot parse month; got '%s'", self.key, value)

    @property
    def month_name(self):
        m = self.month
        if m > 0:
            return self.months[m - 1]
        else:
            return ""

    @property
    def reftype(self):
        return self.fieldDict['Type']

    @reftype.setter
    def reftype(self, value):
        value = value.lower()
        if value not in self.validtypes:
            raise AttributeError, "bad reference type [%s]" % self.getKey()
        self.reftype = value
        self.fieldDict['Type'] = value

    def set(self, key, value):
        if key not in self.allfields:
            raise AttributeError, "[%s] Field '%s' not recognized" % (
                self.key, key)

        if key == 'Year':
            self.year = value
        elif key == 'Month':
            self.month = month
        else:
            self.fieldDict[key] = value

    def search(self, target, field="all", ignorecase=True):
        def _search(field):
            if field not in self.fieldDict:
                warnings.warn("Field '%s' not present." % field)
                return False
            s = self.fieldDict[field]
            if is_iterable(s):
                s = ' '.join(s)
            if s:
                args = (target, s) + (re.IGNORECASE,) if ignorecase else ()
                m = re.search(*args)
                if m:
                    return True

        if field.lower() == 'all':
            for k in self.fieldDict:
                if k[0] == '_':
                    continue
                if _search(k):
                    return True
            return False

        return _search(field)

    def match_author_list(self, other):

        def split(author):
            return re.findall(r"""([a-zA-Z][a-zA-Z-]*[.]?)""", author)

        def matchfrag(frag1, frag2):
            dot1 = frag1[-1:] == '.'
            dot2 = frag2[-1:] == '.'

            if (dot1 and dot1) or (not dot1 and not dot2):
                # Both or neither are abbreviated
                return frag1 == frag2
            elif dot1:
                # frag1 is abbreviated
                m = re.match("%s*" % frag1, frag2)
                return m is not None and m.group(0) == frag1
            elif dot2:
                # frag2 is abbreviated
                m = re.match("%s*" % frag2, frag1)
                return m is not None and m.group(0) == frag2

        def match_author(author1, author2):
            count = 0
            for frag1 in split(author1):
                for frag2 in split(author2):
                    if matchfrag(frag1, frag2):
                        count += 1
            return count

        # check if each article has the same number of authors
        authors1 = self.author_list
        authors2 = other.author_list
        if len(authors1) != len(authors2):
            return False

        # now check the authors match, in order
        for author1, author2 in zip(authors1, authors2):
            if match_author(author1, author2) < 2:
                return False
        return True

    def match_title(self, other, thresh):

        def distance(a, b):
            """Levenshtein distance between two strings."""
            c = {}
            n = len(a)
            m = len(b)

            for i in range(n + 1):
                c[i, 0] = i
            for j in range(m + 1):
                c[0, j] = j

            for i in range(1, n + 1):
                for j in range(1, m + 1):
                    x = c[i - 1, j] + 1
                    y = c[i, j - 1] + 1
                    if a[i - 1] == b[j - 1]:
                        z = c[i - 1, j - 1]
                    else:
                        z = c[i - 1, j - 1] + 1
                    c[i,j] = min(x, y, z)
            return c[n, m]

        return distance(mogrify(self.title), mogrify(be.title)) <= dthresh

    def match_type(self, other):
        return self.reftype == other.reftype

    def match_year(self, other):
        return fuzzymatch(self.year, other.year)

    def match_month(self, other):
        return fuzzymatch(self.month, other.month)

    def match_volume_number(self, other):
        return (fuzzymatch(self.volume, other.volume)
                and fuzzymatch(self.number, other.number))

    def match_pages(self, other):
        p1, p2 = self.page, other.page
        if not p1 or not p2:
            return True

        p1 = re.findall("([0-9.]+)", p1)
        p2 = re.findall("([0-9.]+)", p2)
        if len(p1) > 0 and len(p2) > 0:
            # optionally compare starting page numbers
            if p1[0] != p2[0]:
                return False
        if len(p1) > 1 and len(p2) > 1:
            # optionally compare ending page numbers
            if p1[-1] != p2[-1]:
                return False
        return True

    def match(self, other, dthresh=2):
        # We do the cheapest comparisons first
        if not self.match_type(other):
            return False
        if not self.match_year(other):
            return False
        if not self.match_month(other):
            return False
        if self.reftype.lower() == "article":
            if not self.match_volume_number(other):
                return False
        if not self.match_page(other):
            return False
        if not self.match_author_list(other):
            return False
        if not self.match_title(other, dthresh):
            return False
        return True


# lists of required and optional fields for each reference type
required_fields = {
  'article': ('Author', 'Title', 'Journal', 'Year'),
  'book': ('Author', 'Title', 'Publisher', 'Year'),
  'booklet': ('Title',),
  'inbook': ('Author', 'Title', 'Chapter', 'Pages', 'Publisher', 'Year'),
  'incollection': ('Author', 'Title', 'Booktitle', 'Publisher', 'Year'),
  'inproceedings': ('Author', 'Title', 'Booktitle', 'Year'),
  'manual': ('Title',),
  'misc': (),
  'mastersthesis': ('Author', 'Title', 'School', 'Year'),
  'phdthesis': ('Author', 'Title', 'School', 'Year'),
  'proceedings': ('Title', 'Year'),
  'techreport': ('Author', 'Title', 'Institution', 'Year'),
  'unpublished': ('Author', 'Title', 'Note'),
}

optional_fields = {
  'article': ('Volume', 'Number', 'Pages', 'Month', 'Note'),
  'book': ('Editor', 'Volume', 'Number', 'Series', 'Address', 'Edition',
           'Month', 'Note'),
  'booklet': ('Author', 'Howpublished', 'Address', 'Month', 'Year', 'Note'),
  'inbook': (
      'Editor', 'Volume', 'Series', 'Address', 'Edition', 'Month', 'Note'),
  'incollection': ('Editor', 'Volume', 'Number', 'Series', 'Type', 'Chapter',
                   'Pages', 'Address', 'Edition', 'Month', 'Note'),
  'inproceedings': ('Editor', 'Pages', 'Organization', 'Publisher',
                    'Address', 'Month', 'Note'),
  'manual': (
      'Author', 'Organization', 'Address', 'Edition', 'Month', 'Year', 'Note'),
  'misc': ('Title', 'Author', 'Howpublished', 'Month', 'Year', 'Note'),
  'mastersthesis': ('Address', 'Month', 'Note'),
  'phdthesis': ('Address', 'Month', 'Note'),
  'proceedings': (
      'Editor', 'Publisher', 'Organization', 'Address', 'Month', 'Note'),
  'techreport': ('Type', 'Number', 'Address', 'Month', 'Note'),
  'unpublished': ('Month', 'Year'),
}

# list of additional fields, ignored by the standard BibTeX styles
ignored_fields = ('crossref', 'code', 'url', 'annote', 'abstract')
