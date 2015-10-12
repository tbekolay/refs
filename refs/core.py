# Bibliography entry class
#   - holds all information about one bibliographic item
#   - provides methods for manipulating/setting/representing that information
#
# TODO:
#    __repr__ method needs to do a better job depending on the reference type,
#    similar logic is required in bib2html (but it's not their either...)
#
# Bibliography class
#   - essentially a container for many BibEntry objects
#   - provides methods for reading/writing the bibliography
#   - provides iterators, sorting etc
#
# TODO add __enter__ and __exit__ to make a context manager

import logging
import re
import os.path
import string
import sys
import urllib
import urlparse
import warnings

from .compat import is_integer, is_iterable, is_string, range
from .utils import english_join, fuzzymatch, mogrify


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


class Entry(object):

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

    allfields = ('_reftype',
                 'address',
                 'author',
                 'booktitle',
                 'chapter',
                 'edition',
                 'editor',
                 'howpublished',
                 'institution',
                 'journal',
                 'month',
                 'number',
                 'organization',
                 'pages',
                 'publisher',
                 'school',
                 'series',
                 'title',
                 'type',
                 'volume',
                 'year',
                 'note',
                 'code',
                 'url',
                 'crossref',
                 'annote',
                 'abstract',
                 'date-added',
                 'date-modified',
                 'read',
                 'doi')

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
        print(self)

    def display(self):
        r = "%12s: %s\n" % ("CiteKey", self.key)
        for k in self.fieldDict:
            if k[0] == '_':
                continue
            if k == 'Author':
                r += "%12s: %s\n" % (k, self.authors)
            else:
                r += "%12s: %s\n" % (k, self.fieldDict[k])
        print(r)

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
            raise AttributeError("[%s] Bad reference type '%s'" % (
                self.key, value))
        self.fieldDict['Type'] = value

    def set(self, key, value):
        def _strip(s):
            s = s.strip(' ')
            if (s[0] == '"') and (s[-1] == '"'):
                return s[1:-1]
            if (s[0] == '{') and (s[-1] == '}'):
                return s[1:-1]
            return s

        if key not in self.allfields:
            raise AttributeError, "[%s] Field '%s' not recognized" % (
                self.key, key)

        if key in ("Author", "Editor"):
            value = value.split(" and ")
            value = [_strip(v) for v in value]

        if key == 'Year':
            self.year = value
        elif key == 'Month':
            self.month = month
        else:
            self.fieldDict[key] = value

    def write_bibtex(self, fp=sys.stdout):
        """Write a BibTex format entry."""
        fp.write("@%s{%s,\n"  % (self.reftype, self.key))
        count = 0
        for rk in self.fieldDict:
            count += 1
            # skip internally used fields
            if rk[0] == '_':
                continue
            if rk == 'Type':
                continue

            # generate the entry
            value = self.fieldDict[rk]
            fp.write("  %s=" % rk)

            if rk in ['Author', 'Editor']:
                fp.write("{%s}" % " and ".join(value))
            elif rk == 'Month':
                if value:
                    fp.write("{%s}" % value)
                else:
                    value = self.month_name
                    fp.write("%s" % value[:3].lower())
            else:
                # is it an abbrev?
                if (self.bibliography is not None
                    and value in self.bibliography.abbrevs):
                    fp.write("%s" % value)
                else:
                    fp.write("{%s}" % value)

            # add comma to all but last fields
            if count < len(self.fieldDict):
                fp.write(",\n")
            else:
                fp.write("\n")
        fp.write("}\n")

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


