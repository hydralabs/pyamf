# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Adapter for the stdlib C{sets} module.

@since: 0.4
"""

import sets

import pyamf

def to_tuple(x):
    return tuple(x)

if hasattr(sets, 'ImmutableSet'):
    pyamf.add_type(sets.ImmutableSet, to_tuple)

if hasattr(sets, 'Set'):
    pyamf.add_type(sets.Set, to_tuple)
