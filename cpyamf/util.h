#ifndef CPYAMF_UTIL_H
#define CPYAMF_UTIL_H

#ifdef __cpluscplus
extern "C" {
#endif
/**
 *
 * util.h
 *
 * Defines the BufferedByteStream.
 *
 **/
#include <Python.h>

#define CPYAMF_UTIL_IMPORT                                                   \
	cPyAmf_BufferedByteStream = (struct cPyAmf_BufferedByteStream_CAPI*)     \
                                PyCObject_Import("cpyamf.util",              \
                                                 "BufferedByteStream_CAPI");

typedef struct {
    PyObject_HEAD
    PyObject* buffer; /* cStringIO buffer */
    char endian;
} BufferedByteStream;

static struct cPyAmf_BufferedByteStream_CAPI {
	// TODO: Add more methods here as deemed necessary.
	int (*init)(PyObject*, PyObject*, int); /* (self, buf_obj, rewind) */
	PyTypeObject* Type;
} *cPyAmf_BufferedByteStream;


#define ENDIAN_NETWORK '!'
#define ENDIAN_NATIVE '@'
#define ENDIAN_LITTLE '<'
#define ENDIAN_BIG '>'



#define BufferedByteStream_Check(O) ((O)->ob_type==cPyAmf_BufferedByteStream->Type)
#ifdef __cpluscplus
}
#endif
#endif /* !CPYAMF_UTIL_H */
