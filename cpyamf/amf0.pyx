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


from cpyamf.util cimport IndexedCollection, cBufferedByteStream, BufferedByteStream
from cpyamf.context cimport BaseContext
import pyamf
from pyamf import util
import types

cdef int complete_init = 0

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

cdef PyObject *Undefined
cdef PyObject *BuiltinFunctionType = <PyObject *>types.BuiltinFunctionType
cdef PyObject *GeneratorType = <PyObject *>types.GeneratorType
cdef object encoder_type_map = {}
cdef object empty_string = str('')
cdef object amf0


cdef int complete_import() except -1:
    """
    This function is internal - do not call it yourself. It is used to
    finalise the cpyamf.util module to improve startup time.
    """
    global complete_init, amf0
    global Undefined

    import pyamf.amf0 as amf0_module

    amf0 = amf0_module

    Undefined = <PyObject *>pyamf.Undefined

    complete_init = 1
    PyDateTime_IMPORT
    encoder_type_map[util.xml_types] = 'writeXML'
    encoder_type_map[pyamf.MixedArray] = 'writeMixedArray'

    return 0


cdef class Context(BaseContext):
    """
    I hold the AMF0 context for en/decoding streams.
    """

    cdef list amf3_objs

    def __cinit__(self):
        if complete_init == 0:
            complete_import()

    def clear(self):
        """
        Clears the context.
        """
        BaseContext.clear(self)

        self.amf3_objs = []

    def hasAMF3ObjectReference(self, obj):
        """
        Gets a reference for an object.
        """
        return obj in self.amf3_objs

    cpdef int addAMF3Object(self, obj) except? -1:
        """
        Adds an AMF3 reference to C{obj}.

        @type obj: C{mixed}
        @param obj: The object to add to the context.
        @rtype: C{int}
        @return: Reference to C{obj}.
        """
        return self.amf3_objs.append(obj)
