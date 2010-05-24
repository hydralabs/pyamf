import types
import datetime

import pyamf
from pyamf import util



class Context(object):
    """
    I hold the AMF context for en/decoding streams.

    :ivar objects: An indexed collection of referencable objects encountered
        during en/decoding.
    :type objects: :class:`pyamf.util.IndexedCollection`
    :ivar class_aliases: A `dict` of `class` to :class:`ClassAlias`
    """

    def __init__(self):
        self.objects = util.IndexedCollection()

        self.clear()

    def clear(self):
        """
        Completely clears the context.
        """
        self.objects.clear()
        self.class_aliases = {}
        self.proxied_objects = {}
        self.unicodes = {}
        self.extra_context = {}

    def getObject(self, ref):
        """
        Gets an object based on a reference.

        :param ref: The reference for the object.
        :type ref: `int`
        :return: The referenced object or `None` if not found.
        """
        return self.objects.getByReference(ref)

    def getObjectReference(self, obj):
        """
        Gets a reference for an object.

        :param obj: The referenced object.
        :return: The reference to the object or `None` if the object is not
                 in the context.
        """
        return self.objects.getReferenceTo(obj)

    def addObject(self, obj):
        """
        Adds a reference to `obj`.

        :type obj: `mixed`
        :param obj: The object to add to the context.
        :rtype: `int`
        :return: Reference to `obj`.
        """
        return self.objects.append(obj)

    def getClassAlias(self, klass):
        """
        Gets a class alias based on the supplied `klass`.

        :param klass: The class object.
        :return: The :class:`ClassAlias` that is linked to `klass`
        """
        alias = self.class_aliases.get(klass)

        if alias is not None:
            return alias

        try:
            alias = self.class_aliases[klass] = pyamf.get_class_alias(klass)
        except pyamf.UnknownClassAlias:
            # no alias has been found yet .. check subclasses
            alias = util.get_class_alias(klass)

            alias = self.class_aliases[klass] = alias(klass)

        return alias

    def getProxyForObject(self, obj):
        """
        Returns the proxied version of `obj` as stored in the context, or
        creates a new proxied object and returns that.

        :see: func:`pyamf.flex.proxy_object`
        :since: 0.6
        """
        proxied = self.proxied_objects.get(id(obj))

        if proxied is None:
            from pyamf import flex

            proxied = flex.proxy_object(obj)

            self.addProxyObject(obj, proxied)

        return proxied

    def getObjectForProxy(self, proxy):
        """
        Returns the unproxied version of `proxy` as stored in the context, or
        unproxies the proxy and returns that 'raw' object.

        :see: :func:`pyamf.flex.unproxy_object`
        :since: 0.6
        """
        obj = self.proxied_objects.get(id(proxy))

        if obj is None:
            from pyamf import flex

            obj = flex.unproxy_object(proxy)

            self.addProxyObject(obj, proxy)

        return obj

    def addProxyObject(self, obj, proxied):
        """
        Stores a reference to the unproxied and proxied versions of `obj` for
        later retrieval.

        :since: 0.6
        """
        self.proxied_objects[id(obj)] = proxied
        self.proxied_objects[id(proxied)] = obj

    def getUnicodeForString(self, s):
        """
        Returns the corresponding unicode object for a given string. If there
        is no unicode object, one is created.

        :since: 0.6
        """
        h = hash(s)
        u = self.unicodes.get(h, None)

        if u is not None:
            return u

        u = self.unicodes[h] = unicode(s, 'utf-8')

        return u

    def getStringForUnicode(self, u):
        """
        Returns the corresponding utf-8 encoded string for a given unicode
        object. If there is no string, one is encoded.

        :since: 0.6
        """
        h = hash(u)
        s = self.unicodes.get(h, None)

        if s is not None:
            return s

        s = self.unicodes[h] = u.encode('utf-8')

        return s


class Codec(object):
    """
    Base codec.

    @ivar stream: The underlying data stream.
    @type stream: L{util.BufferedByteStream}
    @ivar context: The context for the encoding.
    @ivar strict: Whether the codec should operate in I{strict} mode. Nothing
        is really affected by this for the time being - its just here for
        flexibility.
    @type strict: C{bool}, default is C{False}.
    @ivar timezone_offset: The offset from I{UTC} for any C{datetime} objects
        being encoded. Default to C{None} means no offset.
    @type timezone_offset: C{datetime.timedelta} or C{int} or C{None}
    """

    context_class = Context

    def __init__(self, stream=None, context=None, strict=False, timezone_offset=None):
        if isinstance(stream, util.BufferedByteStream):
            self.stream = stream
        else:
            self.stream = util.BufferedByteStream(stream)

        self.context = context or self.buildContext()

        self._func_cache = {}

        self.strict = strict
        self.timezone_offset = timezone_offset

    def buildContext(self):
        return self.context_class()


