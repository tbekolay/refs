import sys

# Only test for Python 2 so that we have less changes for Python 4
PY2 = sys.version_info[0] == 2

if PY2:
    string_types = (str, unicode)
    int_types = (int, long)
    range = xrange
else:
    string_types = (str,)
    int_types = (int,)
    range = range


def is_integer(obj):
    return isinstance(obj, int_types)


def is_iterable(obj):
    return isinstance(obj, collections.Iterable)


def is_string(obj):
    return isinstance(obj, string_types)
