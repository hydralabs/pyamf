from cpyamf cimport codec


cdef class ClassDefinition(object):
    """
    Holds transient class trait info for an individual encode/decode.
    """

    cdef object alias
    cdef Py_ssize_t ref
    cdef Py_ssize_t attr_len
    cdef int encoding

    cdef char *encoded_ref
    cdef Py_ssize_t encoded_ref_size

    cdef list static_properties


cdef class Context(codec.Context):
    cdef codec.IndexedCollection strings
    cdef codec.IndexedCollection legacy_xml
    cdef dict classes
    cdef dict class_ref
    cdef dict proxied_objects
    cdef Py_ssize_t class_idx

    cpdef object getString(self, Py_ssize_t ref)
    cpdef Py_ssize_t getStringReference(self, object s) except -2
    cpdef Py_ssize_t addString(self, object s) except -2

    cpdef object getLegacyXML(self, Py_ssize_t ref)
    cpdef Py_ssize_t getLegacyXMLReference(self, object doc) except -2
    cpdef Py_ssize_t addLegacyXML(self, object doc) except -1

    cpdef int addProxyObject(self, object obj, object proxied) except? -1
    cpdef object getProxyForObject(self, object obj)
    cpdef object getObjectForProxy(self, object proxy)

    cpdef object getClassByReference(self, Py_ssize_t ref)
    cpdef object getClass(self, object klass)
    cpdef Py_ssize_t addClass(self, ClassDefinition alias, klass) except? -1