class Bibliography(object):
    def __init__(self):
        self.bibentries = []
        self.abbrevs = {}
        self.stringDict = {}

    def open(self, path_or_url):
        if path_or_url == '-':
            self.filename = "stdin"
            return sys.stdin
        urlbits = urlparse.urlparse(path_or_url)
        if urlbits.scheme:
            fp = urllib.urlopen(path_or_url)
            self.filename = path_or_url
        else:
            fp = open(path_or_url, "r")
            home = os.path.expanduser('~')
            f2 = os.path.abspath(path_or_url)
            common = os.path.commonprefix([home, f2])
            if common:
                self.filename = "~" + f2[len(common):]
            else:
                self.filename = path_or_url
        return fp

    def close(self, fp):
        fp.close()

    @property
    def keys(self):
        return [x.key for x in self.bibentries]

    def resolve_abbrev(self):
        """Resolve all abbreviations found in value fields."""
        for entry in self:
            for field in entry:
                v = entry.get(f)
                if is_string(v):
                    if v in self.abbrevs:
                        if self.abbrevs[v]:
                            entry.setField(f, self.abbrevs[v])

    def insert_entry(self, entry):
        if not isinstance(entry, Entry):
            raise TypeError("Can only insert Entry instances.")
        if entry.key in self.keys:
            raise ValueError(
                "key %s already exists. Please change the key." % entry.key)
        self.bibentries.append(entry)

    def insert_abbrev(self, abbrev, value):
        if abbrev in self.abbrevs:
            raise ValueError("abbrev %s already exists." % abbrev)
        self.abbrevs[abbrev] = value

    def brief(self):
        for entry in self:
            entry.brief()

    def display(self):
        for entry in self:
            entry.display()

    def __contains__(self, key):
        return key in self.keys

    def __getitem__(self, idx):
        if is_string(idx):
            return self.bibentries[self.keys.index(idx)]
        elif is_integer(idx):
            return self.bibentries[idx]
        raise KeyError("Can only index in with strings or integers.")

    def __len__(self):
        return len(self.bibentries)

    def sort(self):
        """Sort entries by key."""
        self.bibentries.sort(key=lambda be: be.key)

    def search(self, key, target, reftype="all", ignorecase=True):
        if target == '*':
            return self.bibentries

        result = []
        for entry in self:
            if ((reftype.lower() == 'all' or entry.reftype == reftype)
                    and entry.search(key, target, ignorecase)):
                result.append(entry)
        return result

    def load_bibtex(self, path_or_url=None, ignore=False):
        if path_or_url == None:
            fp = sys.stdin
        else:
            fp = self.open(path_or_url)

        # get the file into one huge string
        nbib = 0
        s = fp.read()
        return self.loads_bibtex(s, ignore=ignore)

    def loads_bibtex(self, s, ignore=False):
        class BibLexer(object):
            """Lexical analyzer for bibtex format files."""
            def __init__(self, s):
                self.in_str = s  # the string to parse
                self.linenum = 1
                self.pos = 0

            def next(self):
                """Iterator for the class, return next character."""
                if self.pos >= len(self.in_str):
                    raise StopIteration
                c = self.in_str[self.pos]
                if c == '\n':
                    self.linenum += 1
                self.pos += 1
                return c

            def __iter__(self):
                return self

            def peek(self):
                """Peek at the next character."""
                return self.in_str[self.pos]

            def pushback(self, c):
                """Push a character back onto the input."""
                self.pos -= 1
                if c == '\n':
                    self.linenum -= 1

            def skipwhite(self):
                """Eat whitepsace characters and comments."""
                for c in self:
                    if c == '%':
                        for c in self:
                            if c == '\n':
                                break
                    elif not c.isspace():
                        self.pushback(c)
                        break

            def show(self):
                print >> sys.stderr, "[%c]%s" % (
                    self.in_str[0], self.in_str[1:10])

            def nextword(self):
                """Get the next word from the input stream.

                A word can be:
                - [alpha][alnum$_-]
                - "...."
                - {....}
                """
                word = ""
                c = self.peek()

                if c == '"':
                    # quote delimited string
                    word = self.next()
                    cp = None  # prev char
                    for c in self:
                        word += c
                        if c == '"' and cp != '\\':
                            break
                        cp = c
                elif c == '{':
                    # brace delimited string
                    count = 0
                    for c in self:
                        if c == '{':
                            count += 1
                        if c == '}':
                            count -= 1

                        word += c
                        if count == 0:
                            break
                else:
                    # undelimited string
                    for c in self:
                        if c.isalnum():
                            word += c
                        elif c in ".+-_$:'":
                            word += c
                        else:
                            self.pushback(c)
                            break
                return word

        class Token(object):
            ENTRY = 1
            DELIM_L = 2
            DELIM_R = 3
            STRING = 5
            EQUAL = 6
            COMMA = 7

            def __init__(self, val=None, typ=None):
                self.val = val
                self.typ = typ

            def __repr__(self):
                if self.is_entry():
                    return "@ %s" % self.val
                elif self.is_delim_r():
                    return "  }"
                elif self.is_string():
                    return "<%s>" % self.val
                elif self.is_equal():
                    return "  EQUAL"
                elif self.is_comma():
                    return "  COMMA"
                else:
                    return "BAD TOKEN (%d) <%s>" % (self.typ, self.val)

            def is_string(self):
                return self.typ == self.STRING

            def is_abbrev(self):
                return self.is_string() and self.val.isalnum()

            def is_comma(self):
                return self.typ == self.COMMA

            def is_equal(self):
                return self.typ == self.EQUAL

            def is_entry(self):
                return self.typ == self.ENTRY

            def is_delim_r(self):
                return self.typ == self.DELIM_R

            def is_delim_l(self):
                return self.typ == self.DELIM_L

        class BibTokenizer(object):
            """Tokenizer for bibtex format files."""

            def __init__(self, s):
                self.lex = BibLexer(s)

            def __iter__(self):
                """Setup an iterator for the next token."""
                return self

            def next(self):
                """Return next token."""
                self.lex.skipwhite()
                c = self.lex.next()
                t = Token()

                if c == '@':
                    t.typ = t.ENTRY
                    self.lex.skipwhite()
                    t.val = self.lex.nextword()
                    self.lex.skipwhite()
                    c = self.lex.next()
                    if not (c == '{' or c == '('):
                        raise ValueError("BAD START OF ENTRY")
                elif c == ',':
                    t.typ = t.COMMA
                elif c == '=':
                    t.typ = t.EQUAL
                elif (c == '}') or (c == ')'):
                    t.typ = t.DELIM_R
                else:
                    self.lex.pushback(c)
                    t.typ = t.STRING
                    t.val = self.lex.nextword()
                return t

        class BibParser(object):
            def __init__(self, s, bt):
                self.tok = BibTokenizer(s)
                self.bibtex = bt

            def __iter__(self):
                """Set up an iterator for the next entry."""
                return self

            def next(self):
                """Return next entry."""

                def _strip(s):
                    if s[0] in '"{':
                        return s[1:-1]
                    else:
                        return s

                t = self.tok.next()
                if not t.is_entry():
                    raise SyntaxError(self.tok.lex.linenum)
                if t.val.lower() == 'string':
                    tn = self.tok.next()
                    if not tn.is_string():
                        raise SyntaxError(self.tok.lex.linenum)
                    t = self.tok.next()
                    if not t.isequal():
                        raise SyntaxError(self.tok.lex.linenum)
                    tv = self.tok.next()
                    if not tv.isstring():
                        raise SyntaxError(self.tok.lex.linenum)
                    # insert string into the string table
                    self.bibtex.insert_abbrev(tn.val, _strip(tv.val))
                    t = self.tok.next()
                    if not t.is_delim_r():
                        raise SyntaxError(self.tok.lex.linenum)
                elif t.val.lower() == 'comment':
                    depth = 0
                    while True:
                        tn = self.tok.next()
                        if t.is_delim_l():
                            depth += 1
                        if t.is_delim_r():
                            depth -= 1
                            if depth == 0:
                                break
                else:
                    # NOT A STRING or COMMENT ENTRY
                    # assume a normal reference type

                    # get the cite key
                    ck = self.tok.next()
                    if not ck.is_string():
                        raise SyntaxError(self.tok.lex.linenum)

                    entry = Entry(ck.val, self.bibtex)
                    entry.reftype = t.val

                    # get the comma
                    ck = self.tok.next()
                    if not ck.is_comma():
                        raise SyntaxError(self.tok.lex.linenum)

                    # get the field value pairs
                    for tf in self.tok:
                        # allow for poor syntax with comma before end brace
                        if tf.is_delim_r():
                            break
                        if not tf.is_string():
                            raise SyntaxError(self.tok.lex.linenum)
                        t = self.tok.next()
                        if not t.is_equal():
                            raise SyntaxError(self.tok.lex.linenum)
                        ts = self.tok.next()
                        if not ts.is_string():
                            raise SyntaxError(self.tok.lex.linenum)
                        entry.set(tf.val, _strip(ts.val))

                        # if it was an abbrev in the file, put it in the
                        # abbrevDict so it gets written as an abbrev
                        if ts.is_abbrev():
                            self.bibtex.insert_abbrev(ts.val, None)

                        t = self.tok.next()
                        if t.is_comma():
                            continue
                        elif t.is_delim_r():
                            break
                        else:
                            raise SyntaxError(self.tok.lex.linenum)

                    self.bibtex.insert_entry(entry)
                return

        bibparser = BibParser(s, self)
        bibcount = 0
        try:
            for _ in bibparser:
                bibcount += 1
                pass
        except SyntaxError as err:
            print "Syntax error at line %s" % err

        return bibcount


    def write_bibtex(self, file=sys.stdout):
        for entry in self:
            entry.write_bibtex(file)

    def write_strings(self, file=sys.stdout):
        for abbrev, value in self.abbrevDict.items():
            file.write("@string{ %s = {%s} }\n" % (abbrev, value) )

    # resolve BibTeX's cross reference capability
    def resolve_crossref(self):
        for entry in self:
            try:
                xref = self.get('crossref')
            except:
                return

            for f in xref:
                if f not in entry:
                    entry.set(f, xref.get(f))
