# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Thijs Triemstra
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Contains compatibility classes/functions for Python -> Flex and vice versa
"""

import pyamf

class ArrayCollection(dict):
    """
    I represent a AS3 based class flex.messaging.io.ArrayCollection
    """

    def __repr__(self):
        return "<flex.messaging.io.ArrayCollection %s>" % dict.__repr__(self)

def read_ArrayCollection(obj, data):
    if hasattr(data, 'iteritems'):
        for (k, v) in data.iteritems():
            obj[k] = v
    else:
        count = 0
        for i in data:
            obj[count] = i
            count += 1   

def write_ArrayCollection(obj):
    return obj.__dict__

pyamf.register_class(ArrayCollection, 'flex.messaging.io.ArrayCollection',
    read_func=read_ArrayCollection, write_func=write_ArrayCollection)
