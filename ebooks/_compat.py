"""
    Look here for more information:
    https://github.com/mitsuhiko/flask/blob/master/flask/_compat.py
"""
import sys

PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    string_types = (str,)
    unicode_type = str
    integer_types = (int,)

    iterrange = range
    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

else:
    text_type = unicode
    string_types = (str, unicode)
    unicode_type = unicode
    integer_types = (int, long)

    iterrange = xrange
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
