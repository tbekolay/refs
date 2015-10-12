import sys

# Only test for Python 2 so that we have less changes for Python 4
PY2 = sys.version_info[0] == 2

if PY2:
    import ConfigParser as configparser
    string_types = (str, unicode)
    int_types = (int, long)
    range = xrange

    # No iterkeys; use ``for key in dict:`` instead
    iteritems = lambda d: d.iteritems()
    itervalues = lambda d: d.itervalues()
else:
    import configparser
    string_types = (str,)
    int_types = (int,)
    range = range

    # No iterkeys; use ``for key in dict:`` instead
    iteritems = lambda d: iter(d.items())
    itervalues = lambda d: iter(d.values())


def is_integer(obj):
    return isinstance(obj, int_types)


def is_iterable(obj):
    return isinstance(obj, collections.Iterable)


def is_string(obj):
    return isinstance(obj, string_types)
