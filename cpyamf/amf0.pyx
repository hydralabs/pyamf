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

cdef extern from "Python.h":
    PyObject* Py_True
    PyObject *Py_None

    bint PyClass_Check(object)
    bint PyType_CheckExact(object)


from cpyamf.util cimport cBufferedByteStream, BufferedByteStream
from cpyamf cimport codec, amf3
import pyamf
from pyamf import util
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

    cpdef object hasAMF3ObjectReference(self, obj):
        """
        Gets a reference for an object.
        """
        return obj in self.amf3_objs

    cpdef int addAMF3Object(self, obj) except -1:
        """
        Adds an AMF3 reference to C{obj}.

        @type obj: C{mixed}
        @param obj: The object to add to the context.
        @rtype: C{int}
        @return: Reference to C{obj}.
        """
        return self.amf3_objs.append(obj)


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
