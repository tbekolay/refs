"""Query databases for reference metadata."""

import hashlib
import json
import urllib

import mendeley
import requests
import requests.auth

from .rc import rc

def search(query, m_id, m_secret):
    mend = mendeley.Mendeley(m_id, m_secret)
    session = mend.start_client_credentials_flow().authenticate()
    return session.catalog.search(query)


def sha1hash(path):
    with open(path, 'rb') as f:
        sha1 = hashlib.sha1(f.read()).hexdigest()
    return sha1


def doi2bib(doi, url_template="http://dx.doi.org/{}"):
    url = url_template.format(doi)

    headers = {'Accept': 'application/x-bibtex; charset=utf-8'}
    r = requests.get(url, headers=headers)
    r.encoding = "utf-8"
    r.raise_for_status()
    return r.text.strip()
