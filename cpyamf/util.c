#include <Python.h>

#include "util.h"

#include <cStringIO.h>
#include <stdio.h>
#include <structmember.h>

#if PY_VERSION_HEX < 0x02050000 && !defined(PY_SSIZE_T_MIN)
typedef int Py_ssize_t;
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
#endif

/* Useful Forward Declarations */
static PyObject * BufferedByteStream_tell(BufferedByteStream *);
static PyObject * BufferedByteStream_at_eof(BufferedByteStream *);
static PyObject * BufferedByteStream_remaining(BufferedByteStream *);
static PyObject * BufferedByteStream_seek(BufferedByteStream *, PyObject *, PyObject *);
static PyObject * BufferedByteStream_peek(BufferedByteStream *, PyObject *, PyObject *);
static PyObject * BufferedByteStream_read(BufferedByteStream *, PyObject *, PyObject *);
static PyObject * BufferedByteStream_readline(BufferedByteStream *);
static PyObject * BufferedByteStream_readlines(BufferedByteStream *, PyObject *, PyObject *);
static PyObject * BufferedByteStream_write(BufferedByteStream *, PyObject *);
static PyObject * BufferedByteStream_writelines(BufferedByteStream *, PyObject *);
static PyObject * BufferedByteStream_getvalue(BufferedByteStream *);
static PyObject * BufferedByteStream_truncate(BufferedByteStream *, PyObject *, PyObject *);
static PyObject * BufferedByteStream_flush(BufferedByteStream *);
static PyObject * BufferedByteStream_close(BufferedByteStream *);
static int BufferedByteStream_init_(BufferedByteStream *, PyObject *, int);

staticforward PyTypeObject BufferedByteStreamType;
#undef BufferedByteStream_Check
#define BufferedByteStream_Check(O) ((O)->ob_type==&BufferedByteStreamType)

/**
 * Utility Functions
 **/

static int
get_long(PyObject *v, long *p)
{
    long x;

    x = PyLong_AsLong(v);
    if (x == -1 && PyErr_Occurred()) {
        return -1;
    }
    *p = x;
    return 0;
}

static int
get_ulong(PyObject *v, unsigned long *p)
{
    unsigned long x;
    PyObject* py_long;
    
    py_long = PyNumber_Long(v);
    if (py_long==NULL)
    {
        PyErr_SetNone(PyExc_ValueError);
        return -1;
    }

    x = PyLong_AsUnsignedLong(py_long);
    Py_XDECREF(py_long);
    if (PyErr_Occurred()) {
        return -1;
    }
    *p = x;
    return 0;
}

static PyObject *
unpack_uint(BufferedByteStream *self, const char *buf, long num_bytes)
{
    unsigned long x;
    const unsigned char *bytes;

    x = 0;
    bytes = (const unsigned char *) buf;
    do
    {
        if ( (self->endian==ENDIAN_BIG) ||
             (self->endian==ENDIAN_NETWORK) )
        {
            x = (x<<8) | *bytes++;
        }
        else
        {
            x = (x<<8) | bytes[num_bytes-1];
        }        
    } while (--num_bytes > 0);
    return PyLong_FromUnsignedLong(x);
}

static PyObject *
unpack_int(BufferedByteStream *self, const char *buf, long num_bytes)
{
    long x;
    long bytes_left;
    const unsigned char *bytes;

    x = 0;
    bytes_left = num_bytes;
    bytes = (const unsigned char *) buf;
    do
    {
        if ( (self->endian==ENDIAN_BIG) ||
             (self->endian==ENDIAN_NETWORK) )
        {
            x = (x<<8) | *bytes++;
        }
        else
        {
            x = (x<<8) | bytes[bytes_left-1];
        }        
    } while (--bytes_left > 0);
    /* Extend the sign bit. */
    if (SIZEOF_LONG > num_bytes)
    {
        x |= -(x & (1L << ((8 *num_bytes) - 1)));
    }
    return PyLong_FromLong(x);
}

static int
pack_uint(BufferedByteStream *self, unsigned long x, long num_bytes)
{
    char buf[num_bytes];

    if (num_bytes != SIZEOF_LONG) {
        unsigned long maxint = 1;
        maxint <<= (unsigned long)(num_bytes * 8);
        if (x >= maxint)
        {
            PyErr_SetString(PyExc_OverflowError, "integer out of range");
            return -1;
        }
    }
    long i=num_bytes; 
    while(i>0)
    {
        switch(self->endian)
        {
            case ENDIAN_BIG:
            case ENDIAN_NETWORK:
                buf[--i] = (char)x;
                break;
            case ENDIAN_LITTLE:
                buf[num_bytes-i] = (char)x;
                i--;
                break;
            case ENDIAN_NATIVE:
                buf[num_bytes-i] = ((char *)&x)[num_bytes-i];
                i--;
        }
        x >>= 8;
    }
    PycStringIO->cwrite(self->buffer, buf, num_bytes);
    return 0;
}

