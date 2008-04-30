# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
AMF Remoting support.

A Remoting request from the client consists of a short preamble, headers, and
bodies. The preamble contains basic information about the nature of the
request. Headers can be used to request debugging information, send
authentication info, tag transactions, etc. Bodies contain actual Remoting
requests and responses. A single Remoting envelope can contain several
requests; Remoting supports batching out of the box.

Client headers and bodies need not be responded to in a one-to-one manner. That
is, a body or header may not require a response. Debug information is requested
by a header but sent back as a body object. The response index is essential for
the Flash Player to understand the response therefore.

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
from pyamf import util

__all__ = ['Envelope', 'Request', 'Response', 'decode', 'encode']

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

#: AMF mimetype.
CONTENT_TYPE = 'application/x-amf'

ERROR_CALL_FAILED, = range(1)
ERROR_CODES = {
    ERROR_CALL_FAILED: 'Server.Call.Failed'
}

APPEND_TO_GATEWAY_URL = 'AppendToGatewayUrl'
REPLACE_GATEWAY_URL = 'ReplaceGatewayUrl'
REQUEST_PERSISTENT_HEADER = 'RequestPersistentHeader'

class RemotingError(pyamf.BaseError):
    """
    Generic remoting error class.
    """

class RemotingCallFailed(RemotingError):
    """
    Raised if Server.Call.Failed received
    """

