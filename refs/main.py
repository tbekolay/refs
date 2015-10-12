import os
import sys

import click
import mendeley.resources.catalog

from .compat import iteritems, range
from .core import Bibliography
from .metadata import doc2bib
from .metadata import search as _search
from .rc import rc


class Refs(object):
    def __init__(self, master='', m_id='', m_secret=''):
        if master == '':
            master = rc.get('general', 'master')
        self.master = os.path.abspath(master)
        self.m_id = m_id if m_id != '' else rc.get('mendeley', 'client_id')
        self.m_secret = (m_secret if m_secret != ''
                         else rc.get('mendeley', 'client_secret'))


@click.group()
@click.option('--master', default='')
@click.option('--mendeley_id', default='')
@click.option('--mendeley_secret', default='')
@click.pass_context
def main(ctx, master, mendeley_id, mendeley_secret):
    ctx.obj = Refs(master, mendeley_id, mendeley_secret)


@main.command()
@click.option('--brief', is_flag=True,
              help="brief listing (one line per entry)")
@click.option('--abbrev', is_flag=True,
              help="resolve abbreviations from defined strings")
@click.option('--resolve', is_flag=True,
              help="resolve cross reference entries")
@click.argument('bibliography')
@click.pass_obj
def list(refs, bibliography, brief, abbrev, resolve):
    """Print bibliography in readable format."""
    # TODO handle multiple bibs?
    bib = Bibliography()
    bib.load_bibtex(bibliography)

    if abbrev:
        bib.resolve_abbrev()
    if resolve:
        bib.resolve_crossref()

    # output the readable text
    for bibentry in bib:
        if brief:
            bibentry.brief()
        else:
            bibentry.display()
        print


@main.command()
@click.option('--overwrite', is_flag=True,
              help="overwrite bibliography with sorted version")
@click.argument('bibliography')
@click.pass_obj
def sort(refs, bibliography, overwrite):
    """Sort bibliography by citekey."""
    bib = Bibliography()
    bib.load_bibtex(bibliography)
    bib.sort()

    if overwrite:
        with open(bibliography, 'w') as fp:
            bib.write_bibtex(fp)
    else:
        bib.write_bibtex(sys.stdout)


@main.command()
@click.option('--abstract', is_flag=True,
              help="include the abstract, if available.")
@click.argument('query')
@click.pass_obj
def search(refs, query, abstract):
    """Search for a reference."""

    result = _search(query, refs.m_id, refs.m_secret)

    if isinstance(result, mendeley.resources.catalog.CatalogSearch):

        for i, item in enumerate(result.iter()):
            click.echo(item.title)
            if item.identifiers is not None:
                for ident, identval in iteritems(item.identifiers):
                    click.echo("  %s: %s" % (ident, identval))

            result = item
            break

            # TODO: show search results, prompt user for which one to choose
            #
            # if i > 100:
            #     click.echo("Not found in 100 search results. Giving up.")
            #     return

    entry = doc2bib(result)
    if not abstract:
        del entry.fieldDict['abstract']
    entry.write_bibtex(sys.stdout)


if __name__ == '__main__':
    main()
