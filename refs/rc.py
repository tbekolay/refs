"""refs configuration with refsrc files."""

import os.path

from .compat import configparser
from . import paths

# The default core RC settings.
RC_DEFAULTS = {
    'general': {
        'master': os.path.expanduser(os.path.join("~", ".refs", "master.bib")),
    },
    'mendeley': {
        'client_id': '',
        'client_secret': '',
    }
}

# The RC files in the order in which they will be read.
RC_FILES = [paths.rc['user'], paths.rc['project']]


class _RC(configparser.SafeConfigParser):
    def __init__(self):
        # configparser uses old-style classes without 'super' support
        configparser.SafeConfigParser.__init__(self)
        self.reload_rc()

    def _clear(self):
        self.remove_section(configparser.DEFAULTSECT)
        for s in self.sections():
            self.remove_section(s)

    def _init_defaults(self):
        for section, settings in RC_DEFAULTS.items():
            self.add_section(section)
            for k, v in settings.items():
                self.set(section, k, str(v))

    def reload_rc(self, filenames=None):
        """Resets the currently loaded RC settings and loads new RC files.

        Parameters
        ----------
        filenames: iterable object
            Filenames of RC files to load.
        """
        if filenames is None:
            filenames = RC_FILES

        self._clear()
        self._init_defaults()
        self.read(filenames)

# The current RC settings.
rc = _RC()
