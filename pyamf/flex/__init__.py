# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Compatibility classes/functions for Flex.

@note: Not available in ActionScript 1.0 and 2.0.
@see: U{Flex on Wikipedia (external)
<http://en.wikipedia.org/wiki/Adobe_Flex>}

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

    def __init__(self, source=None):
        if source is not None:
            if isinstance(source, (list, tuple)):
                for i in range(len(source)):
                    self[i] = source[i]
            elif isinstance(source, (dict)):
                for k, v in source.iteritems():
                    self[k] = v

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
        output.writeObject(pyamf.MixedArray(self), use_references=False)

pyamf.register_class(ArrayCollection, 'flex.messaging.io.ArrayCollection',
    metadata=['external', 'amf3'])

class ObjectProxy(object):
    """
    I represent the ActionScript 3 based class C{flex.messaging.io.ObjectProxy}
    used in the Flex framework. Flex's ObjectProxy class allows an anonymous,
    dynamic ActionScript Object to be bindable and report change events.

    @see: U{ObjectProxy on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/utils/ObjectProxy.html>}
    """

    def __init__(self, object=None):
        if object is None:
            self._amf_object = pyamf.ASObject()
        else:
            self._amf_object = object

    def __repr__(self):
        return "<flex.messaging.io.ObjectProxy %s>" % self._amf_object

    def __getattr__(self, name):
        if name == '_amf_object':
            return self.__dict__['_amf_object']

        return getattr(self.__dict__['_amf_object'], name)

    def __setattr__(self, name, value):
        if name == '_amf_object':
            self.__dict__['_amf_object'] = value
        else:
            setattr(self._amf_object, name, value)

    def __readamf__(self, input):
        self._amf_object = input.readObject()

    def __writeamf__(self, output):
        output.writeObject(self._amf_object)

pyamf.register_class(ObjectProxy, 'flex.messaging.io.ObjectProxy',
    metadata=['external', 'amf3'])
