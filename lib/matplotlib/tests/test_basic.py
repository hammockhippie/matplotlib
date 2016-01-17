from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from matplotlib.externals import six


from pylab import *
import pytest


def test_simple():
    assert 1 + 1 == 2


@pytest.mark.xfail
def test_simple_knownfail():
    # Test the known fail mechanism.
    assert 1 + 1 == 3


def test_override_builtins():
    ok_to_override = set([
        '__name__',
        '__doc__',
        '__package__',
        '__loader__',
        '__spec__',
        'any',
        'all',
        'sum'
    ])

    # We could use six.moves.builtins here, but that seems
    # to do a little more than just this.
    if six.PY3:
        builtins = sys.modules['builtins']
    else:
        builtins = sys.modules['__builtin__']

    overridden = False
    for key in globals().keys():
        if key in dir(builtins):
            if (globals()[key] != getattr(builtins, key) and
                    key not in ok_to_override):
                print("'%s' was overridden in globals()." % key)
                overridden = True

    assert not overridden
