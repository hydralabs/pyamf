# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
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
Compatibility classes/functions for Flex.

@note: Not available in ActionScript 1.0 and 2.0.
@see: U{Flex on Wikipedia (external)
<http://en.wikipedia.org/wiki/Adobe_Flex>}

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import pyamf

__all__ = ['ArrayCollection', 'ObjectProxy']

class ArrayCollection(dict):
    """
    I represent the ActionScript 3 based class
    C{flex.messaging.io.ArrayCollection} used in the Flex framework.

    The ArrayCollection class is a wrapper class that exposes an Array
    as a collection that can be accessed and manipulated using the
    methods and properties of the C{ICollectionView} or C{IList}
    interfaces in the Flex framework.

    @see: U{ArrayCollection on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/collections/ArrayCollection.html>}
    """

    def __repr__(self):
        return "<flex.messaging.io.ArrayCollection %s>" % dict.__repr__(self)

    def __readamf__(self, input):
        data = input.readObject()

        if hasattr(data, 'iteritems'):
            for (k, v) in data.iteritems():
                self[k] = v
        else:
            count = 0
            for i in data:
                self[count] = i
                count += 1

    def __writeamf__(self, output):
        output.writeObject(dict(self), use_references=False)

pyamf.register_class(ArrayCollection, 'flex.messaging.io.ArrayCollection',
    read_func=ArrayCollection.__readamf__,
    write_func=ArrayCollection.__writeamf__)

class ObjectProxy(object):
    """
    I represent the ActionScript 3 based class C{flex.messaging.io.ObjectProxy}
    used in the Flex framework.

    @see: U{ObjectProxy on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/utils/ObjectProxy.html>}
    """

    def __init__(self, object=None):
        self._amf_object = object

    def __repr__(self):
        return "<flex.messaging.io.ObjectProxy %s>" % self._amf_object

    def __getattr__(self, name):
        if name == '_amf_object':
            return self._amf_object

        return getattr(self._amf_object, name)

    def __setattr__(self, name, value):
        if name == '_amf_object':
            self.__dict__['_amf_object'] = value
        else:
            return setattr(self._amf_object, name, value)

    def __readamf__(self, input):
        self._amf_object = input.readObject()

    def __writeamf__(self, output):
        output.writeObject(self._amf_object)

pyamf.register_class(ObjectProxy, 'flex.messaging.io.ObjectProxy',
    read_func=ObjectProxy.__readamf__,
    write_func=ObjectProxy.__writeamf__)