static int
pack_int(BufferedByteStream *self, long x, long num_bytes)
{
    char buf[num_bytes];

    if (num_bytes != SIZEOF_LONG) {
        long maxint = 1;
        long minint = -1;
        maxint <<= (unsigned long)((num_bytes * 8)-1);
        minint = (-maxint);
        if ((x >= maxint) || (x < minint))
        {
            PyErr_SetString(PyExc_OverflowError, "integer out of range");
            return -1;
        }
    }
    long i=num_bytes; 
    while(i>0)
    {
        switch(self->endian)
        {
            case ENDIAN_BIG:
            case ENDIAN_NETWORK:
                buf[--i] = ((char *)&x)[0];
                break;
            case ENDIAN_LITTLE:
                buf[num_bytes-i] = ((char *)&x)[0];
                i--;
                break;
            case ENDIAN_NATIVE:
                buf[num_bytes-i] = ((char *)&x)[num_bytes-i];
                i--;
        }
        x >>= 8;
    }
    PycStringIO->cwrite(self->buffer, buf, num_bytes);
    return 0;
}

/**
 * BufferedByteStream methods
 **/
static void
BufferedByteStream_dealloc(BufferedByteStream *self)
{
    Py_XDECREF(self->buffer);
    self->ob_type->tp_free((PyObject *)self);
}

static PyObject *
BufferedByteStream_tell(BufferedByteStream *self)
{
    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    return PyObject_CallMethod(self->buffer, "tell", NULL);
}

static PyObject *
BufferedByteStream_at_eof(BufferedByteStream *self)
{
    PyObject *obj_remaining, *result;
    long remaining;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    /* at_eof <=> remaining==0 */

    obj_remaining = BufferedByteStream_remaining(self);
    remaining = PyInt_AsLong(obj_remaining);
    Py_XDECREF(obj_remaining);

    result = PyBool_FromLong(remaining==0);
    Py_INCREF(result);

    return result;
}

static PyObject *
BufferedByteStream_remaining(BufferedByteStream *self)
{
    PyObject *cur_pos, *end_pos, *tmp, *result;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    cur_pos = BufferedByteStream_tell(self);

    PyObject_CallMethod(self->buffer, "seek", "ii", 0, 2);
    end_pos = BufferedByteStream_tell(self);

    tmp = PyObject_CallMethod(self->buffer, "seek", "Oi", cur_pos, 0);
    Py_XDECREF(tmp);

    result = PyNumber_Subtract(end_pos, cur_pos);
    Py_XDECREF(end_pos);
    Py_XDECREF(cur_pos);

    return result;
}

static PyObject *
BufferedByteStream_seek(BufferedByteStream *self, PyObject *args, PyObject *kwargs)
{
    PyObject *obj_pos = NULL;
    PyObject *obj_mode = NULL;
    static char *kwlist[] = {"pos", "mode", NULL};

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|O", kwlist, &obj_pos, &obj_mode))
        return NULL;

    if (!obj_mode)
        obj_mode = PyInt_FromLong(0);

    return PyObject_CallMethod(self->buffer, "seek", "OO", obj_pos, obj_mode);
}

static PyObject *
BufferedByteStream_peek(BufferedByteStream *self, PyObject *args, PyObject *kwargs)
{
    PyObject *obj_size = NULL;
    static char *kwlist[] = {"size", NULL};

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", kwlist, &obj_size))
        return NULL;

    long size = 1;
    if (obj_size)
        size = PyInt_AsLong(obj_size);

    if (size==-1 && PyErr_Occurred())
        return NULL;

    PyObject *old_pos = BufferedByteStream_tell(self);

    char *buf = NULL;
    size = PycStringIO->cread(self->buffer, &buf, size);
    PyObject *result = PyString_FromStringAndSize(buf, size);

    PyObject_CallMethod(self->buffer, "seek", "Oi", old_pos, 0);
    Py_XDECREF(old_pos);

    return result;
}

