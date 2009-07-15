# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
`array` adapter module.

Will convert all array.array instances to a python list before encoding. All
type information is lost (but degrades nicely).

@since: 0.5
"""

import array

import pyamf
from pyamf.adapters import util


if hasattr(array, 'array'):
    pyamf.add_type(array.ArrayType, util.to_list)
