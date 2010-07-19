# -*- coding: utf-8 -*-
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Provides basic functionality for all pyamf.amf?.[De|E]ncoder classes.
"""

import types
import datetime

import pyamf
from pyamf import util


class IndexedCollection(object):
    """
    Store references to objects and provides an api to query references.

    @note: All attributes on the instance are private, use the apis only.
    """

    def __init__(self, use_hash=False):
        if use_hash is True:
            self.func = hash
        else:
            self.func = id

        self.clear()

    def clear(self):
        """
        Clears the collection.
        """
        self.list = []
        self.dict = {}

    def getByReference(self, ref):
        """
        Returns an object based on the supplied reference. The C{ref} should
        be an C{int}.

        If the reference is not found, C{None} will be returned.

        @raise pyamf.ReferenceError: references must be integers.
        """
        try:
            return self.list[ref]
        except IndexError:
            return None

    def getReferenceTo(self, obj):
        """
        Returns a reference to C{obj} if it is contained within this index.

        If the object is not contained within the collection, C{-§} will be
        returned.

        @param obj: The object to find the reference to.
        @return: An C{int} representing the reference or C{-1} is the object
            is not contained within the collection.
        """
        return self.dict.get(self.func(obj), -1)

    def append(self, obj):
        """
        Appends C{obj} to this index.

        @note: Uniqueness is not checked
        @return: The reference to C{obj} in this index.
        """
        h = self.func(obj)

        self.list.append(obj)
        idx = len(self.list) - 1
        self.dict[h] = idx

        return idx

    def __eq__(self, other):
        if isinstance(other, list):
            return self.list == other

        raise NotImplementError("cannot compare %s to %r" % (type(other), self))

    def __len__(self):
        return len(self.list)

    def __getitem__(self, idx):
        return self.getByReference(idx)

    def __contains__(self, obj):
        r = self.getReferenceTo(obj)

        return r != -1

    def __repr__(self):
        t = self.__class__

        return '<%s.%s size=%d 0x%x>' % (
            t.__module__,
            t.__name__,
            len(self.list),
            id(self))


class Context(object):
    """
    The base context for all AMF [de|en]coding.

    @ivar extra: The only public attribute. This is a placeholder for any extra
        contextual data that required for different adapters.
    @type extra: C{dict}
    @ivar _objects: A collection of stored references to objects that have
        already been visited by this context.
    @type _objects: L{IndexedCollection}
    @ivar _class_aliases: Lookup of C{class} -> L{pyamf.ClassAlias} as
        determined by L{pyamf.get_class_alias}
    @ivar _class_aliases: C{dict}
    @ivar _unicodes: Lookup of utf-8 encoded byte strings -> string objects
        (aka strings/unicodes). The reverse of L{_strings}.
    @type _unicodes: C{dict}
    """

    def __init__(self):
        self._objects = IndexedCollection()

        self.clear()

    def clear(self):
        """
        Clears the context.
        """
        self._objects.clear()
        self._class_aliases = {}
        self._unicodes = {}
        self.extra = {}

    def getObject(self, ref):
        """
        Gets an object based on a reference.

        @type ref: C{int}
        @return: The referenced object or C{None} if not found.
        """
        return self._objects.getByReference(ref)

    def getObjectReference(self, obj):
        """
        Gets a reference for an already referenced object.

        @return: The reference to the object or C{-1} if the object is not in
            the context.
        """
        return self._objects.getReferenceTo(obj)

    def addObject(self, obj):
        """
        Adds a reference to C{obj}.

        @return: Reference to C{obj}.
        @rtype: C{int}
        """
        return self._objects.append(obj)

    def getClassAlias(self, klass):
        """
        Gets a class alias based on the supplied C{klass}.

        @param klass: A class object.
        @return: The L{pyamf.ClassAlias} that is linked to C{klass}
        """
        alias = self._class_aliases.get(klass)

        if alias is not None:
            return alias

        try:
            alias = self._class_aliases[klass] = pyamf.get_class_alias(klass)
        except pyamf.UnknownClassAlias:
            # no alias has been found yet .. check subclasses
            alias = util.get_class_alias(klass)

            alias = self._class_aliases[klass] = alias(klass)

        return alias

    def getUnicodeForString(self, s):
        """
        Returns the corresponding unicode object for a given string. If there
        is no unicode object, one is created.

        @since: 0.6
        """
        h = hash(s)
        u = self._unicodes.get(h, None)

        if u is not None:
            return u

        u = self._unicodes[h] = unicode(s, 'utf-8')

        return u

    def getStringForUnicode(self, u):
        """
        Returns the corresponding utf-8 encoded string for a given unicode
        object. If there is no string, one is encoded.

        @since: 0.6
        """
        h = hash(u)
        s = self._unicodes.get(h, None)

        if s is not None:
            return s

        s = self._unicodes[h] = u.encode('utf-8')

        return s


class Codec(object):
    """
    Base codec.

    @ivar stream: The underlying data stream.
    @type stream: L{util.BufferedByteStream}
    @ivar context: The context for the encoding.
    @ivar strict: Whether the codec should operate in I{strict} mode.
    @type strict: C{bool}, default is C{False}.
    @ivar timezone_offset: The offset from I{UTC} for any C{datetime} objects
        being encoded. Default to C{None} means no offset.
    @type timezone_offset: C{datetime.timedelta} or C{int} or C{None}
    """

    def __init__(self, stream=None, context=None, strict=False,
                 timezone_offset=None):
        if not isinstance(stream, util.BufferedByteStream):
            stream = util.BufferedByteStream(stream)

        self.stream = stream
        self.context = context or self.buildContext()
        self.strict = strict
        self.timezone_offset = timezone_offset

        self._func_cache = {}

    def buildContext(self):
        """
        A context factory.
        """
        raise NotImplementedError

    def getTypeFunc(self, data):
        """
        Returns a callable based on C{data}. If no such callable can be found,
        the default must be to return C{None}.
        """
        raise NotImplementedError


class Decoder(Codec):
    """
    Base AMF decoder.

    @ivar strict: Defines how strict the decoding should be. For the time
        being this relates to typed objects in the stream that do not have a
        registered alias. Introduced in 0.4.
    @type strict: C{bool}
    """

    def readElement(self):
        """
        Reads an AMF3 element from the data stream.

        @raise DecodeError: The ActionScript type is unsupported.
        @raise EOStream: No more data left to decode.
        """
        pos = self.stream.tell()

        try:
            t = self.stream.read(1)
        except IOError:
            raise pyamf.EOStream

        try:
            func = self._func_cache[t]
        except KeyError:
            func = self.getTypeFunc(t)

            if not func:
                raise pyamf.DecodeError("Unsupported ActionScript type %x" % t)

            self._func_cache[t] = func

        try:
            return func()
        except IOError:
            self.stream.seek(pos)

            raise

    def __iter__(self):
        try:
            while True:
                yield self.readElement()
        except pyamf.EOStream:
            raise StopIteration


class _CustomTypeFunc(object):
    """
    Support for custom type mappings when encoding.
    """

    def __init__(self, encoder, func):
        self.encoder = encoder
        self.func = func

    def __call__(self, data, **kwargs):
        self.encoder.writeElement(
            self.func(data, encoder=self.encoder), **kwargs)


class Encoder(Codec):
    """
    Base AMF encoder.
    """

    def writeNull(self, obj, **kwargs):
        """
        Subclasses should override this and all write[type] functions
        """
        raise NotImplementedError

    writeString = writeNull
    writeUnicode = writeNull
    writeBoolean = writeNull
    writeNumber = writeNull
    writeList = writeNull
    writeUndefined = writeNull
    writeDate = writeNull
    writeXML = writeNull
    writeObject = writeNull

    def getTypeFunc(self, data):
        """
        Returns a callable that will encode C{data} to C{self.stream}
        """
        # check for any overridden types
        for type_, func in pyamf.TYPE_MAP.iteritems():
            try:
                if isinstance(data, type_):
                    return _CustomTypeFunc(self, func)
            except TypeError:
                if callable(type_) and type_(data):
                    return _CustomTypeFunc(self, func)

        if data is None:
            return self.writeNull

        t = type(data)

        if t is str:
            return self.writeString
        elif t is unicode:
            return self.writeUnicode
        elif t is bool:
            return self.writeBoolean
        elif t in (int, long, float):
            return self.writeNumber
        elif isinstance(data, (list, tuple)):
            return self.writeList
        elif t is pyamf.UndefinedType:
            return self.writeUndefined
        elif t in (datetime.date, datetime.datetime, datetime.time):
            return self.writeDate
        elif t in (types.ClassType, types.TypeType):
            # can't encode classes
            return None
        elif t in (types.BuiltinFunctionType, types.BuiltinMethodType,
                types.FunctionType, types.GeneratorType, types.ModuleType,
                types.LambdaType, types.MethodType):
            # can't encode code objects
            return None

        if util.is_xml_type(data):
            return self.writeXML

        return self.writeObject

    def writeElement(self, data, **kwargs):
        """
        Encodes C{data}.
        """
        key = type(data)
        func = None

        try:
            func = self._func_cache[key]
        except KeyError:
            func = self.getTypeFunc(data)

            if func is None:
                raise pyamf.EncodeError('Unable to encode %r (type %r)' % (
                    data, key))

            self._func_cache[key] = func

        func(data, **kwargs)
