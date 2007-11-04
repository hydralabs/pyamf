# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Nick Joyce
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
AMF Remoting support.

Reference: U{http://osflash.org/documentation/amf/envelopes/remoting}
"""

import pyamf
from pyamf import util

__all__ = ['Envelope', 'Request', 'decode', 'encode']

#: Succesful call.
STATUS_OK = 0
#: Reserved for runtime errors.
STATUS_ERROR = 1
#: Debug information.
#: 
#: Reference: U{http://osflash.org/documentation/amf/envelopes/remoting/debuginfo}
STATUS_DEBUG = 2

STATUS_CODES = {
    STATUS_OK:    '/onResult',
    STATUS_ERROR: '/onStatus',
    STATUS_DEBUG: '/onDebugEvents'
}

class HeaderCollection(dict):
    def __init__(self, raw_headers={}):
        self.required = []

        for (k, ig, v) in raw_headers:
            self[k] = v
            if ig:
                self.required.append(k)

    def is_required(self, idx):
        if not idx in self:
            raise KeyError("Unknown header %s" % str(idx))

        return idx in self.required

    def set_required(self, idx, value=True):
        if not idx in self:
            raise KeyError("Unknown header %s" % str(idx))

        if not idx in self.required:
            self.required.append(idx)

class Envelope(dict):
    """
    I wrap an entire request, encapsulating headers and bodies (there may more
    than one request in one transaction).
    """

    def __init__(self, amfVersion=None, clientType=None):
        self.amfVersion = amfVersion
        self.clientType = clientType

        self.headers = HeaderCollection()

    def __repr__(self):
        r = "<Envelope amfVersion=%s clientType=%s>\n" % (
            self.amfVersion, self.clientType)

        for h in self.headers:
            r += " " + repr(h) + "\n"

        for request in iter(self):
            r += " " + repr(request) + "\n"

        r += "</Envelope>"

        return r

    def __setitem__(self, idx, value):
        if isinstance(value, (tuple, set, list)):
            value = Message(self, value[0], value[1], value[2])
        elif not isinstance(value, Message):
            raise TypeError("value must be a tuple/set/list")

        dict.__setitem__(self, idx, value)

    def __iter__(self):
        return iter([v for (k, v) in self.iteritems()])

class Message(object):
    """
    I represent a singular message, containing a collection of headers and
    one body of data.

    I am used to iterate over all requests in the L{Envelope}
    """

    def __init__(self, envelope, target, status, body):
        self.envelope = envelope
        self.target = target
        self.status = status
        self.body = body

    def _get_headers(self):
        return self.envelope.headers

    headers = property(_get_headers)

    def __repr__(self):
        return "<%s target=%s status=%s>%s</Message>" % (
            type(self).__name__, self.target,
            _get_status(self.status), self.body)

def _read_header(stream, decoder):
    """
    Read AMF message header.
    
    I return a tuple of:
     - The name of the header
     - A boolean determining if understanding this header is required
     - value of the header
    """
    name_len = stream.read_ushort()
    name = stream.read_utf8_string(name_len)

    required = bool(stream.read_uchar())

    data_len = stream.read_ulong()
    pos = stream.tell()

    data = decoder.readElement()

    if pos + data_len != stream.tell():
        raise pyamf.ParseError(
            "Data read from stream does not match header length")

    return (name, required, data)

def _write_header(name, header, required, stream, encoder):
    """
    Write AMF message header.
    """
    stream.write_ushort(len(name))
    stream.write_utf8_string(name)

    stream.write_uchar(required)
    write_pos = stream.tell()

    stream.write_ulong(0)
    old_pos = stream.tell()
    encoder.writeElement(header)
    new_pos = stream.tell()

    stream.seek(write_pos)
    stream.write_ulong(new_pos - old_pos)
    stream.seek(new_pos)

def _read_body(stream, decoder):
    """
    Read AMF message body.

    I return a tuple containing:
     - The target of the body
     - The id (as sent by the client) of the body
     - The data of the body
    """
    target_len = stream.read_ushort()
    target = stream.read_utf8_string(target_len)

    response_len = stream.read_ushort()
    response = stream.read_utf8_string(response_len)
    
    status = STATUS_OK

    for (code, s) in STATUS_CODES.iteritems():
        if response.endswith(s):
            status = code
            response = response[:0 - len(s)]

    data_len = stream.read_ulong()
    pos = stream.tell()
    data = decoder.readElement()

    if pos + data_len != stream.tell():
        raise pyamf.ParseError(
            "Data read from stream does not match body length")

    return (target, response, status, data)

def _write_body(name, body, stream, encoder):
    """
    Write AMF message body.
    """
    response = "%s%s" % (name, _get_status(body.status))

    stream.write_ushort(len(response))
    stream.write_utf8_string(response)

    response = 'null'
    stream.write_ushort(len(response))
    stream.write_utf8_string(response)

    write_pos = stream.tell()
    stream.write_ulong(0)
    old_pos = stream.tell()
    encoder.writeElement(body.body)
    new_pos = stream.tell()

    stream.seek(write_pos)
    stream.write_ulong(new_pos - old_pos)
    stream.seek(new_pos)

def _get_status(status):
    if status not in STATUS_CODES.keys():
        raise ValueError("Unknown status code")

    return STATUS_CODES[status]

def decode(stream, context=None):
    """
    Decodes the incoming stream and returns a L{Envelope} object.
    """
    if not isinstance(stream, util.BufferedByteStream):
        stream = util.BufferedByteStream(stream)

    msg = Envelope()

    msg.amfVersion = stream.read_uchar()
    decoder = pyamf._get_decoder(msg.amfVersion)(stream, context=context)
    msg.clientType = stream.read_uchar()

    header_count = stream.read_ushort()

    for i in xrange(header_count):
        name, required, data = _read_header(stream, decoder)
        msg.headers[name] = data

        if required:
            msg.headers.set_required(name)

    body_count = stream.read_short()

    for i in range(body_count):
        target, response, status, data = _read_body(stream, decoder)
        msg[response] = (target, status, data)

    if stream.remaining() > 0:
        raise RuntimeError("Unable to fully consume the buffer")

    return msg

def encode(msg, context=None):
    """
    Encodes AMF stream and returns file object.
    """
    stream = util.BufferedByteStream()

    encoder = pyamf._get_encoder(msg.amfVersion)(stream, context=context)

    stream.write_uchar(msg.amfVersion)
    stream.write_uchar(msg.clientType)
    stream.write_short(len(msg.headers))

    for name, header in msg.headers.iteritems():
        _write_header(name, header, msg.headers.is_required(name), stream, encoder)

    stream.write_short(len(msg))

    for name, body in msg.iteritems():
        _write_body(name, body, stream, encoder)

    return stream
