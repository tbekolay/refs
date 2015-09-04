import os
import sys

import click

from . import BibEntry, Bibliography


class Refs(object):
    def __init__(self, master=None, debug=False):
        self.master = os.path.abspath(master)  # Should ensure it exists
        self.debug = debug


@click.group()
@click.option('--master', default='~/master.bib')
@click.option('--debug', is_flag=True)
@click.pass_context
def main(ctx, master, debug):
    ctx.obj = Refs(master, debug)


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
    bib = Bibliography.Bibliography()
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
    bib = Bibliography.Bibliography()
    bib.load_bibtex(bibliography)
    bib.sort()

    if overwrite:
        with open(bibliography, 'w') as fp:
            bib.write_bibtex(fp)
    else:
        bib.write_bibtex(sys.stdout)


if __name__ == '__main__':
    main()