class Decoder(Codec):
    """
    Base AMF decoder.

    :ivar stream: The underlying data stream.
    :type stream: :class:`BufferedByteStream<pyamf.util.BufferedByteStream>`
    :ivar strict: Defines how strict the decoding should be. For the time
                  being this relates to typed objects in the stream that do not
                  have a registered alias. Introduced in 0.4.
    :type strict: `bool`
    :ivar timezone_offset: The offset from UTC for any datetime objects being
        decoded. Default to `None` means no offset.
    :type timezone_offset: `datetime.timedelta`
    """

    def readProxy(self, obj, **kwargs):
        """
        Decodes a proxied object from the stream.

        :since: 0.6
        """
        return self.context.getObjectForProxy(obj)

    def readElement(self):
        """
        Reads an AMF3 element from the data stream.

        :raise DecodeError: The ActionScript type is unsupported.
        :raise EOStream: No more data left to decode.
        """
        pos = self.stream.tell()

        try:
            t = self.stream.read(1)
        except IOError:
            raise pyamf.EOStream

        try:
            func = self._func_cache[t]
        except KeyError:
            func = getattr(self, self.type_map[t])

            if not func:
                raise pyamf.DecodeError("Unsupported ActionScript type %r" % (t,))

            self._func_cache[t] = func

        try:
            return func()
        except IOError:
            self.stream.seek(pos)

            raise

    def __iter__(self):
        try:
            while 1:
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
        self.encoder.writeElement(self.func(data, encoder=self.encoder), **kwargs)


class Encoder(Codec):
    """
    Base AMF encoder.
    """

    type_map = {
        util.xml_types: 'writeXML'
    }

    def writeProxy(self, obj, **kwargs):
        """
        Encodes a proxied object to the stream.

        @since: 0.6
        """
        proxy = self.context.getProxyForObject(obj)

        self.writeElement(proxy, use_proxies=False)

    def writeNull(self, obj, **kwargs):
        """
        Subclasses should override this and all write[type] functions
        """
        raise NotImplementedError

    writeString = writeNull
    writeBoolean = writeNull
    writeNumber = writeNull
    writeList = writeNull
    writeUndefined = writeNull
    writeDate = writeNull
    writeXML = writeNull
    writeObject = writeNull

    def getCustomTypeFunc(self, data):
        for type_, func in pyamf.TYPE_MAP.iteritems():
            try:
                if isinstance(data, type_):
                    return _CustomTypeFunc(self, func)
            except TypeError:
                if callable(type_) and type_(data):
                    return _CustomTypeFunc(self, func)

    def _getTypeFunc(self, data):
        """
        Gets a function used to encode C{data}.

        @rtype: callable.
        @return: The function used to encode data to the stream.
        @raise EncodeError: Unable to find a corresponding function that will
            encode C{data}.
        """
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
        elif t in (types.ClassType, types.TypeType):
            # can't encode classes
            raise pyamf.EncodeError("Cannot encode %r" % (data,))
        elif t in (datetime.date, datetime.datetime, datetime.time):
            return self.writeDate
        elif t in (types.BuiltinFunctionType, types.BuiltinMethodType,
                types.FunctionType, types.GeneratorType, types.ModuleType,
                types.LambdaType, types.MethodType):
            # can't encode code objects
            raise pyamf.EncodeError("Cannot encode %r" % (data,))

        for t, method in self.type_map.iteritems():
            if not isinstance(data, t):
                continue

            if callable(method):
                return lambda *args, **kwargs: method(self, *args, **kwargs)

            return getattr(self, method)

        return self.writeObject

    def writeElement(self, data, **kwargs):
        """
        Writes the data. Overridden in subclass.

        :type   data: `mixed`
        :param  data: The data to be encoded to the data stream.
        """
        key = type(data)
        func = None

        try:
            func = self._func_cache[key]
        except KeyError:
            func = self.getCustomTypeFunc(data)

            if not func:
                func = self._getTypeFunc(data)

            self._func_cache[key] = func

        func(data, **kwargs)
