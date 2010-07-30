# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C-extension for L{pyamf.amf3} Python module in L{PyAMF<pyamf>}.

@since: 0.6
"""

from cpython cimport *


from cpyamf.util cimport cBufferedByteStream, BufferedByteStream
from cpyamf cimport codec
import pyamf
from pyamf import util, amf3, xml
import types


try:
    import zlib
except ImportError:
    zlib = None


cdef char TYPE_UNDEFINED = '\x00'
cdef char TYPE_NULL = '\x01'
cdef char TYPE_BOOL_FALSE = '\x02'
cdef char TYPE_BOOL_TRUE = '\x03'
cdef char TYPE_INTEGER = '\x04'
cdef char TYPE_NUMBER = '\x05'
cdef char TYPE_STRING = '\x06'
cdef char TYPE_XML = '\x07'
cdef char TYPE_DATE = '\x08'
cdef char TYPE_ARRAY = '\x09'
cdef char TYPE_OBJECT = '\x0A'
cdef char TYPE_XMLSTRING = '\x0B'
cdef char TYPE_BYTEARRAY = '\x0C'

cdef unsigned int REFERENCE_BIT = 0x01
cdef char REF_CHAR = '\x01'

#: The maximum that can be represented by an signed 29 bit integer.
cdef long MAX_29B_INT = 0x0FFFFFFF

#: The minimum that can be represented by an signed 29 bit integer.
cdef long MIN_29B_INT = -0x10000000

cdef int OBJECT_ENCODING_STATIC = 0x00
cdef int OBJECT_ENCODING_EXTERNAL = 0x01
cdef int OBJECT_ENCODING_DYNAMIC = 0x02
cdef int OBJECT_ENCODING_PROXY = 0x03

cdef PyObject *ByteArrayType = <PyObject *>amf3.ByteArray
cdef object DataInput = amf3.DataInput
cdef object DataOutput = amf3.DataOutput
cdef object empty_string = str('')


cdef class ClassDefinition(object):
    """
    Holds transient class trait info for an individual encode/decode.
    """

    property alias:
        def __get__(self):
            return self.alias

    property encoding:
        def __get__(self):
            return self.encoding

    property static_properties:
        def __get__(self):
            return self.static_properties

    property attr_len:
        def __get__(self):
            return self.attr_len

    def __cinit__(self):
        self.alias = None
        self.ref = -1
        self.attr_len = -1
        self.encoding = -1
        self.encoded_ref = NULL
        self.encoded_ref_size = -1

    def __init__(self, alias):
        self.alias = alias

        alias.compile()

        self.attr_len = 0
        self.static_properties = []

        if alias.static_attrs:
            self.attr_len = len(alias.static_attrs)
            self.static_properties = alias.static_attrs

        self.encoding = OBJECT_ENCODING_DYNAMIC

        if alias.external:
            self.encoding = OBJECT_ENCODING_EXTERNAL
        elif not alias.dynamic:
            if alias.static_attrs == alias.encodable_properties:
                self.encoding = OBJECT_ENCODING_STATIC

    def __dealloc__(self):
        if self.encoded_ref != NULL:
            PyMem_Free(self.encoded_ref)
            self.encoded_ref = NULL


cdef class Context(codec.Context):
    """
    I hold the AMF3 context for en/decoding streams.
    """

    def __cinit__(self):
        self.strings = codec.IndexedCollection(use_hash=1)
        self.classes = {}
        self.class_ref = {}
        self.proxied_objects = {}
        self.legacy_xml = codec.IndexedCollection()

        self.class_idx = 0

    cpdef int clear(self) except? -1:
        """
        Clears the context.
        """
        codec.Context.clear(self)

        self.strings.clear()
        self.legacy_xml.clear()

        self.classes = {}
        self.class_ref = {}
        self.class_idx = 0

        return 0

    property strings:
        def __get__(self):
            return self.strings

    property class_ref:
        def __get__(self):
            return self.class_ref

        def __set__(self, value):
            self.class_ref = value

    property classes:
        def __get__(self):
            return self.classes

        def __set__(self, value):
            self.classes = value

    property legacy_xml:
        def __get__(self):
            return self.legacy_xml

    cpdef object getString(self, Py_ssize_t ref):
        cdef PyObject *r = PyDict_GetItem(self.unicodes, ref)

        if r != NULL:
            return <object>r

        return self.strings.getByReference(ref)

    cpdef Py_ssize_t getStringReference(self, object s) except -2:
        return self.strings.getReferenceTo(s)

    cpdef Py_ssize_t addString(self, object s) except -2:
        """
        Returns -2 which signifies that s was empty
        """
        if not PyString_CheckExact(s):
            raise TypeError('str expected')

        if PyString_GET_SIZE(s) == 0:
            return -1

        return self.strings.append(s)

    cpdef object getClassByReference(self, Py_ssize_t ref):
        cdef PyObject *ret
        cdef object ref_obj

        ref_obj = PyInt_FromSsize_t(ref)

        ret = PyDict_GetItem(self.class_ref, ref_obj)

        if ret == NULL:
            return None

        return <object>ret

    cpdef object getClass(self, object klass):
        cdef PyObject *ret

        ret = PyDict_GetItem(self.classes, klass)

        if ret == NULL:
            return None

        return <object>ret

    cpdef Py_ssize_t addClass(self, ClassDefinition alias, klass) except? -1:
        cdef Py_ssize_t ref = self.class_idx
        cdef object ref_obj

        ref_obj = PyInt_FromSsize_t(ref)

        self.class_ref[ref_obj] = alias
        self.classes[klass] = alias

        alias.ref = ref_obj
        self.class_idx += 1

        return ref

    cpdef object getLegacyXML(self, Py_ssize_t ref):
        return self.legacy_xml.getByReference(ref)

    cpdef Py_ssize_t getLegacyXMLReference(self, object doc) except -2:
        return self.legacy_xml.getReferenceTo(doc)

    cpdef Py_ssize_t addLegacyXML(self, object doc) except -1:
        return self.legacy_xml.append(doc)

    cpdef object getProxyForObject(self, object obj):
        """
        Returns the proxied version of C{obj} as stored in the context, or
        creates a new proxied object and returns that.

        @see: L{pyamf.flex.proxy_object}
        @since: 0.6
        """
        cdef PyObject *ret = PyDict_GetItem(self.proxied_objects, PyLong_FromVoidPtr(<void *>obj))

        if ret != NULL:
            return <object>ret

        from pyamf import flex

        proxied = flex.proxy_object(obj)

        self.addProxyObject(obj, proxied)

        return proxied

    cpdef object getObjectForProxy(self, object proxy):
        """
        Returns the unproxied version of C{proxy} as stored in the context, or
        unproxies the proxy and returns that 'raw' object.

        @see: L{pyamf.flex.unproxy_object}
        @since: 0.6
        """
        cdef PyObject *ret = PyDict_GetItem(self.proxied_objects, PyLong_FromVoidPtr(<void *>proxy))

        if ret != NULL:
            return <object>ret

        from pyamf import flex

        obj = flex.unproxy_object(proxy)

        self.addProxyObject(obj, proxy)

        return obj

    cpdef int addProxyObject(self, object obj, object proxied) except? -1:
        """
        Stores a reference to the unproxied and proxied versions of C{obj} for
        later retrieval.

        @since: 0.6
        """
        self.proxied_objects[PyLong_FromVoidPtr(<void *>obj)] = proxied
        self.proxied_objects[PyLong_FromVoidPtr(<void *>proxied)] = obj

        return 0


cdef class Decoder(codec.Decoder):
    """
    Decodes an AMF3 data stream.
    """

    cdef readonly Context context

    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', None)

        if self.context is None:
            self.context = codec.Context()

        codec.Decoder.__init__(self, *args, **kwargs)

    cdef object readInteger(self, int signed=1):
        """
        Reads and returns an integer from the stream.

        @type signed: C{bool}
        @see: U{Parsing integers on OSFlash
        <http://osflash.org/amf3/parsing_integers>} for the AMF3 integer data
        format.
        """
        cdef long r

        decode_int(self.stream, &r, signed)

        return <object>r

    cdef object readNumber(self):
        cdef double d

        self.stream.read_double(&d)

        return d

    cdef object readUnicode(self):
        """
        Reads and returns a decoded utf-u unicode from the stream.
        """
        cdef object s = self.readString()

        return self.context.getUnicodeForString(s)

    cpdef object readString(self):
        """
        Reads and returns a string from the stream.
        """
        cdef long r = _read_ref(self.stream)

        if r & REFERENCE_BIT == 0:
            # read a string reference
            return self.context.getString(r >> 1)

        r >>= 1

        if r == 0:
            return empty_string

        cdef char *buf = NULL
        cdef object s

        try:
            self.stream.read(&buf, r)
            s = PyString_FromStringAndSize(buf, r)
        finally:
            if buf != NULL:
                PyMem_Free(buf)

        self.context.addString(s)

        return s

    cdef object readDate(self):
        """
        Read date from the stream.

        The timezone is ignored as the date is always in UTC.
        """
        cdef long ref = _read_ref(self.stream)

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        cdef double ms

        self.stream.read_double(&ms)

        cdef object result = util.get_datetime(ms / 1000.0)

        if self.timezone_offset is not None:
            result += self.timezone_offset

        self.context.addObject(result)

        return result

    cdef object readArray(self):
        """
        Reads an array from the stream.
        """
        cdef long size = _read_ref(self.stream)
        cdef long i
        cdef object result
        cdef object tmp

        if size & REFERENCE_BIT == 0:
            return self.context.getObject(size >> 1)

        size >>= 1
        key = self.readString()

        if key == empty_string:
            # integer indexes only -> python list
            result = []
            self.context.addObject(result)

            for i from 0 <= i < size:
                PyList_Append(result, self.readElement())

            return result

        result = pyamf.MixedArray()
        self.context.addObject(result)

        while key:
            result[key] = self.readElement()
            key = self.readString()

        for i from 0 <= i < size:
            el = self.readElement()
            result[i] = el

        return result

    cpdef ClassDefinition _getClassDefinition(self, long ref):
        """
        Reads class definition from the stream.
        """
        if ref & REFERENCE_BIT == 0:
            return self.context.getClassByReference(ref >> 1)

        ref >>= 1

        cdef object name = self.readString()
        cdef object alias = None
        cdef Py_ssize_t i

        if PyString_GET_SIZE(name) == 0:
            name = pyamf.ASObject

        try:
            alias = pyamf.get_class_alias(name)
        except pyamf.UnknownClassAlias:
            if self.strict:
                raise

            alias = pyamf.TypedObjectClassAlias(pyamf.TypedObject, name)

        cdef ClassDefinition class_def = ClassDefinition(alias)

        class_def.encoding = ref & 0x03
        class_def.attr_len = ref >> 2
        class_def.static_properties = []

        if class_def.attr_len > 0:
            for i from 0 <= i < class_def.attr_len:
                key = self.readString()

                PyList_Append(class_def.static_properties, key)

        self.context.addClass(class_def, alias.klass)

        return class_def

    cdef int _readStatic(self, ClassDefinition class_def, obj) except -1:
        cdef Py_ssize_t i

        for 0 <= i < class_def.attr_len:
            PyDict_SetItem(obj, <object>PyList_GetItem(class_def.static_properties, i), self.readElement())

        return 0

    cdef int _readDynamic(self, ClassDefinition class_def, obj) except -1:
        cdef object attr = self.readString()

        while PyString_GET_SIZE(attr) != 0:
            PyDict_SetItem(obj, attr, self.readElement())

            attr = self.readString()

        return 0

    cdef object readObject(self, int use_proxies=-1):
        """
        Reads an object from the stream.

        @raise pyamf.EncodeError: Decoding an object in amf3 tagged as amf0
            only is not allowed.
        @raise pyamf.DecodeError: Unknown object encoding.
        """
        if use_proxies == -1:
            use_proxies = self.use_proxies

        cdef long ref = _read_ref(self.stream)
        cdef object obj

        if ref & REFERENCE_BIT == 0:
            obj = self.context.getObject(ref >> 1)

            if obj is None:
                raise pyamf.ReferenceError('Unknown reference')

            if use_proxies == 1:
                return self.readProxy(obj)

            return obj

        cdef ClassDefinition class_def = self._getClassDefinition(ref >> 1)
        cdef object alias = class_def.alias

        obj = alias.createInstance(codec=self)
        cdef dict obj_attrs = {}

        self.context.addObject(obj)

        if class_def.encoding == OBJECT_ENCODING_DYNAMIC:
            self._readStatic(class_def, obj_attrs)
            self._readDynamic(class_def, obj_attrs)
        elif class_def.encoding == OBJECT_ENCODING_STATIC:
            self._readStatic(class_def, obj_attrs)
        elif class_def.encoding == OBJECT_ENCODING_EXTERNAL or class_def.encoding == OBJECT_ENCODING_PROXY:
            obj.__readamf__(DataInput(self))

            if use_proxies == 1:
                return self.readProxy(obj)

            return obj
        else:
            raise pyamf.DecodeError("Unknown object encoding")

        alias.applyAttributes(obj, obj_attrs, codec=self)

        if use_proxies == 1:
            return self.readProxy(obj)

        return obj

    cdef object readXML(self, int legacy=0):
        """
        Reads an XML object from the stream.

        @type legacy: C{bool}
        @param legacy: The read XML is in 'legacy' format.
        """
        cdef long ref = _read_ref(self.stream)

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        ref >>= 1

        cdef char *buf = NULL
        cdef object s

        try:
            self.stream.read(&buf, ref)
            s = PyString_FromStringAndSize(buf, ref)
        finally:
            if buf != NULL:
                PyMem_Free(buf)

        x = util.ET.fromstring(s)
        self.context.addObject(x)

        if legacy == 1:
            self.context.addLegacyXML(x)

        return x

    cdef object readByteArray(self):
        """
        Reads a string of data from the stream.

        Detects if the L{ByteArray} was compressed using C{zlib}.

        @see: L{ByteArray}
        @note: This is not supported in ActionScript 1.0 and 2.0.
        """
        cdef long ref = _read_ref(self.stream)

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        cdef char *buf = NULL
        cdef object s
        cdef object compressed = None

        ref >>= 1

        try:
            self.stream.read(&buf, ref)
            s = PyString_FromStringAndSize(buf, ref)
        finally:
            if buf != NULL:
                PyMem_Free(buf)

        if zlib:
            try:
                s = zlib.decompress(s)
                compressed = True
            except zlib.error:
                compressed = False

            s = (<object>ByteArrayType)(s)

        s.compressed = compressed

        self.context.addObject(s)

        return s

    cdef object readProxy(self, obj):
        """
        Decodes a proxied object from the stream.

        @since: 0.6
        """
        return self.context.getObjectForProxy(obj)

    cpdef object readElement(self):
        """
        Reads an AMF3 element from the data stream.

        @raise DecodeError: The ActionScript type is unsupported.
        @raise EOStream: No more data left to decode.
        """
        cdef Py_ssize_t pos = self.stream.tell()

        cdef unsigned char t

        if self.stream.at_eof():
            raise pyamf.EOStream

        self.stream.read_uchar(&t)

        try:
            if t == TYPE_STRING:
                return self.readUnicode()
            elif t == TYPE_OBJECT:
                return self.readObject()
            elif t == TYPE_UNDEFINED:
                return pyamf.Undefined
            elif t == TYPE_NULL:
                return None
            elif t == TYPE_BOOL_FALSE:
                return False
            elif t == TYPE_BOOL_TRUE:
                return True
            elif t == TYPE_INTEGER:
                return self.readInteger()
            elif t == TYPE_NUMBER:
                return self.readNumber()
            elif t == TYPE_ARRAY:
                return self.readArray()
            elif t == TYPE_DATE:
                return self.readDate()
            elif t == TYPE_BYTEARRAY:
                return self.readByteArray()
            elif t == TYPE_XML:
                return self.readXML(1)
            elif t == TYPE_XMLSTRING:
                return self.readXML(0)
        except IOError:
            self.stream.seek(pos)

            raise

        raise pyamf.DecodeError("Unsupported ActionScript type")


cdef class Encoder(codec.Encoder):
    """
    The AMF3 Encoder.
    """

    cdef public bint use_proxies
    cdef readonly Context context

    def __init__(self, *args, **kwargs):
        self.use_proxies = kwargs.pop('use_proxies', amf3.use_proxies_default)
        self.context = kwargs.pop('context', None)

        if self.context is None:
            self.context = Context()

        codec.Encoder.__init__(self, *args, **kwargs)

    cpdef int writeString(self, object s, int writeType=1) except -1:
        cdef Py_ssize_t l
        cdef Py_ssize_t r

        if writeType == 1:
            self.writeType(TYPE_STRING)

        l = PyString_GET_SIZE(s)

        if l == 0:
            # '' is a special case
            self.stream.write(&REF_CHAR, 1)

            return 0

        r = self.context.getStringReference(s)

        if r != -1:
            # we have a reference

            _encode_integer(self.stream, r << 1)

            return 0

        self.context.addString(s)

        _encode_integer(self.stream, (l << 1) | REFERENCE_BIT)
        self.stream.write(PyString_AS_STRING(s), l)

        return 0

    cdef int writeUnicode(self, object u, int writeType=1) except -1:
        if writeType == 1:
            self.writeType(TYPE_STRING)

        l = PyUnicode_GET_SIZE(u)

        if l == 0:
            # '' is a special case
            self.stream.write(&REF_CHAR, 1)

            return 0

        cdef object s = self.context.getStringForUnicode(u)

        return self.writeString(s, 0)

    cdef inline int writeType(self, char type) except -1:
        return self.stream.write(<char *>&type, 1)

    cdef int writeInt(self, object n) except -1:
        cdef long x = PyInt_AS_LONG(n)

        if x < MIN_29B_INT or x > MAX_29B_INT:
            return self.writeNumber(float(n))

        self.writeType(TYPE_INTEGER)
        _encode_integer(self.stream, x)

    cdef int writeLong(self, object n) except -1:
        cdef long x

        try:
            x = PyLong_AsLong(n)
        except:
            return self.writeNumber(float(n))

        if x < MIN_29B_INT or x > MAX_29B_INT:
            return self.writeNumber(float(n))

        self.writeType(TYPE_INTEGER)
        _encode_integer(self.stream, x)

    cdef int writeNumber(self, object n) except -1:
        cdef double x = PyFloat_AS_DOUBLE(n)

        self.writeType(TYPE_NUMBER)
        self.stream.write_double(x)

        return 0

    cdef int writeList(self, object n, int use_proxies=-1) except -1:
        cdef Py_ssize_t ref = self.context.getObjectReference(n)
        cdef Py_ssize_t i
        cdef PyObject *x

        if use_proxies == -1:
            use_proxies = self.use_proxies

        if use_proxies == 1:
            # Encode lists as ArrayCollections
            return self.writeProxy(n)

        self.writeType(TYPE_ARRAY)

        if ref != -1:
            return _encode_integer(self.stream, ref << 1)

        self.context.addObject(n)

        ref = PyList_GET_SIZE(n)

        _encode_integer(self.stream, (ref << 1) | REFERENCE_BIT)

        self.writeType('\x01')

        for i from 0 <= i < ref:
            x = PyList_GET_ITEM(n, i)

            self.writeElement(<object>x)

        return 0

    cdef int writeTuple(self, object n) except -1:
        cdef Py_ssize_t ref = self.context.getObjectReference(n)
        cdef Py_ssize_t i
        cdef PyObject *x

        self.writeType(TYPE_ARRAY)

        if ref != -1:
            return _encode_integer(self.stream, ref << 1)

        self.context.addObject(n)

        ref = PyTuple_GET_SIZE(n)

        _encode_integer(self.stream, (ref << 1) | REFERENCE_BIT)
        self.writeType('\x01')

        for i from 0 <= i < ref:
            x = PyTuple_GET_ITEM(n, i)

            self.writeElement(<object>x)

        return 0

    cpdef int writeLabel(self, str e) except -1:
        return self.writeString(e, 0)

    cpdef int writeMixedArray(self, object n, int use_proxies=-1) except? -1:
        # Design bug in AMF3 that cannot read/write empty key strings
        # http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug
        # for more info
        if '' in n:
            raise pyamf.EncodeError("dicts cannot contain empty string keys")

        if use_proxies == -1:
            use_proxies = self.use_proxies

        if use_proxies == 1:
            return self.writeProxy(n)

        self.writeType(TYPE_ARRAY)

        ref = self.context.getObjectReference(n)

        if ref != -1:
            return _encode_integer(self.stream, ref << 1)

        self.context.addObject(n)

        # The AMF3 spec demands that all str based indicies be listed first
        keys = n.keys()
        int_keys = []
        str_keys = []

        for x in keys:
            if isinstance(x, (int, long)):
                int_keys.append(x)
            elif isinstance(x, (str, unicode)):
                str_keys.append(x)
            else:
                raise ValueError("Non int/str key value found in dict")

        # Make sure the integer keys are within range
        l = len(int_keys)

        for x in int_keys:
            if l < x <= 0:
                # treat as a string key
                str_keys.append(x)
                del int_keys[int_keys.index(x)]

        int_keys.sort()

        # If integer keys don't start at 0, they will be treated as strings
        if len(int_keys) > 0 and int_keys[0] != 0:
            for x in int_keys:
                str_keys.append(str(x))
                del int_keys[int_keys.index(x)]

        _encode_integer(self.stream, len(int_keys) << 1 | REFERENCE_BIT)

        for x in str_keys:
            self.writeLabel(x)
            self.writeElement(n[x])

        self.stream.write_uchar(0x01)

        for k in int_keys:
            self.writeElement(n[k])

    cpdef int writeObject(self, object obj, int use_proxies=-1) except -1:
        cdef Py_ssize_t ref
        cdef object kls
        cdef ClassDefinition definition
        cdef object alias = None
        cdef int class_ref = 0
        cdef int ret = 0
        cdef char *buf = NULL
        cdef PyObject *key
        cdef PyObject *value
        cdef object attrs

        if use_proxies == -1:
            use_proxies = self.use_proxies

        if use_proxies == 1:
            return self.writeProxy(obj)

        self.writeType(TYPE_OBJECT)

        ref = self.context.getObjectReference(obj)

        if ref != -1:
            _encode_integer(self.stream, ref << 1)

            return 0

        self.context.addObject(obj)

        # object is not referenced, serialise it
        kls = obj.__class__
        definition = <ClassDefinition>self.context.getClass(kls)

        if definition:
            class_ref = 1
            alias = definition.alias
        else:
            try:
                alias = pyamf.get_class_alias(kls)
            except pyamf.UnknownClassAlias:
                alias_klass = util.get_class_alias(kls)
                meta = util.get_class_meta(kls)

                alias = alias_klass(kls, defer=True, **meta)

            definition = ClassDefinition(alias)

            self.context.addClass(definition, alias.klass)

        if class_ref == 1:
            self.stream.write(definition.encoded_ref, definition.encoded_ref_size)
        else:
            ref = 0

            if definition.encoding != OBJECT_ENCODING_EXTERNAL:
                ref += definition.attr_len << 4

            ref |= definition.encoding << 2 | REFERENCE_BIT << 1 | REFERENCE_BIT

            try:
                ret = encode_int(ref, &buf)

                self.stream.write(buf, ret)
            finally:
                if buf != NULL:
                    PyMem_Free(buf)

            try:
                definition.encoded_ref_size = encode_int(definition.ref << 2 | REFERENCE_BIT, &definition.encoded_ref)
            except:
                if definition.encoded_ref != NULL:
                    PyMem_Free(definition.encoded_ref)
                    definition.encoded_ref = NULL

                raise

            if alias.anonymous:
                self.stream.write(&REF_CHAR, 1)
            else:
                self.writeLabel(alias.alias)

            # work out what the final reference for the class will be.
            # this is okay because the next time an object of the same
            # class is encoded, class_ref will be True and never get here
            # again.

        if alias.external:
            obj.__writeamf__(DataOutput(self))

            return 0

        attrs = alias.getEncodableAttributes(obj, codec=self)

        if PyDict_CheckExact(attrs) != 1:
            raise TypeError('Expected dict for encodable attributes')

        if definition.attr_len > 0:
            if class_ref == 0:
                for attr in definition.static_properties:
                    self.writeLabel(attr)

            for attr in definition.static_properties:
                value = PyDict_GetItem(attrs, attr)

                if value == NULL:
                    raise KeyError

                if PyDict_DelItem(attrs, attr) == -1:
                    return -1

                self.writeElement(<object>value)

            if definition.encoding == OBJECT_ENCODING_STATIC:
                return 0

        if definition.encoding == OBJECT_ENCODING_DYNAMIC:
            ref = 0
            key = NULL
            value = NULL

            while PyDict_Next(attrs, &ref, &key, &value):
                self.writeLabel(<object>key)
                self.writeElement(<object>value)

            self.stream.write(&REF_CHAR, 1)

        return 0

    cdef int writeByteArray(self, object obj) except -1:
        """
        Writes a L{ByteArray} to the data stream.

        @param n: The L{ByteArray} data to be encoded to the AMF3 data stream.
        @type n: L{ByteArray}
        """
        cdef Py_ssize_t ref
        cdef object buf

        self.writeType(TYPE_BYTEARRAY)

        ref = self.context.getObjectReference(obj)

        if ref != -1:
            _encode_integer(self.stream, ref << 1)

            return 0

        self.context.addObject(obj)

        buf = str(obj)
        l = PyString_GET_SIZE(buf)

        _encode_integer(self.stream, (l << 1) | REFERENCE_BIT)
        self.stream.write(PyString_AS_STRING(buf), l)

        return 0

    cdef int writeXML(self, obj) except -1:
        cdef Py_ssize_t i = self.context.getLegacyXMLReference(obj)

        if i == -1:
            self.writeType(TYPE_XMLSTRING)
        else:
            self.writeType(TYPE_XML)

        i = self.context.getObjectReference(obj)

        if i != -1:
            _encode_integer(self.stream, i << 1)

            return 0

        self.context.addObject(obj)

        s = xml.tostring(obj).encode('utf-8')

        if PyString_CheckExact(s):
            raise TypeError('Expected string from xml serialization')

        i = PyString_GET_SIZE(s)

        _encode_integer(self.stream, (i << 1) | REFERENCE_BIT)
        self.stream.write(PyString_AS_STRING(s), i)

        return 0

    cdef int writeDateTime(self, obj) except -1:
        """
        Writes an L{datetime.datetime} object to the stream
        """
        cdef Py_ssize_t ref = self.context.getObjectReference(obj)

        self.writeType(TYPE_DATE)

        if ref != -1:
            _encode_integer(self.stream, ref << 1)

            return 0

        self.context.addObject(obj)
        self.stream.write(&REF_CHAR, 1)

        if self.timezone_offset is not None:
            obj -= self.timezone_offset

        ms = <double>util.get_timestamp(obj)
        self.stream.write_double(ms * 1000.0)

    cdef int writeProxy(self, obj) except -1:
        """
        Encodes a proxied object to the stream.

        @since: 0.6
        """
        cdef object proxy = self.context.getProxyForObject(obj)

        return self.writeObject(proxy, 0)

    cdef inline int handleBasicTypes(self, object element, object py_type) except -1:
        cdef int ret = codec.Encoder.handleBasicTypes(self, element, py_type)

        if ret == 1: # not handled
            if <PyObject *>py_type == ByteArrayType:
                ret = self.writeByteArray(element)

        return ret


cdef int encode_int(long i, char **buf) except -1:
    # Use typecasting to get the twos complement representation of i
    cdef unsigned long n = (<unsigned long*>(<void *>(&i)))[0]

    cdef int size = 0
    cdef unsigned long real_value = n
    cdef char changed = 0
    cdef unsigned char count = 0
    cdef char *bytes = NULL

    if n > 0x1fffff:
        size = 4
        bytes = <char *>PyMem_Malloc(size)

        if bytes == NULL:
            raise MemoryError

        changed = 1
        n = n >> 1
        bytes[count] = 0x80 | ((n >> 21) & 0xff)
        count += 1

    if n > 0x3fff:
        if size == 0:
            size = 3
            bytes = <char *>PyMem_Malloc(size)

            if bytes == NULL:
                raise MemoryError

        bytes[count] = 0x80 | ((n >> 14) & 0xff)
        count += 1

    if n > 0x7f:
        if size == 0:
            size = 2
            bytes = <char *>PyMem_Malloc(size)

            if bytes == NULL:
                raise MemoryError

        bytes[count] = 0x80 | ((n >> 7) & 0xff)
        count += 1

    if changed == 1:
        n = real_value

    if size == 0:
        size = 1

        bytes = <char *>PyMem_Malloc(size)

        if bytes == NULL:
            raise MemoryError

    if n > 0x1fffff:
        bytes[count] = n & 0xff
    else:
        bytes[count] = n & 0x7f

    buf[0] = bytes

    return size


cdef int decode_int(cBufferedByteStream stream, long *ret, int sign=0) except -1:
    cdef int n = 0
    cdef long result = 0
    cdef unsigned char b

    stream.read_uchar(&b)

    while b & 0x80 != 0 and n < 3:
        result <<= 7
        result |= b & 0x7f

        stream.read_uchar(&b)

        n += 1

    if n < 3:
        result <<= 7
        result |= b
    else:
        result <<= 8
        result |= b

        if result & 0x10000000 != 0:
            if sign == 1:
                result -= 0x20000000
            else:
                result <<= 1
                result += 1

    ret[0] = result

    return 0


cdef inline int _encode_integer(cBufferedByteStream stream, long i) except -1:
    cdef char *buf = NULL
    cdef int size = 0

    try:
        size = encode_int(i, &buf)

        return stream.write(buf, size)
    finally:
        PyMem_Free(buf)


cdef inline long _read_ref(cBufferedByteStream stream) except -1:
    cdef long ref

    decode_int(stream, &ref, 0)

    return ref