pyamf.add_error_class(RemotingCallFailed, ERROR_CODES[ERROR_CALL_FAILED])

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
        @raise KeyError: Unknown header found.
        """
        if not idx in self:
            raise KeyError("Unknown header %s" % str(idx))

        return idx in self.required

    def set_required(self, idx, value=True):
        """
        @raise KeyError: Unknown header found.
        """
        if not idx in self:
            raise KeyError("Unknown header %s" % str(idx))

        if not idx in self.required:
            self.required.append(idx)

    def __len__(self):
        return len(self.keys())

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
        if not isinstance(value, Message):
            raise TypeError, "Message instance expected"

        value.envelope = self
        dict.__setitem__(self, idx, value)

    def __iter__(self):
        order = self.keys()
        order.sort()

        for x in order:
            yield x, self[x]

        raise StopIteration

class Message(object):
    """
    I represent a singular request/response, containing a collection of
    headers and one body of data.

    I am used to iterate over all requests in the L{Envelope}.

    @ivar envelope: The parent envelope of this AMF Message.
    @type envelope: L{Envelope}
    @ivar body: The body of the message.
    @type body: C{mixed}
    @ivar headers: The message headers.
    @type headers: C{dict}
    """
    def __init__(self, envelope, body):
        self.envelope = envelope
        self.body = body

    def _get_headers(self):
        return self.envelope.headers

    headers = property(_get_headers)

class Request(Message):
    """
    An AMF Request payload.

    @ivar target: The target of the request
    @type target: C{basestring}
    """
    def __init__(self, target, body=[], envelope=None):
        Message.__init__(self, envelope, body)

        self.target = target

    def __repr__(self):
        return "<%s target=%s>%s</%s>" % (
            type(self).__name__, self.target, self.body, type(self).__name__)

class Response(Message):
    """
    An AMF Response.

    @ivar status: The status of the message.
    @type status: Member of L{STATUS_CODES}
    """
    def __init__(self, body, status=STATUS_OK, envelope=None):
        Message.__init__(self, envelope, body)

        self.status = status

    def __repr__(self):
        return "<%s status=%s>%s</%s>" % (
            type(self).__name__, _get_status(self.status), self.body,
            type(self).__name__)

class BaseFault(object):
    """
    I represent a Fault message (C{mx.rpc.Fault}).

    @ivar level: The level of the fault.
    @type level: C{str}
    @ivar code: A simple code describing the fault.
    @type code: C{str}
    @ivar details: Any extra details of the fault.
    @type details: C{str}
    @ivar description: Text description of the fault.
    @type description: C{str}

    @see: U{mx.rpc.Fault on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/rpc/Fault.html>}
    """
    level = None

    def __init__(self, *args, **kwargs):
        self.code = kwargs.get('code', '')
        self.type = kwargs.get('type', '')
        self.details = kwargs.get('details', '')
        self.description = kwargs.get('description', '')

    def __repr__(self):
        x = '<%s level=%s' % (self.__class__.__name__, self.level)

        if self.code not in ('', None):
            x += ' code=%s' % self.code
        if self.type not in ('', None):
            x += ' type=%s' % self.type
        if self.description not in ('', None):
            x += ' description=%s' % self.description

        return x + '>'

    def raiseException(self):
        """
        Raises an exception based on the fault object. There is no traceback
        available.
        """
        raise get_exception_from_fault(self), self.description, None

pyamf.register_class(BaseFault,
    attrs=['level', 'code', 'type', 'details', 'description'])

class ErrorFault(BaseFault):
    """
    I represent an error level fault.
    """

    level = 'error'

pyamf.register_class(ErrorFault)

def _read_header(stream, decoder, strict=False):
    """
    Read AMF L{Message} header.

    @type   stream: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    @param  stream: AMF data.
    @type   decoder: L{amf0.Decoder<pyamf.amf0.Decoder>}
    @param  decoder: AMF decoder instance
    @type strict: C{bool}
    @param strict:
    @raise DecodeError: The data that was read from the stream
    does not match the header length.

    @rtype: C{tuple}
    @return:
     - Name of the header.
     - A C{bool} determining if understanding this header is
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

    @type   name: C{str}
    @param  name: Name of the header.
    @type   header:
    @param  header: Raw header data.
    @type   required: L{bool}
    @param  required: Required header.
    @type   stream: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    @param  stream: AMF data.
    @type   encoder: L{amf0.Encoder<pyamf.amf0.Encoder>}
    or L{amf3.Encoder<pyamf.amf3.Encoder>}
    @param  encoder: AMF encoder instance.
    @type strict: C{bool}
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

    @type   stream: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    @param  stream: AMF data.
    @type   decoder: L{amf0.Decoder<pyamf.amf0.Decoder>}
    @param  decoder: AMF decoder instance.
    @type strict: C{bool}
    @param strict:
    @raise DecodeError: Data read from stream does not match body length.

    @rtype: C{tuple}
    @return: A C{tuple} containing:
        - ID of the request
        - L{Request} or L{Response}
    """
    def _read_args():
        if stream.read(1) != '\x0a':
            raise pyamf.DecodeError, "Array type required for request body"

        x = stream.read_ulong()

        return [decoder.readElement() for i in xrange(x)]

    target = stream.read_utf8_string(stream.read_ushort())
    response = stream.read_utf8_string(stream.read_ushort())

    status = STATUS_OK
    is_request = True

    for (code, s) in STATUS_CODES.iteritems():
        if target.endswith(s):
            is_request = False
            status = code
            target = target[:0 - len(s)]

    data_len = stream.read_ulong()
    pos = stream.tell()

    if is_request:
        data = _read_args()
    else:
        data = decoder.readElement()

    if strict and pos + data_len != stream.tell():
        raise pyamf.DecodeError("Data read from stream does not match body "
            "length (%d != %d)" % (pos + data_len, stream.tell(),))

    if is_request:
        return (response, Request(target, body=data))
    else:
        if status == STATUS_ERROR and isinstance(data, pyamf.ASObject):
            data = get_fault(data)

        return (target, Response(data, status))

def _write_body(name, message, stream, encoder, strict=False):
    """
    Write AMF message body.

    @param name: The name of the request.
    @type name: C{basestring}
    @param message: The AMF payload.
    @type message: L{Request} or L{Response}
    @type stream: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    @type encoder: L{amf0.Encoder<pyamf.amf0.Encoder>}
    @param encoder: Encoder to use.
    @type strict: C{bool}
    @param strict: Use strict encoding policy.
    """
    if not isinstance(message, (Request, Response)):
        raise TypeError, "Unknown message type"

    target = None

    if isinstance(message, Request):
        target = unicode(message.target)
    else:
        target = u"%s%s" % (name, _get_status(message.status))

    target = target.encode('utf8')

    stream.write_ushort(len(target))
    stream.write_utf8_string(target)

    response = 'null'

    if isinstance(message, Request):
        response = name

    stream.write_ushort(len(response))
    stream.write_utf8_string(response)

    if not strict:
        stream.write_ulong(0)
        encoder.writeElement(message.body)
    else:
        write_pos = stream.tell()
        stream.write_ulong(0)
        old_pos = stream.tell()

        encoder.writeElement(message.body)
        new_pos = stream.tell()

        stream.seek(write_pos)
        stream.write_ulong(new_pos - old_pos)
        stream.seek(new_pos)

def _get_status(status):
    """
    Get status code.

    @type status: C{str}
    @raise ValueError: The status code is unknown.
    @return: Status code.
    """
    if status not in STATUS_CODES.keys():
        # TODO print that status code..
        raise ValueError, "Unknown status code"

    return STATUS_CODES[status]

def get_fault_class(level, **kwargs):
    code = kwargs.get('code', '')

    if level == 'error':
        return ErrorFault

    return BaseFault

def get_fault(data):
    try:
        level = data['level']
        del data['level']
    except KeyError:
        level = 'error'

    e = {}

    for x, y in data.iteritems():
        if isinstance(x, unicode):
            e[str(x)] = y
        else:
            e[x] = y

    return get_fault_class(level, **e)(**e)

def decode(stream, context=None, strict=False):
    """
    Decodes the incoming stream. .

    @type   stream: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    @param  stream: AMF data.
    @type   context: L{amf0.Context<pyamf.amf0.Context>} or
    L{amf3.Context<pyamf.amf3.Context>}
    @param  context: Context.
    @type strict: C{bool}
    @param strict: Enforce strict encoding.

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

    # see http://osflash.org/documentation/amf/envelopes/remoting#preamble
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
    context.clear()

    for i in range(body_count):
        target, payload = _read_body(stream, decoder, strict)
        msg[target] = payload

    if strict and stream.remaining() > 0:
        raise RuntimeError, "Unable to fully consume the buffer"

    return msg

def encode(msg, old_context=None, strict=False):
    """
    Encodes AMF stream and returns file object.

    @type   msg: L{Envelope}
    @param  msg: The message to encode.
    @type   old_context: L{amf0.Context<pyamf.amf0.Context>} or
    L{amf3.Context<pyamf.amf3.Context>}
    @param  old_context: Context.
    @type strict: C{bool}
    @param strict: Determines whether encoding should be strict. Specifically
        header/body lengths will be written correctly, instead of the default 0.

    @rtype: C{StringIO}
    @return: File object.
    """
    def getNewContext():
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

    for name, message in msg.iteritems():
        # Each body requires a new context
        encoder.context = getNewContext()
        _write_body(name, message, stream, encoder, strict)

    return stream

def get_exception_from_fault(fault):
    # XXX nick: threading problems here?
    try:
        return pyamf.ERROR_CLASS_MAP[fault.code]
    except KeyError:
        # default to RemotingError
        return RemotingError
