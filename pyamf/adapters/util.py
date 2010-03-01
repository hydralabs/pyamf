# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Useful helpers for adapters.

:since: 0.4
"""

import __builtin__

if not hasattr(__builtin__, 'set'):
    from sets import Set as set


def to_list(obj, encoder):
    """
    Converts an arbitrary object `obj` to a list.

    :rtype: `list`
    """
    return list(obj)


def to_dict(obj, encoder):
    """
    Converts an arbitrary object `obj` to a dict.

    :rtype: `dict`
    """
    return dict(obj)


def to_set(obj, encoder):
    """
    Converts an arbitrary object `obj` to a set.

    :rtype: `set`
    """
    return set(obj)


def to_tuple(x, encoder):
    """
    Converts an arbitrary object `obj` to a tuple.

    :rtype: `tuple`
    """
    return tuple(x)

def to_string(x, encoder):
    """
    Converts an arbitrary object `obj` to a string.

    :rtype: `tuple`
    :since: 0.5
    """
    return str(x)
