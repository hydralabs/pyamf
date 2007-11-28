# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
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

A Remoting request from the client consists of a short preamble, headers, and bodies.
The preamble contains basic information about the nature of the request. Headers can
be used to request debugging information, send authentication info, tag transactions,
etc. Bodies contain actual Remoting requests and responses. A single Remoting envelope
can contain several requests; Remoting supports batching out of the box.

Client headers and bodies need not be responded to in a one-to-one manner. That is, a
body or header may not require a response. Debug information is requested by a header
but sent back as a body object. The response index is essential for the Flash Player
to understand the response therefore.

@see: U{Remoting Envelope on OSFlash (external)
<http://osflash.org/documentation/amf/envelopes/remoting>}
@see: U{Remoting Headers on OSFlash (external)
<http://osflash.org/amf/envelopes/remoting/headers>}
@see: U{Remoting Debug Headers on OSFlash (external)
<http://osflash.org/documentation/amf/envelopes/remoting/debuginfo>}

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}
@since: 0.1.0
"""

import pyamf
from pyamf import util, flex

__all__ = ['Envelope', 'Request', 'decode', 'encode']

#: Succesful call.
STATUS_OK = 0
#: Reserved for runtime errors.
STATUS_ERROR = 1
#: Debug information.
STATUS_DEBUG = 2

#: List of available status response codes.
STATUS_CODES = {
    STATUS_OK:    '/onResult',
    STATUS_ERROR: '/onStatus',
    STATUS_DEBUG: '/onDebugEvents'
}

class RemotingError(pyamf.BaseError):
    """
    Generic remoting error class.
    """

class HeaderCollection(dict):
    """
    Collection of AMF message headers.
    """
    def __init__(self, raw_headers={}):
        self.required = []

        for (k, ig, v) in raw_headers:
            self[k] = v
            if ig:
                self.required.append(k)

    def is_required(self, idx):
        """
        @type idx:
        @param idx:
        @raise KeyError: Unknown header found.
        """
        if not idx in self:
            raise KeyError("Unknown header %s" % str(idx))

        return idx in self.required

    def set_required(self, idx, value=True):
        """
        @type idx:
        @param idx:
        @type value: bool
        @param value:

        @raise KeyError: Unknown header found.
        """
        if not idx in self:
            raise KeyError("Unknown header %s" % str(idx))

        if not idx in self.required:
            self.required.append(idx)

class Envelope(dict):
    """
    I wrap an entire request, encapsulating headers and bodies.

    There can be more than one request in a single transaction.
    """

    def __init__(self, amfVersion=None, clientType=None):
        #: AMF encoding version
        self.amfVersion = amfVersion
        #: Client type
        self.clientType = clientType
        #: Message headers
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
        """
        @type idx:
        @param idx:
        @type value:
        @param value:
        @raise TypeError: The parameter C{value} is not of the C{tuple},
        C{set} or C{list} type.
        """
        if isinstance(value, (tuple, set, list)):
            value = Message(self, value[0], value[1], value[2])
        elif not isinstance(value, Message):
            raise TypeError("value must be a tuple/set/list")

        value.envelope = self
        dict.__setitem__(self, idx, value)

    def __iter__(self):
        return self.iteritems()

class Message(object):
    """
    I represent a singular message, containing a collection of
    headers and one body of data.

    I am used to iterate over all requests in the L{Envelope}.
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

def _read_header(stream, decoder, strict=False):
    """
    Read AMF L{Message} header.

    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data.
    @type   decoder: L{amf0.Decoder<pyamf.amf0.Decoder>} or
    L{amf3.Decoder<pyamf.amf3.Decoder>}
    @param  decoder: AMF decoder instance
    @type strict: bool
    @param strict:
    @raise DecodeError: The data that was read from the stream
    does not match the header length.

    @rtype: tuple
    @return:
     - Name of the header.
     - A boolean determining if understanding this header is
     required.
     - Value of the header.
    """

    name_len = stream.read_ushort()
    name = stream.read_utf8_string(name_len)

    required = bool(stream.read_uchar())

    data_len = stream.read_ulong()
    pos = stream.tell()

    data = decoder.readElement()

    if strict and pos + data_len != stream.tell():
        raise pyamf.DecodeError(
            "Data read from stream does not match header length")

    return (name, required, data)

def _write_header(name, header, required, stream, encoder, strict=False):
    """
    Write AMF message header.

    @type   name: str
    @param  name: Name of header
    @type   header:
    @param  header: Raw header data.
    @type   required: L{bool}
    @param  required: Required header.
    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data.
    @type   encoder: L{amf0.Encoder<pyamf.amf0.Encoder>}
    or L{amf3.Encoder<pyamf.amf3.Encoder>}
    @param  encoder: AMF encoder instance.
    @type strict: bool
    @param strict:
    """
    stream.write_ushort(len(name))
    stream.write_utf8_string(name)

    stream.write_uchar(required)
    write_pos = stream.tell()

    stream.write_ulong(0)
    old_pos = stream.tell()
    encoder.writeElement(header)
    new_pos = stream.tell()

    if strict:
        stream.seek(write_pos)
        stream.write_ulong(new_pos - old_pos)
        stream.seek(new_pos)

def _read_body(stream, decoder, strict=False):
    """
    Read AMF message body.

    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data.
    @type   decoder: L{amf0.Decoder<pyamf.amf0.Decoder>} or
    L{amf3.Decoder<pyamf.amf3.Decoder>}
    @param  decoder: AMF decoder instance.
    @type strict: bool
    @param strict:
    @raise DecodeError: Data read from stream does not match body length.

    @rtype: tuple
    @return:
     - The target of the body.
     - The id (as sent by the client) of the body.
     - The data of the body.
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

    if strict and pos + data_len != stream.tell():
        raise pyamf.DecodeError("Data read from stream "
            "does not match body length (%d != %d)" %
                (pos + data_len, stream.tell(),))

    return (target, response, status, data)

def _write_body(name, message, stream, encoder, strict=False):
    """
    Write AMF message body.

    @type   name: str
    @param  name: Name of body.
    @type   message: L{Message}
    @param  message: Message to write.
    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data
    @type   encoder: L{amf0.Encoder<pyamf.amf0.Encoder>}
    or L{amf3.Encoder<pyamf.amf3.Encoder>}
    @param  encoder: Encoder to use.
    @type strict: bool
    @param strict:
    """
    target = u"%s%s" % (name, _get_status(message.status))

    stream.write_ushort(len(target))
    stream.write_utf8_string(target)

    response = u'null'
    stream.write_ushort(len(response))
    stream.write_utf8_string(response)

    write_pos = stream.tell()
    stream.write_ulong(0)
    old_pos = stream.tell()

    try:
        encoder.writeElement(message.body)
    except RuntimeError:
        # TODO
        print "doh"

    new_pos = stream.tell()

    if strict:
        stream.seek(write_pos)
        stream.write_ulong(new_pos - old_pos)
        stream.seek(new_pos)

def _get_status(status):
    """
    Get status code.

    @type status:
    @param status:
    @raise ValueError: The status code is unknown.

    @rtype:
    @return: Status codes.
    """
    if status not in STATUS_CODES.keys():
        raise ValueError, "Unknown status code"

    return STATUS_CODES[status]

def decode(stream, context=None, strict=False):
    """
    Decodes the incoming stream. .

    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data.
    @type   context: L{AMF0 Context<pyamf.amf0.Context>} or
    L{AMF3 Context<pyamf.amf3.Context>}
    @param  context: Context.
    @type strict: bool
    @param strict:

    @raise DecodeError: Malformed stream.
    @raise RuntimeError: Decoder is unable to fully consume the
    stream buffer.

    @return: Message envelope.
    @rtype: L{Envelope}
    """
    if not isinstance(stream, util.BufferedByteStream):
        stream = util.BufferedByteStream(stream)

    msg = Envelope()

    msg.amfVersion = stream.read_uchar()

    # See http://osflash.org/documentation/amf/envelopes/remoting#preamble
    # why we are doing this...
    if msg.amfVersion > 0x09:
        raise pyamf.DecodeError("Malformed stream (amfVersion=%d)" %
            msg.amfVersion)

    if context is None:
        context = pyamf.get_context(pyamf.AMF0)

    decoder = pyamf._get_decoder_class(pyamf.AMF0)(stream, context=context)
    msg.clientType = stream.read_uchar()

    header_count = stream.read_ushort()

    for i in xrange(header_count):
        name, required, data = _read_header(stream, decoder, strict)
        msg.headers[name] = data

        if required:
            msg.headers.set_required(name)

    body_count = stream.read_short()

    for i in range(body_count):
        target, response, status, data = _read_body(stream, decoder, strict)

        if response == 'null':
            # the body is a response
            x = target.rsplit('/', 1)
            response = x[0]

            for (code, s) in STATUS_CODES.iteritems():
                if s.endswith(x[1]):
                    status = code

                    break

        msg[response] = (target, status, data)

    if stream.remaining() > 0:
        raise RuntimeError("Unable to fully consume the buffer")

    return msg

def encode(msg, old_context=None, strict=False):
    """
    Encodes AMF stream and returns file object.

    @type   msg: L{Envelope}
    @param  msg: The message to encode.
    @type   old_context: L{AMF0 Context<pyamf.amf0.Context>} or
    L{AMF3 Context<pyamf.amf3.Context>}
    @param  old_context: Context.
    @type strict: bool
    @param strict: Determines whether encoding should be strict. Specifically
        header/body lengths will be written correctly, instead of the default 0.

    @rtype:
    @return: File object.
    """
    def getNewContext():
        """
        @rtype:
        @return:
        """
        if old_context:
            import copy

            return copy.copy(old_context)
        else:
            return pyamf.get_context(pyamf.AMF0)

    stream = util.BufferedByteStream()

    encoder = pyamf._get_encoder_class(msg.amfVersion)(stream)

    stream.write_uchar(msg.amfVersion)
    stream.write_uchar(msg.clientType)
    stream.write_short(len(msg.headers))

    for name, header in msg.headers.iteritems():
        _write_header(
            name, header, msg.headers.is_required(name),
            stream, encoder, strict)

    stream.write_short(len(msg))

    for name, body in msg.iteritems():
        # Each body requires a new context
        encoder.context = getNewContext()
        _write_body(name, body, stream, encoder, strict)

    return stream

class RecordSet(object):
    """
    I represent the RecordSet class used in Flash
    Remoting to hold (amongst other things) SQL records.

    @ivar columns: The columns to send
    @type columns: List of strings
    @ivar items: The recordset data
    @type items: List of lists, the order of the data corresponds
        to the order of the columns
    @ivar service: Service linked to the recordset
    @type: ?
    @ivar id: The id of the recordset
    @type id: str

    @see: U{RecordSet on OSFlash (external)
    <http://osflash.org/documentation/amf/recordset>}
    """

    def __init__(self, columns=[], items=[], service=None, id=None):
        """
        """
        self.columns = columns
        self.items = items
        self.service = service
        self.id = id

    def _get_server_info(self):
        """
        @rtype: dict
        @return: The object to be encoded.
        """
        ret = dict(totalCount=len(self.items), cursor=1, version=1,
            initialData=self.items, columnNames=self.columns)

        if self.service is not None:
            ret.update(serviceName=str(self.service.name))

        if self.id is not None:
            ret.update(id=str(self.id))

        return ret

    def _set_server_info(self, val):
        """
        @type val:
        @param val:
        """
        self.columns = val['columnNames']
        self.items = val['initialData']

        try:
            # TODO nick: find relevant service and link in here.
            self.service = pyamf.Bag({'name': val['serviceName']})
        except KeyError:
            self.service = None

        try:
            self.id = val['id']
        except KeyError:
            self.id = None

    serverInfo = property(_get_server_info, _set_server_info)

pyamf.register_class(RecordSet, 'RecordSet', attrs=['serverInfo'],
    metadata=['amf3'])
