# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C-extension for L{pyamf.amf3} Python module in L{PyAMF<pyamf>}.

:since: 0.6
"""

from python cimport *

cdef extern from "datetime.h":
    void PyDateTime_IMPORT()
    int PyDateTime_Check(object)
    int PyTime_Check(object)

cdef extern from "math.h":
    float floor(float)

cdef extern from "stdlib.h" nogil:
    ctypedef unsigned long size_t

    int memcmp(void *dest, void *src, size_t)
    void *memcpy(void *, void *, size_t)

cdef extern from "Python.h":
    PyObject* Py_True
    PyObject *Py_None

    bint PyClass_Check(object)
    bint PyType_CheckExact(object)


from cpyamf cimport codec, amf3, util
import pyamf
import types


cdef char TYPE_NUMBER      = '\x00'
cdef char TYPE_BOOL        = '\x01'
cdef char TYPE_STRING      = '\x02'
cdef char TYPE_OBJECT      = '\x03'
cdef char TYPE_MOVIECLIP   = '\x04'
cdef char TYPE_NULL        = '\x05'
cdef char TYPE_UNDEFINED   = '\x06'
cdef char TYPE_REFERENCE   = '\x07'
cdef char TYPE_MIXEDARRAY  = '\x08'
cdef char TYPE_OBJECTTERM  = '\x09'
cdef char TYPE_ARRAY       = '\x0A'
cdef char TYPE_DATE        = '\x0B'
cdef char TYPE_LONGSTRING  = '\x0C'
cdef char TYPE_UNSUPPORTED = '\x0D'
cdef char TYPE_RECORDSET   = '\x0E'
cdef char TYPE_XML         = '\x0F'
cdef char TYPE_TYPEDOBJECT = '\x10'
cdef char TYPE_AMF3        = '\x11'

cdef PyObject *Undefined = <PyObject *>pyamf.Undefined
cdef PyObject *BuiltinFunctionType = <PyObject *>types.BuiltinFunctionType
cdef PyObject *GeneratorType = <PyObject *>types.GeneratorType
cdef object empty_string = str('')

PyDateTime_IMPORT


cdef class Context(codec.Context):
    """
    I hold the AMF0 context for en/decoding streams.
    """

    cdef list amf3_objs

    cpdef int clear(self) except? -1:
        """
        Clears the context.
        """
        codec.Context.clear(self)

        self.amf3_objs = []

    cdef object hasAMF3ObjectReference(self, obj):
        """
        Gets a reference for an object.
        """
        return obj in self.amf3_objs

    cdef int addAMF3Object(self, obj) except -1:
        """
        Adds an AMF3 reference to C{obj}.

        @type obj: C{mixed}
        @param obj: The object to add to the context.
        @rtype: C{int}
        @return: Reference to C{obj}.
        """
        return self.amf3_objs.append(obj)


cdef class Decoder(codec.Codec):
    """
    Decodes an AMF0 stream.
    """

    cdef amf3.Decoder amf3_decoder

    def __cinit__(self):
        self.amf3_decoder = NULL

    cdef Context buildContext(self):
        return Context()

    cdef object readNumber(self):
        """
        Reads a ActionScript C{Number} value.

        In ActionScript 1 and 2 the C{NumberASTypes} type represents all numbers,
        both floats and integers.

        @rtype: C{int} or C{float}
        """
        cdef double number
        cdef int done = 0
        cdef unsigned char *buf

        self.stream.read_double(&number)
        #buf = <unsigned char *>&number

        #if floor(number) == number:
        #    if memcmp(buf, &util.system_nan, 8) == 0:
        #        done = 1
        #    elif memcmp(buf, &util.system_posinf, 8) == 0:
        #        done = 1
        #    elif memcmp(buf, &util.system_neginf, 8) == 0:
        #        done = 1

        #    if done == 0:
        #        return int(number)

        return number

    cdef object readBoolean(self):
        cdef unsigned char b

        self.stream.read_uchar(&b)

        if b == 1:
            return True
        elif b == 0:
            return False

        raise pyamf.DecodeError('Unexpected value when decoding boolean')

    cdef inline object readNull(self):
        return None

    cdef inline object readUndefined(self):
        return <object>Undefined

    def readMixedArray(self):
        """
        Read mixed array.

        @rtype: C{dict}
        @return: C{dict} read from the stream
        """
        cdef unsigned long l

        self.stream.read_ulong(&l)

        obj = pyamf.MixedArray()
        self.context.addObject(obj)
        self._readObject(obj)
        ikeys = []

        for key in obj.keys():
            try:
                ikey = int(key)
                ikeys.append((key, ikey))
                obj[ikey] = obj[key]
                del obj[key]
            except ValueError:
                # XXX: do we want to ignore this?
                pass

        ikeys.sort()

        return obj

    cdef object readList(self):
        """
        Read a C{list} from the data stream.

        @rtype: C{list}
        @return: C{list}
        """
        cdef unsigned long l
        cdef list obj = []

        self.context.addObject(obj)
        self.stream.read_ulong(&l)

        for 0 <= i < l:
            PyList_Append(obj, self.readElement())

        return obj

    def readTypedObject(self):
        """
        Reads an ActionScript object from the stream and attempts to
        'cast' it.

        @see: L{load_class<pyamf.load_class>}
        """
        classname = self.readString()
        alias = None

        try:
            alias = pyamf.get_class_alias(classname)

            ret = alias.createInstance(codec=self)
        except pyamf.UnknownClassAlias:
            if self.strict:
                raise

            ret = pyamf.TypedObject(classname)

        self.context.addObject(ret)
        self._readObject(ret, alias)

        return ret

    cdef inline amf3.Decoder _getAMF3Decoder(self):
        if self.amf3_decoder == NULL:
            self.amf3_decoder = amf3.Decoder(self.stream)

        return self.amf3_decoder

    cdef object readAMF3(self):
        """
        Read AMF3 elements from the data stream.

        @rtype: C{mixed}
        @return: The AMF3 element read from the stream
        """
        cdef amf3.Decoder decoder = self._getAMF3Decoder()
        cdef object element = decoder.readElement()

        self.context.addAMF3Object(element)

        return element

    cdef inline char *readBytes(self, bint big=0) except NULL:
        cdef Py_ssize_t l
        char *buf = NULL

        if not big:
            self.stream.read_ushort(&<unsigned short>l)
        else:
            self.stream.read_ulong(&<unsigned long>l)

        self.stream.read(buf, l)

        return buf

    cdef object readString(self, bint big=0):
        """
        Reads a C{string} from the stream.
        """
        cdef char *buf = self.readBytes(big)
        cdef object s

        try:
            s = PyString_FromStringAndSize(buf, r)
        finally:
            if buf != NULL:
                free(buf)

        return s

    cdef object readUnicode(self, bint big=0):
        """
        Reads a C{unicode} from the data stream.
        """
        cdef char *bytes = self.readBytes(big)

        try:
            return self.context.getUnicodeForString(bytes)
        finally:
            free(bytes)

    cdef int _readObject(self, obj, alias=None) except -1:
        cdef dict obj_attrs = {}
        cdef char *key

        while self.stream.peek() != TYPE_OBJECTTERM:
            key = self.readBytes()
            # change to PyDict_SetString()
            obj_attrs[key] = self.readElement()
            free(key)

        # discard the end marker (TYPE_OBJECTTERM)
        self.stream.read(1)

        if alias:
            alias.applyAttributes(obj, obj_attrs, codec=self)
        else:
            util.set_attrs(obj, obj_attrs)

    cdef object readObject(self):
        """
        Reads an object from the data stream.

        @rtype: L{ASObject<pyamf.ASObject>}
        """
        obj = pyamf.ASObject()
        self.context.addObject(obj)

        self._readObject(obj)

        return obj

    cdef object readReference(self):
        """
        Reads a reference from the data stream.

        @raise pyamf.ReferenceError: Unknown reference.
        """
        cdef unsigned short idx

        self.stream.read_ushort(&idx)
        o = self.context.getObject(idx)

        if o is None:
            raise pyamf.ReferenceError('Unknown reference %d' % (idx,))

        return o

    cdef object readDate(self):
        """
        Reads a UTC date from the data stream. Client and servers are
        responsible for applying their own timezones.

        Date: C{0x0B T7 T6} .. C{T0 Z1 Z2 T7} to C{T0} form a 64 bit
        Big Endian number that specifies the number of nanoseconds
        that have passed since 1/1/1970 0:00 to the specified time.
        This format is UTC 1970. C{Z1} and C{Z0} for a 16 bit Big
        Endian number indicating the indicated time's timezone in
        minutes.
        """
        cdef double ms
        cdef short s

        self.stream.read_double(&ms)
        self.stream.read_short(&s)

        # Timezones are ignored
        d = util.get_datetime(ms / 1000.0)

        if self.timezone_offset:
            d = d + self.timezone_offset

        self.context.addObject(d)

        return d

    cdef char *readLongString(self) except NULL:
        """
        Read UTF8 string.
        """
        cdef unsigned long l
        cdef char *buf
        cdef object s

        self.stream.read_ulong(&l)

        try:
            self.stream.read(&buf, l)
        except:
            if buf != NULL:
                PyMem_Free(buf)

        return buf

    def readXML(self):
        """
        Read XML.
        """
        cdef char *data = self.readLongString()

        try:
            xml = util.ET.fromstring(data)
            self.context.addObject(xml)
        finally:
            if data != NULL:
                PyMem_Free(data)

        return xml

    cpdef object readElement(self):
        """
        Reads an AMF3 element from the data stream.

        @raise DecodeError: The ActionScript type is unsupported.
        @raise EOStream: No more data left to decode.
        """
        cdef Py_ssize_t pos = self.stream.tell()
        cdef char t

        if self.stream.at_eof():
            raise pyamf.EOStream

        self.stream.read_char(&t)

        try:
            if t == TYPE_NUMBER:
                return self.readNumber()
            elif t == TYPE_BOOL:
                return self.readBoolean()
            elif t == TYPE_STRING:
                return self.readUnicode()
            elif t == TYPE_OBJECT:
                return self.readObject()
            elif t == TYPE_ARRAY:
                return self.readArray()
            elif t == TYPE_NULL:
                return None
            elif t == TYPE_UNDEFINED:
                return pyamf.Undefined
            elif t == TYPE_DATE:
                return self.readDate()
            elif t == TYPE_XML:
                return self.readXML()
        except IOError:
            self.stream.seek(pos)

            raise

        raise pyamf.DecodeError("Unsupported ActionScript type")


cdef class Encoder(codec.Codec):
    """
    The AMF0 Encoder.
    """

    cdef bint use_amf3
    cdef amf3.Encoder amf3_encoder
    cdef object _func_cache
    cdef object _use_write_object # list of types that are okay to short circuit to writeObject

    type_map = {
        util.xml_types: 'writeXML'
    }

    property use_amf3:
        def __get__(self):
            return self.use_amf3

        def __set__(self, value):
            self.use_amf3 = value

    def __init__(self, stream=None, context=None, strict=False, timezone_offset=None, use_amf3=False):
        codec.Codec.__init__(self, stream, context, strict, timezone_offset)

        self.use_amf3 = use_amf3

        self._func_cache = {}
        self._use_write_object = []

    cdef Context buildContext(self):
        return Context()

    cdef inline int writeType(self, char type) except -1:
        return self.stream.write(<char *>&type, 1)

    cdef int writeBoolean(self, b) except -1:
        """
        Write boolean to the data stream.

        @type b: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param b: The boolean data to be encoded to the AMF0 data stream.
        """
        self.writeType(TYPE_BOOL)

        if b is True:
            self.writeType('\x01')
        else:
            self.writeType('\x00')

    cdef int writeList(self, list a) except -1:
        """
        Write array to the stream.

        @type a: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param a: The array data to be encoded to the AMF0 data stream.
        """
        alias = self.context.getClassAlias(a.__class__)

        if alias.external:
            # a is a subclassed list with a registered alias - push to the
            # correct method
            self.writeObject(a)

            return 0

        if self.writeReference(a) != -1:
            return 0

        self.context.addObject(a)

        self.writeType(TYPE_ARRAY)
        self.stream.write_ulong(len(a))

        for data in a:
            self.writeElement(data)

        return 0

    cdef int writeNumber(self, n) except -1:
        """
        Write number to the data stream.

        @type   n: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param  n: The number data to be encoded to the AMF0 data stream.
        """
        self.writeType(TYPE_NUMBER)
        return self.stream.write_double(float(n))

    cpdef int writeString(self, s, bint writeType=1) except -1:
        """
        Write string to the data stream.

        @type s: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param s: The string data to be encoded to the AMF0 data stream.
        @type writeType: C{bool}
        @param writeType: Write data type.
        """
        cdef Py_ssize_t l = len(s)

        if writeType == 1:
            if l > 0xffff:
                self.writeType(TYPE_LONGSTRING)
            else:
                self.writeType(TYPE_STRING)

        if l > 0xffff:
            self.stream.write_ulong(l)
        else:
            self.stream.write_ushort(l)

        self.stream.write(s, l)

    def writeLabel(self, s):
        self.writeString(s, False)

    cdef int writeUnicode(self, u, bint writeType=1) except -1:
        """
        Write a unicode to the data stream.
        """
        cdef object s = self.context.getStringForUnicode(u)

        return self.writeString(s, writeType)

    cpdef inline int writeReference(self, o) except -2:
        """
        Write reference to the data stream.

        @type o: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param o: The reference data to be encoded to the AMF0 data
            stream.
        """
        cdef Py_ssize_t idx = self.context.getObjectReference(o)

        if idx == -1 or idx > 65535:
            return -1

        self.writeType(TYPE_REFERENCE)

        return self.stream.write_ushort(idx)

    cdef int _writeDict(self, o) except -1:
        """
        Write C{dict} to the data stream.

        @type o: C{iterable}
        @param o: The C{dict} data to be encoded to the AMF0 data
            stream.
        """
        for key, val in o.iteritems():
            self.writeString(key, False)
            self.writeElement(val)

        return 0

    cdef int writeMixedArray(self, o) except -1:
        """
        Write mixed array to the data stream.

        @type o: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param o: The mixed array data to be encoded to the AMF0
            data stream.
        """
        if self.writeReference(o) != -1:
            return 0

        self.context.addObject(o)
        self.writeType(TYPE_MIXEDARRAY)

        # TODO: optimise this
        # work out the highest integer index
        try:
            # list comprehensions to save the day
            max_index = max([y[0] for y in o.items()
                if isinstance(y[0], (int, long))])

            if max_index < 0:
                max_index = 0
        except ValueError:
            max_index = 0

        self.stream.write_ulong(max_index)

        self._writeDict(o)
        self._writeEndObject()

    cdef inline int _writeEndObject(self) except -1:
        self.stream.write('\x00\x00', 2)

        return self.writeType(TYPE_OBJECTTERM)

    cpdef int writeObject(self, o) except -1:
        """
        Write object to the stream.

        @type o: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param o: The object data to be encoded to the AMF0 data stream.
        """
        if self.use_amf3:
            return self.writeAMF3(o)

        if self.writeReference(o) != -1:
            return 0

        self.context.addObject(o)
        alias = self.context.getClassAlias(o.__class__)

        alias.compile()

        if alias.amf3:
            return self.writeAMF3(o)

        if alias.anonymous:
            self.writeType(TYPE_OBJECT)
        else:
            self.writeType(TYPE_TYPEDOBJECT)
            self.writeString(alias.alias, False)

        attrs = alias.getEncodableAttributes(o, codec=self)

        if alias.static_attrs and attrs:
            for key in alias.static_attrs:
                value = attrs.pop(key)

                self.writeString(key, False)
                self.writeElement(value)

        if attrs:
            for key, value in attrs.iteritems():
                self.writeString(key, False)
                self.writeElement(value)

        return self._writeEndObject()

    def writeDate(self, d):
        """
        Writes a date to the data stream.

        @type d: Instance of C{datetime.datetime}
        @param d: The date to be encoded to the AMF0 data stream.
        """
        # According to the Red5 implementation of AMF0, dates references are
        # created, but not used.
        if self.timezone_offset is not None:
            d -= self.timezone_offset

        secs = util.get_timestamp(d)
        tz = 0

        self.writeType(TYPE_DATE)
        self.stream.write_double(secs * 1000.0)
        self.stream.write_short(tz)

    def writeXML(self, e):
        """
        Write XML to the data stream.

        @type e: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param e: The XML data to be encoded to the AMF0 data stream.
        """
        if self.use_amf3 is True:
            self.writeAMF3(e)

            return

        self.writeType(TYPE_XML)

        data = util.ET.tostring(e, 'utf-8')
        self.stream.write_ulong(len(data))
        self.stream.write(data, len(data))

    cdef amf3.Encoder _getAMF3Encoder(self):
        if self.amf3_encoder:
            return self.amf3_encoder

        self.amf3_encoder = amf3.Encoder(self.stream)

        return self.amf3_encoder

    cdef int writeAMF3(self, data) except -1:
        """
        Writes an element to the datastream in L{AMF3<pyamf.amf3>} format.

        @type data: C{mixed}
        @param data: The data to be encoded to the AMF0 data stream.
        """
        cdef amf3.Encoder encoder = self._getAMF3Encoder()

        self.context.addAMF3Object(data)
        self.writeType(TYPE_AMF3)

        return encoder.writeElement(data)

    cpdef int writeElement(self, object element) except -1:
        cdef int ret = 0
        cdef object py_type = type(element)
        cdef PyObject *func = NULL

        if PyString_CheckExact(element):
            ret = self.writeString(element, 1)
        elif PyUnicode_CheckExact(element):
            ret = self.writeUnicode(element, 1)
        elif <PyObject *>element == Py_None:
            ret = self.writeType(TYPE_NULL)
        elif PyBool_Check(element):
            ret = self.writeBoolean(element)
        elif PyInt_CheckExact(element):
            ret = self.writeNumber(element)
        elif PyLong_CheckExact(element):
            ret = self.writeNumber(element)
        elif PyFloat_CheckExact(element):
            ret = self.writeNumber(element)
        elif PyList_CheckExact(element):
            ret = self.writeList(element)
        elif PyTuple_CheckExact(element):
            ret = self.writeTuple(element)
        elif <PyObject *>element == Undefined:
            ret = self.writeType(TYPE_UNDEFINED)
        elif PyDict_CheckExact(element):
            ret = self.writeObject(element)
        elif PyDateTime_Check(element):
            ret = self.writeDateTime(element)
        elif <PyObject *>py_type == <PyObject *>pyamf.MixedArray:
            ret = self.writeMixedArray(element)
        elif PySequence_Contains(self._use_write_object, py_type):
            return self.writeObject(element)
        elif self.use_amf3 and self.context.hasAMF3ObjectReference(element):
            # There is a very specific use case that we must check for.
            # In the context there is an array of amf3_objs that contain
            # references to objects that are to be encoded in amf3.
            ret = self.writeAMF3(element)
        else:
            func = PyDict_GetItem(self._func_cache, py_type)

            if func == NULL:
                func = self.getCustomTypeFunc(element)

                if func == NULL:
                    f = self.getTypeMapFunc(element)

                    if f is None:
                        if PyModule_CheckExact(element):
                            raise pyamf.EncodeError("Cannot encode modules")
                        elif PyMethod_Check(element):
                            raise pyamf.EncodeError("Cannot encode methods")
                        elif PyFunction_Check(element) or <PyObject *>py_type == BuiltinFunctionType:
                            raise pyamf.EncodeError("Cannot encode functions")
                        elif <PyObject *>py_type == GeneratorType:
                            raise pyamf.EncodeError("Cannot encode generators")
                        elif PyClass_Check(element) or PyType_CheckExact(element):
                            raise pyamf.EncodeError("Cannot encode class objects")
                        elif PyTime_Check(element):
                            raise pyamf.EncodeError('A datetime.time instance was found but '
                                'AMF3 has no way to encode time objects. Please use '
                                'datetime.datetime instead ')

                        PyList_Append(self._use_write_object, py_type)

                        return self.writeObject(element)

                    func = <PyObject *>f

                PyDict_SetItem(self._func_cache, py_type, <object>func)

            (<object>func)(element)

        return ret