static PyObject *
BufferedByteStream_read(BufferedByteStream *self, PyObject *args, PyObject *kwargs)
{
    PyObject *obj_n = NULL;
    static char *kwlist[] = {"n", NULL};
    long n = -1;
    char *buf = NULL;
    long chars_received;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", kwlist, &obj_n))
        return NULL;

    if (obj_n)
        n = PyInt_AsLong(obj_n);

    if (n==-1 && PyErr_Occurred())
        return NULL;

    chars_received = PycStringIO->cread(self->buffer, &buf, n);
    if (n>chars_received)
    {
        if(chars_received>0)
            PyErr_SetNone(PyExc_IOError);
        else
            PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }
    return PyString_FromStringAndSize(buf, chars_received);
}

static PyObject *
BufferedByteStream_readline(BufferedByteStream *self)
{
    char *buf = NULL;
    long len;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    len = PycStringIO->creadline(self->buffer, &buf);
    return PyString_FromStringAndSize(buf, len);
}

static PyObject *
BufferedByteStream_readlines(BufferedByteStream *self, PyObject *args, PyObject *kwargs)
{
    PyObject *obj_sizehint = NULL;
    static char *kwlist[] = {"sizehint", NULL};
    long sizehint = 0;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", kwlist, &obj_sizehint))
        return NULL;

    if (obj_sizehint)
        sizehint = PyInt_AsLong(obj_sizehint);

    if (sizehint==-1 && PyErr_Occurred())
        return NULL;

    return PyObject_CallMethod(self->buffer, "readlines", "i", sizehint);
}

