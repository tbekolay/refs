import os
import sys

import click

from .compat import range
from .core import Bibliography
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
@click.option('--limit', default=10, type=int)
@click.argument('query')
@click.pass_obj
def search(refs, query, limit):
    """Search for a reference."""
    items = _search(query, refs.m_id, refs.m_secret).iter(page_size=limit)

    for i, item in enumerate(items):
        click.echo(item.title)
        click.echo(item.id)

        if i > limit:
            click.echo("over limit")
            break
    #     click.echo(items[i][u'title'][0])
    #     if u'DOI' in items[i]:
    #         click.echo("DOI: %s" % items[i][u'DOI'])

    # click.echo("DEBUG: other info")
    # click.echo(items[0].keys())




if __name__ == '__main__':
    main()
