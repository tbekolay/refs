# Defines two classes:
#
#  BibTexEntry, subclass of BibEntry, and provides all BibTeX specific methods
#  such as writing an entry to file
#
#  BibTex, a subclass of Bibliography, and provides all BibTeX specific
#  methods, in  particular a parser.

import re
import sys
import urllib

from . import BibEntry, Bibliography


class BibTeXEntry(BibEntry.BibEntry):
    def write(self, fp=sys.stdout):
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
                if value in self.bibliography.abbrevs:
                    fp.write("%s" % value)
                else:
                    fp.write("{%s}" % value)

            # add comma to all but last fields
            if count < len(self.fieldDict):
                fp.write(",\n")
            else:
                fp.write("\n")
        fp.write("}\n\n")

    def set(self, field, value):
        def _strip(s):
            s = s.strip(' ')
            if (s[0] == '"') and (s[-1] == '"'):
                return s[1:-1]
            if (s[0] == '{') and (s[-1] == '}'):
                return s[1:-1]
            return s

        # deal specially with author list, convert from bibtex X and Y to
        # a list for bibentry class
        if field.lower() in ["author", "editor"]:
            value = value.split(" and ")
            value = [_strip(v) for v in value]
        try:
            super(BibTeXEntry, self).set(field, value)
        except AttributeError as err:
            raise ValueError("%15s: bad value <%s=%s>"
                             % (self.key, field, value))

class BibTeX(Bibliography.Bibliography):
    def __init__(self):
        super(BibTeX, self).__init__()
        self.stringDict = {}

    def load(self, path_or_url=None, ignore=False):
        if path_or_url == None:
            fp = sys.stdin
        else:
            fp = self.open(path_or_url)

        # get the file into one huge string
        nbib = 0
        s = fp.read()
        try:
            nbib = self.parseString(s, ignore=ignore, verbose=verbose)
        except AttributeError, err:
            print >> sys.stderr, "Error %s" % err

        self.close(fp)
        return nbib

    def display(self):
        for be in self:
                be.display()

    def write(self, file=sys.stdout, resolve=0):
        if resolve:
            dict = self.stringDict
        else:
            dict = None

        for be in self:
                be.write(file, dict)

    def writeStrings(self, file=sys.stdout):
        for abbrev, value in self.abbrevDict.items():
                file.write("@string{ %s = {%s} }\n" % (abbrev, value) )

    # resolve BibTeX's cross reference capability
    def resolveCrossRef(self):
        for be in self:
            try:
                xfref = self.getField('crossref')
            except:
                return

            for f in xref:
                if not (f in be):
                    be.setField(f, xref.getField(f))

    def loads(self, s, ignore=False):

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
                    self.lineNum += 1
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
                    self.lineNum -= 1

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
                    return = "@ %s" % self.val
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
                    raise SyntaxError(self.tok.lex.lineNum)
                if t.val.lower() == 'string':
                    tn = self.tok.next()
                    if not tn.is_string():
                        raise SyntaxError(self.tok.lex.lineNum)
                    t = self.tok.next()
                    if not t.isequal():
                        raise SyntaxError(self.tok.lex.lineNum)
                    tv = self.tok.next()
                    if not tv.isstring():
                        raise SyntaxError(self.tok.lex.lineNum)
                    # insert string into the string table
                    self.bibtex.insert_abbrev(tn.val, _strip(tv.val))
                    t = self.tok.next()
                    if not t.is_delim_r():
                        raise SyntaxError(self.tok.lex.lineNum)
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
                        raise SyntaxError(self.tok.lex.lineNum)

                    bibentry = BibTeXEntry(ck.val, self.bibtex)
                    bibentry.reftype = t.val

                    # get the comma
                    ck = self.tok.next()
                    if not ck.is_comma():
                        raise SyntaxError(self.tok.lex.lineNum)

                    # get the field value pairs
                    for tf in self.tok:
                        # allow for poor syntax with comma before end brace
                        if tf.is_delim_r():
                            break
                        if not tf.is_string():
                            raise SyntaxError(self.tok.lex.lineNum)
                        t = self.tok.next()
                        if not t.is_equal():
                            raise SyntaxError(self.tok.lex.lineNum)
                        ts = self.tok.next()
                        if not ts.is_string():
                            raise SyntaxError(self.tok.lex.lineNum)
                        bibentry.set(tf.val, _strip(ts.val))

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
                            raise SyntaxError(self.tok.lex.lineNum)

                    self.bibtex.insertEntry(bibentry, ignore)
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