static PyObject *
BufferedByteStream_write(BufferedByteStream *self, PyObject *obj)
{
    char *buffer;
    Py_ssize_t length;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if(PyString_AsStringAndSize(obj, &buffer, &length))
        return NULL;

    PycStringIO->cwrite(self->buffer, buffer, length);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_writelines(BufferedByteStream *self, PyObject *iterable)
{
    PyObject *tmp;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    tmp = PyObject_CallMethod(self->buffer, "writelines", "O", iterable);
    Py_XDECREF(tmp);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_getvalue(BufferedByteStream *self)
{
    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    return PyObject_CallMethod(self->buffer, "getvalue", "");
}

static PyObject *
BufferedByteStream_truncate(BufferedByteStream *self, PyObject *args, PyObject * kwargs)
{
    PyObject *obj_size = NULL;
    static char *kwlist[] = {"size", NULL};

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", kwlist, &obj_size))
        return NULL;

    if (!obj_size)
        obj_size = PyInt_FromLong(0);
    
    Py_XDECREF(self->buffer);
    self->buffer = NULL;

    BufferedByteStream_init_(self, NULL, 0); 

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_flush(BufferedByteStream *self)
{
    PyObject *tmp;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    tmp = PyObject_CallMethod(self->buffer, "flush", NULL);
    Py_XDECREF(tmp);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_close(BufferedByteStream *self)
{
    if(self->buffer)
    {
        PyObject *tmp = PyObject_CallMethod(self->buffer, "close", NULL);
        Py_XDECREF(tmp);

        tmp = self->buffer;
        self->buffer = NULL;
        Py_XDECREF(tmp);
    }

    Py_INCREF(Py_None);
    return Py_None;
}


/**
 * BufferedByteStream Type Read/Write Methods
 **/
static PyObject *
BufferedByteStream_read_uchar(BufferedByteStream *self)
{
    char *buf = NULL;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (PycStringIO->cread(self->buffer, &buf, 1) != 1)
    {
        PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }

    return PyInt_FromLong((long) *(unsigned char *)buf);
}

static PyObject *
BufferedByteStream_write_uchar(BufferedByteStream *self, PyObject *c)
{
    unsigned long val;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (get_ulong(c, &val))
        return NULL;
    if (val < 0 || val > 255)
    {
        PyErr_SetString(PyExc_OverflowError, "uchar not in range");
        return NULL;
    }

    PycStringIO->cwrite(self->buffer, (char *)&val, 1);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_read_char(BufferedByteStream *self)
{
    char *buf = NULL;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if(PycStringIO->cread(self->buffer, &buf, 1) != 1)
    {
        PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }
    return PyInt_FromLong((long) *(char *)buf);
}

static PyObject *
BufferedByteStream_write_char(BufferedByteStream *self, PyObject *c)
{
    long val;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (get_long(c, &val))
        return NULL;
    if (val < -128 || val > 127)
    {
        PyErr_SetString(PyExc_OverflowError, "char not in range");
        return NULL;
    }

    PycStringIO->cwrite(self->buffer, (char *)&val, 1);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_read_ushort(BufferedByteStream *self)
{
    char *buf = NULL;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (PycStringIO->cread(self->buffer, &buf, 2) != 2)
    {
        PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }
    return unpack_uint(self, buf, 2);
}

static PyObject *
BufferedByteStream_write_ushort(BufferedByteStream *self, PyObject *c)
{
    unsigned long val;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (get_ulong(c, &val))
        return NULL;
    if (val < 0 || val > 65535)
    {
        PyErr_SetString(PyExc_OverflowError, "ushort not in range");
        return NULL;
    }
    if (pack_uint(self, val, 2))
        return NULL;
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_read_short(BufferedByteStream *self)
{
    char *buf = NULL;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (PycStringIO->cread(self->buffer, &buf, 2) != 2)
    {
        PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }
    return unpack_int(self, buf, 2);
}

static PyObject *
BufferedByteStream_write_short(BufferedByteStream *self, PyObject *c)
{
    long val;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (get_long(c, &val))
        return NULL;
    if (val < -32768 || val > 32767)
    {
        PyErr_SetString(PyExc_OverflowError, "short not in range");
        return NULL;
    }
    if (pack_int(self, val, 2))
        return NULL;
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_read_ulong(BufferedByteStream *self)
{
    char *buf = NULL;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (PycStringIO->cread(self->buffer, &buf, 4) != 4)
    {
        PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }

    return unpack_uint(self, buf, 4);
}

static PyObject *
BufferedByteStream_write_ulong(BufferedByteStream *self, PyObject *c)
{
    unsigned long val;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (get_ulong(c, &val))
        return NULL;
    if (pack_uint(self, val, 4))
        return NULL;
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_read_long(BufferedByteStream *self)
{
    char *buf = NULL;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    PycStringIO->cread(self->buffer, &buf, 4);
    return unpack_int(self, buf, 4);
}

static PyObject *
BufferedByteStream_write_long(BufferedByteStream *self, PyObject *c)
{
    long val;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (get_long(c, &val))
        return NULL;

    if (pack_int(self, val, 4))
        return NULL;

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_read_float(BufferedByteStream *self)
{
    float x;
    char *buf;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (PycStringIO->cread(self->buffer, &buf, 4) != 4)
    {
        PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }

    switch(self->endian)
    {
        case ENDIAN_NATIVE:
            memcpy((char *)&x, buf, 4);
            break;
        case ENDIAN_NETWORK:
        case ENDIAN_BIG:
            x = _PyFloat_Unpack4((unsigned char *) buf, 0);
            break;
        case ENDIAN_LITTLE:
            x = _PyFloat_Unpack4((unsigned char *) buf, 1);
            break;
    }
    return PyFloat_FromDouble(x);
}

static PyObject *
BufferedByteStream_write_float(BufferedByteStream *self, PyObject *c)
{
    char buf[8];
    double x;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    x = PyFloat_AsDouble(c);
    if(PyErr_Occurred())
    {
        return NULL;
    }

    switch(self->endian)
    {
        case ENDIAN_NATIVE:
            memcpy(buf, (char *)&x, 4);
            break;
        case ENDIAN_NETWORK:
        case ENDIAN_BIG:
            _PyFloat_Pack4(x, (unsigned char *) buf, 0);
            break;
        case ENDIAN_LITTLE:
            _PyFloat_Pack4(x, (unsigned char *) buf, 1);
            break;
    }
    PycStringIO->cwrite(self->buffer, (char *)&buf, 4);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_read_double(BufferedByteStream *self)
{
#if (PY_VERSION_HEX < 0x02050000)
    static const unsigned char NaN[8] =    {0xff, 0xf8, 0, 0, 0, 0, 0, 0};
    static const unsigned char NegInf[8] = {0xff, 0xf0, 0, 0, 0, 0, 0, 0};
    static const unsigned char PosInf[8] = {0x7f, 0xf0, 0, 0, 0, 0, 0, 0};
    static int pyfloat_tested = 0;
    static int pyfloat_broken = 0;
#endif

    double x;
    char *buf;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    if (PycStringIO->cread(self->buffer, &buf, 8) != 8)
    {
        PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }

#if (PY_VERSION_HEX < 0x02050000)
    if (!pyfloat_tested)
    {
        double test;

        test = _PyFloat_Unpack8(NaN, 0);

        pyfloat_broken = memcmp(NaN, &test, 8);
        pyfloat_tested = 1;
    }

    if (pyfloat_broken)
    {
        static unsigned int one = 1;
        int big_endian = ((char*)&one)[0] != 1;
        if (memcmp(NaN, buf, 8)==0)
        {
            if (big_endian)
            {
                static const unsigned char real_NaN[8] = {0x7f, 0xf8, 0, 0, 0, 0, 0, 0}; 
                return PyFloat_FromDouble(*((double*)real_NaN));
            }
            else
            {
                static const unsigned char real_NaN[8] = {0, 0, 0, 0, 0, 0, 0xf8, 0xff}; 
                return PyFloat_FromDouble(*((double*)real_NaN));
            }
        }
        else if (memcmp(NegInf, buf, 8)==0)
        {
            if (big_endian)
            {
                static const unsigned char real_PosInf[8] = {0x7f, 0xf0, 0, 0, 0, 0, 0, 0}; 
                return PyFloat_FromDouble(-*((double*)real_PosInf));
            }
            else
            {
                static const unsigned char real_PosInf[8] = {0, 0, 0, 0, 0, 0, 0xf0, 0x7f}; 
                return PyFloat_FromDouble(-*((double*)real_PosInf));
            }
        }
        else if (memcmp(PosInf, buf, 8)==0)
        {
            if (big_endian)
            {
                static const unsigned char real_PosInf[8] = {0x7f, 0xf0, 0, 0, 0, 0, 0, 0}; 
                return PyFloat_FromDouble(*((double*)real_PosInf));
            }
            else
            {
                static const unsigned char real_PosInf[8] = {0, 0, 0, 0, 0, 0, 0xf0, 0x7f}; 
                return PyFloat_FromDouble(*((double*)real_PosInf));
            }
        }
    }

#endif

    switch(self->endian)
    {
        case ENDIAN_NATIVE:
            memcpy((char *)&x, buf, 8);
            break;
        case ENDIAN_NETWORK:
        case ENDIAN_BIG:
            x = _PyFloat_Unpack8((unsigned char *) buf, 0);
            break;
        case ENDIAN_LITTLE:
            x = _PyFloat_Unpack8((unsigned char *) buf, 1);
            break;
    }

    return PyFloat_FromDouble(x);
}

static PyObject *
BufferedByteStream_write_double(BufferedByteStream *self, PyObject *c)
{
    char buf[8];
    double x;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    x = PyFloat_AsDouble(c);
    if(PyErr_Occurred())
    {
        return NULL;
    }

    switch(self->endian)
    {
        case ENDIAN_NATIVE:
            memcpy(buf, (char *)&x, 8);
            break;
        case ENDIAN_NETWORK:
        case ENDIAN_BIG:
            _PyFloat_Pack8(x, (unsigned char *) buf, 0);
            break;
        case ENDIAN_LITTLE:
            _PyFloat_Pack8(x, (unsigned char *) buf, 1);
            break;
    }

    PycStringIO->cwrite(self->buffer, (char *)&buf, 8);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
BufferedByteStream_read_utf8_string(BufferedByteStream *self, PyObject *len)
{
    long num_bytes;
    char* buf = NULL;
    long n;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }

    num_bytes = PyInt_AsLong(len);
    if (num_bytes==-1)
        return NULL;

    buf = NULL;
    if ((n = PycStringIO->cread(self->buffer, &buf, num_bytes)) != num_bytes)
    {
        PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }

    return PyUnicode_DecodeUTF8(buf, n, "");
}

static PyObject *
BufferedByteStream_write_utf8_string(BufferedByteStream *self, PyObject *s)
{
    PyObject *encoded_string = NULL;
    char *buf = NULL;
    Py_ssize_t len = -1;

    if(!self->buffer) {
        PyErr_SetString(PyExc_ValueError, "buffer is closed");
        return NULL;
    }
    
    if (PyUnicode_Check(s))
    {
        encoded_string = PyUnicode_AsUTF8String(s);
    }
    else if (PyString_Check(s))
    {
        encoded_string = PyString_AsEncodedObject(s, "utf8", "strict");
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "value must be Unicode or str");
        return NULL;
    }
    if (!encoded_string)
    {
        return NULL;
    }

    if (PyString_AsStringAndSize(encoded_string, &buf, &len)==-1)
    {
        Py_XDECREF(encoded_string);
        return NULL;
    }
    Py_XDECREF(encoded_string);
    
    PycStringIO->cwrite(self->buffer, buf, len);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef BufferedByteStream_methods[] = {
    {"tell", (PyCFunction)BufferedByteStream_tell, METH_NOARGS, ""},
    {"at_eof", (PyCFunction)BufferedByteStream_at_eof, METH_NOARGS, ""},
    {"remaining", (PyCFunction)BufferedByteStream_remaining, METH_NOARGS, "Returns number of remaining bytes."},
    {"seek", (PyCFunction)BufferedByteStream_seek, METH_KEYWORDS, ""},
    {"peek", (PyCFunction)BufferedByteStream_peek, METH_KEYWORDS, ""},
    {"read", (PyCFunction)BufferedByteStream_read, METH_KEYWORDS, ""},
    {"readline", (PyCFunction)BufferedByteStream_readline, METH_NOARGS, ""},
    {"readlines", (PyCFunction)BufferedByteStream_readlines, METH_KEYWORDS, ""},
    {"write", (PyCFunction)BufferedByteStream_write, METH_O, ""},
    {"writelines", (PyCFunction)BufferedByteStream_writelines, METH_O, ""},
    {"getvalue", (PyCFunction)BufferedByteStream_getvalue, METH_NOARGS, ""},
    {"truncate", (PyCFunction)BufferedByteStream_truncate, METH_KEYWORDS, ""},
    {"flush", (PyCFunction)BufferedByteStream_flush, METH_NOARGS, ""},
    {"close", (PyCFunction)BufferedByteStream_close, METH_NOARGS, "Closes the stream, freeing memory."},
    {"read_uchar", (PyCFunction)BufferedByteStream_read_uchar, METH_NOARGS, "Reads an C{unsigned char} from the stream."},
    {"write_uchar", (PyCFunction)BufferedByteStream_write_uchar, METH_O, "Writes an C{unsigned char} to the stream."},
    {"read_char", (PyCFunction)BufferedByteStream_read_char, METH_NOARGS, "Reads a C{char} from the stream."},
    {"write_char", (PyCFunction)BufferedByteStream_write_char, METH_O, "Writes a C{char} to the stream."},
    {"read_ushort", (PyCFunction)BufferedByteStream_read_ushort, METH_NOARGS, "Reads a 2 byte unsigned integer from the stream."},
    {"write_ushort", (PyCFunction)BufferedByteStream_write_ushort, METH_O, "Writes a 2 byte unsigned integer to the stream."},
    {"read_short", (PyCFunction)BufferedByteStream_read_short, METH_NOARGS, "Reads a 2 byte integer from the stream."},
    {"write_short", (PyCFunction)BufferedByteStream_write_short, METH_O, "Writes a 2 byte integer to the stream."},
    {"read_ulong", (PyCFunction)BufferedByteStream_read_ulong, METH_NOARGS, "Reads a 4 byte unsigned integer from the stream."},
    {"write_ulong", (PyCFunction)BufferedByteStream_write_ulong, METH_O, "Writes a 4 byte unsigned integer to the stream."},
    {"read_long", (PyCFunction)BufferedByteStream_read_long, METH_NOARGS, "Reads a 4 byte integer from the stream."},
    {"write_long", (PyCFunction)BufferedByteStream_write_long, METH_O, "Writes a 4 byte integer to the stream."},
    {"read_float", (PyCFunction)BufferedByteStream_read_float, METH_NOARGS, "Reads an 4 byte float from the stream."},
    {"write_float", (PyCFunction)BufferedByteStream_write_float, METH_O, "Writes an 4 byte float to the stream."},
    {"read_double", (PyCFunction)BufferedByteStream_read_double, METH_NOARGS, "Reads an 8 byte float from the stream."},
    {"write_double", (PyCFunction)BufferedByteStream_write_double, METH_O, "Writes an 8 byte float to the stream."},
    {"read_utf8_string", (PyCFunction)BufferedByteStream_read_utf8_string, METH_O, "Reads a UTF-8 string from the stream."},
    {"write_utf8_string", (PyCFunction)BufferedByteStream_write_utf8_string, METH_O, "Writes a unicode object to the stream in UTF-8"},
    {NULL}
};

static long
BufferedByteStream___len__(BufferedByteStream *self)
{
    PyObject *cur_pos, *tmp, *end_pos;
    long result;

    if(!self->buffer)
    {
        return 0;
    }
    
    cur_pos = BufferedByteStream_tell(self);
    
    tmp = PyObject_CallMethod(self->buffer, "seek", "ii", 0, 2);
    Py_XDECREF(tmp);
    
    end_pos = BufferedByteStream_tell(self);
    
    tmp = PyObject_CallMethod(self->buffer, "seek", "Oi", cur_pos, 0);
    Py_XDECREF(tmp);
    Py_XDECREF(cur_pos);

    result = PyInt_AsLong(end_pos);
    Py_XDECREF(end_pos);

    return result;
}
static PySequenceMethods BufferedByteStream_sequencemethods = {
    (Py_ssize_t(*)(PyObject*))BufferedByteStream___len__, /*sq_length*/
    0, /*sq_concat*/
    0, /*sq_repeat*/
    0, /*sq_item*/
    0, /*sq_slice*/
    0, /*sq_ass_item*/
    0, /*sq_ass_slice*/
    0, /*sq_contains*/
    0, /*sq_inplace_concat*/
    0, /*sq_inplace_repeat*/
};

static PyObject *
BufferedByteStream___add__(BufferedByteStream *self,
                           PyObject *other)
{
    BufferedByteStream *o, *new;
    PyObject *tmp;

    if (!BufferedByteStream_Check(other))
    {
        PyErr_SetString(PyExc_ValueError, "can only add BufferedByteStream");
        return NULL;
    }
    o = (BufferedByteStream *) other;
    
    new = PyObject_New(BufferedByteStream, &BufferedByteStreamType);
    new->buffer = PycStringIO->NewOutput(128);
    new->endian = self->endian;
    
    BufferedByteStream_init_(new, (PyObject *)self, 0);
    BufferedByteStream_init_(new, (PyObject *)o, 1);

    tmp = PyObject_CallMethod((PyObject *)new, "seek", "i", 0);
    Py_XDECREF(tmp);
    
    return (PyObject *)new; 
}

static PyNumberMethods BufferedByteStream_numbermethods = {
    (binaryfunc)BufferedByteStream___add__, /*nb_add*/
};

static PyMemberDef BufferedByteStream_members[] = {
    {"endian", T_CHAR, offsetof(BufferedByteStream, endian), 0, "endian"},
    {NULL}
};

static PyObject *
BufferedByteStream_new(PyTypeObject* type,
                       PyObject *args,
                       PyObject *kwargs)
{
    BufferedByteStream *self = NULL;
    self = (BufferedByteStream *)type->tp_alloc(type, 0);
    if (self)
    {
        self->buffer = NULL;
        self->endian = ENDIAN_NETWORK;
    }
    return (PyObject *)self;
}

/**
 * Initialize a BufferedByteStream, with the data contained in buf_obj.
 * If rewind==1, it also "rewinds" the file pointer to the start of the buffer.
 **/
static int 
BufferedByteStream_init_(BufferedByteStream *self, PyObject *buf_obj, int rewind)
{
    if (self->buffer == NULL)
    {
        self->buffer = PycStringIO->NewOutput(128);
    }
    if (buf_obj && buf_obj != Py_None)
    {
        if (BufferedByteStream_Check(buf_obj))
        {
            BufferedByteStream *other;
            PyObject *old_pos, *tmp;
            char *str;
            int len;

            /* Copy data from another BufferedByteStream */
            other = (BufferedByteStream *)buf_obj;

            /* Save the position of other, so we can restore it later */
            old_pos = BufferedByteStream_tell(other);

            /* Rewind the other stream */
            tmp = PyObject_CallMethod((PyObject *)other, "seek", "i", 0);
            Py_XDECREF(tmp);
            tmp = NULL;

            /* Copy data */
            str = NULL;
            len = 0;
            len = PycStringIO->cread(other->buffer, &str, -1);
            PycStringIO->cwrite(self->buffer, str, len);

            /* Restore other's current position */
            tmp = PyObject_CallMethod((PyObject *)other, "seek", "O", old_pos);
            Py_XDECREF(tmp);
            Py_XDECREF(old_pos);
            tmp = NULL;
        }
        else if (PyString_Check(buf_obj) || PyUnicode_Check(buf_obj))
        {
            /* Copy data from a Python string */
            char *str = NULL;
            Py_ssize_t len = 0;
            if (!PyString_AsStringAndSize(buf_obj, &str, &len))
            {
                PycStringIO->cwrite(self->buffer, str, len);
            }
        }
        else if (PyObject_HasAttrString(buf_obj, "getvalue"))
        {
            /* Copy data from a Python object with callable attribute getvalue. */
            PyObject *val = PyObject_CallMethod(buf_obj, "getvalue", NULL);
            char *str = NULL;
            Py_ssize_t len = 0;

            val = PyObject_CallMethod(buf_obj, "getvalue", NULL);
            if (!PyString_AsStringAndSize(val, &str, &len))
                PycStringIO->cwrite(self->buffer, str, len);
            Py_XDECREF(val);
        }
        else if (PyObject_HasAttrString(buf_obj, "read") &&
                 PyObject_HasAttrString(buf_obj, "seek") &&
                 PyObject_HasAttrString(buf_obj, "tell"))
        {
            /* Copy data from a file-like Python object */
            PyObject *old_pos, *val, *tmp;
            char *str;

            old_pos = PyObject_CallMethod(buf_obj, "tell", NULL);
            PyObject_CallMethod(buf_obj, "seek", "i", (int)0);

            val = PyObject_CallMethod(buf_obj, "read", NULL);
            str = NULL;
            Py_ssize_t len = 0;
            if (!PyString_AsStringAndSize(val, &str, &len))
                PycStringIO->cwrite(self->buffer, str, len);
            Py_XDECREF(val);

            tmp = PyObject_CallMethod(buf_obj, "seek", "O", old_pos);
            Py_XDECREF(tmp);
            Py_XDECREF(old_pos);
        }
        else
        {
            PyErr_SetString(PyExc_TypeError, "Unable to coerce buf->StringIO");
            return -1;
        }
    }
    /* Rewind self's pointer to the start of the stream, if asked nicely. */
    if (rewind==1)
    {
        PyObject *tmp = PyObject_CallMethod(self->buffer, "seek", "ii", 0, 0);
        Py_XDECREF(tmp);
    }
    return 0;
}

/**
 * Python Wrapper for BufferedByteStream_init_
 **/
static int
BufferedByteStream_init(BufferedByteStream *self,
                        PyObject *args,
                        PyObject *kwds)
{
    PyObject *buf_obj = NULL;
    static char *kwlist[] = {"buf", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", kwlist, &buf_obj))
        return -1;

    return BufferedByteStream_init_(self, buf_obj, 1);
}

static PyTypeObject BufferedByteStreamType = {
  PyObject_HEAD_INIT(NULL)
  0,                                                    /*ob_size*/
  "util.BufferedByteStream",                            /*tp_name*/
  sizeof(BufferedByteStream),                           /*tp_basicsize*/
  0,                                                    /*tp_itemsize*/
  (destructor)BufferedByteStream_dealloc,               /*tp_dealloc*/
  0,                                                    /*tp_print*/
  0,                                                    /*tp_getattr */
  0,                                                    /*tp_setattr */
  0,                                                    /*tp_compare*/
  0,                                                    /*tp_repr*/
  &BufferedByteStream_numbermethods,                    /*tp_as_number*/
  &BufferedByteStream_sequencemethods,                  /*tp_as_sequence*/
  0,                                                    /*tp_as_mapping*/
  0,                                                    /*tp_hash*/
  0,                                                    /*tp_call*/
  0,                                                    /*tp_str*/
  0,                                                    /*tp_getattro */
  0,                                                    /*tp_setattro */
  0,                                                    /*tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,             /*tp_flags*/
  "cpyamf equivalent of pyamf.util.BufferedByteStream", /*tp_doc */
  0,                                                    /*tp_traverse */
  0,                                                    /*tp_clear */
  0,                                                    /*tp_richcompare */
  0,                                                    /*tp_weaklistoffset */
  0,                                                    /*tp_iter */
  0,                                                    /*tp_iternext */
  BufferedByteStream_methods,                           /*tp_methods */
  BufferedByteStream_members,                           /*tp_members */
  0,                                                    /*tp_getset */
  0,                                                    /*tp_base*/
  0,                                                    /*tp_dict*/
  0,                                                    /*tp_descr_get*/
  0,                                                    /*tp_descr_set*/
  0,                                                    /*tp_dictoffset*/
  (initproc)BufferedByteStream_init,                    /*tp_init*/
  0,                                                    /*tp_alloc*/
  BufferedByteStream_new,                               /*tp_new*/
};

/**
 * CAPI struct, with publicly accessible BufferedByteStream API
 **/
static struct cPyAmf_BufferedByteStream_CAPI BufferedByteStream_CAPI = {
    (int (*)(PyObject*, PyObject*, int))&BufferedByteStream_init_,
    &BufferedByteStreamType,
};

PyMethodDef module_methods[] = {
  {NULL, NULL},
};

PyMODINIT_FUNC
initutil(void)
{
    PycString_IMPORT;

    PyObject *m;
    m = Py_InitModule3("cpyamf.util", module_methods, 
                       "C Extension-based substitutes for module pyamf.util");

    if (!m)
        return;

    if (PyType_Ready(&BufferedByteStreamType))
    {
        PyErr_Print();
        return;
    }

    PyModule_AddObject(m, 
                       "BufferedByteStream_CAPI", 
                       PyCObject_FromVoidPtr(&BufferedByteStream_CAPI, NULL));
    cPyAmf_BufferedByteStream = &BufferedByteStream_CAPI; 

    Py_INCREF(&BufferedByteStreamType);
    PyModule_AddObject(m, 
                       "BufferedByteStream",
                       (PyObject *)&BufferedByteStreamType);
}
