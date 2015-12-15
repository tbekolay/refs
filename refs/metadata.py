"""Query databases for reference metadata."""

import hashlib
import json
import sys
import urllib

import mendeley.models.catalog
import requests
import requests.auth

from .core import Entry
from .rc import rc

def search(query, m_id, m_secret):
    mend = mendeley.Mendeley(m_id, m_secret)
    session = mend.start_client_credentials_flow().authenticate()
    if query.startswith("10.") and "/" in query:
        # Interpreting as a DOI
        return session.catalog.by_identifier(doi=query, view='bib')
    elif query.endswith(".pdf"):
        # Interpreting as a file
        filehash = sha1hash(query)
        try:
            return session.catalog.by_identifier(filehash=filehash, view='bib')
        except mendeley.exception.MendeleyException:
            # Let's not show tracebacks here
            sys.tracebacklimit = 0
            raise NotImplementedError(
                "That file not in Mendeley's catalog. Parsing PDFs for "
                "metadata not implemented yet.")
    else:
        return session.catalog.search(query, view='bib')


def sha1hash(path):
    with open(path, 'rb') as f:
        sha1 = hashlib.sha1(f.read()).hexdigest()
    return sha1



def doc2bib(mdoc, bib=None):
    """Converts a mendeley.CatalogBibView to an Entry."""
    assert isinstance(mdoc, mendeley.models.catalog.CatalogBibView)

    # Map from Mendeley type to BibTeX type
    type2reftype = {
        'journal': 'article',
        'book': 'book',
        'generic': 'misc',
        'book_section': 'inbook',
        'conference_proceedings': 'inproceedings',
        'working_paper': 'unpublished',
        'report': 'techreport',
        'web_page': 'misc',
        'thesis': 'phdthesis',
        'magazine_article': 'misc',
        'statute': 'misc',
        'patent': 'misc',
        'newspaper_article': 'misc',
        'computer_program': 'misc',
        'hearing': 'misc',
        'television_broadcast': 'misc',
        'encyclopedia_article': 'misc',
        'case': 'misc',
        'film': 'misc',
        'bill': 'misc',
    }

    key = "%s%s" % (mdoc.authors[0].last_name.lower(), mdoc.year)
    entry = Entry(key, bib=bib)
    entry.reftype = type2reftype[mdoc.type]
    for field in entry.allfields:
        if field == 'journal':
            val = getattr(mdoc, 'source')
            if val is not None:
                entry.set(field, val)

        if hasattr(mdoc, field):
            if field == "type" and entry.reftype != "techreport":
                continue
            val = getattr(mdoc, field)
            if val is not None:
                entry.set(field, val)
    return entry
