# Bibliography class
#   - essentially a container for many BibEntry objects
#   - provides methods for reading/writing the bibliography
#   - provides iterators, sorting etc
#
# TODO add __enter__ and __exit__ to make a context manager

import os.path
import sys
import urllib
import urlparse

from . import BibEntry
from .compat import is_integer, is_string


class Bibliography(object):
    def __init__(self):
        self.bibentries = []
        self.abbrevs = {}

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
            f2 = os.path.abspath(f)
            common = os.path.commonprefix([home, f2])
            if common:
                self.filename = "~" + f2[len(common):]
            else:
                self.filename = f
        return fp

    def close(self, fp):
        fp.close()

    @property
    def keys(self):
        return [x.key for x in self.bibentries]

    def resolve_abbrev(self):
        """Resolve all abbreviations found in value fields."""
        for bibentry in self:
            for field in bibentry:
                v = bibentry.get(f)
                if is_string(v):
                    if v in self.abbrevs:
                        if self.abbrevs[v]:
                            bibentry.setField(f, self.abbrevs[v])

    def insert_entry(self, bibentry):
        if not isinstance(bibentry, BibEntry):
            raise TypeError("Can only insert BibEntry instances.")
        if bibentry.key in self.keys:
            raise ValueError(
                "key %s already exists. Please change the key." % bibentry.key)
        self.bibentries.append(bibentry)

    def insert_abbrev(self, abbrev, value):
        if abbrev in self.abbrevs:
            raise ValueError("abbrev %s already exists." % abbrev)
        self.abbrevs[abbrev] = value

    def brief(self):
        for bibentry in self:
            bibentry.brief()

    def display(self):
        for bibentry in self:
            bibentry.display()

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
        for bibentry in self:
            if ((reftype.lower() == 'all' or bibentry.reftype == reftype)
                    and bibentry.search(key, target, ignorecase)):
                result.append(bibentry)
        return result
