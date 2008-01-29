# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Local Shared Object implementation.

Local Shared Object (LSO), sometimes known as flash cookies, is a cookie-like data
entity used by the Flash Player and Gnash. The players allow web content to read
and write LSO data to the computer's local drive on a per-domain basis.

@see: U{Local Shared Object on WikiPedia (external)
<http://en.wikipedia.org/wiki/Local_Shared_Object>}
@see: U{Local Shared Object envelope (external)
<http://osflash.org/documentation/amf/envelopes/sharedobject>}

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import pyamf
from pyamf import amf0, util

#: Magic Number - 2 bytes
HEADER_VERSION = '\x00\xbf'
#: Marker - 10 bytes
HEADER_SIGNATURE = 'TCSO\x00\x04\x00\x00\x00\x00'
#: Padding - 4 bytes
PADDING_BYTE = '\x00'

def decode(stream, strict=True):
    """
    Decodes a SOL stream. C{strict} mode ensures that the sol stream is as spec
    compatible as possible.

    @raise DecodeError: One of:
     - Unknown SOL version in header.
     - Inconsistent stream header length.
     - Invalid signature.
     - Invalid padding read.
     - Missing padding byte.

    @return: A C{tuple} containing the C{root_name} and a C{dict} of name, value pairs.
    @rtype: C{tuple}
    """
    if not isinstance(stream, util.BufferedByteStream):
        stream = util.BufferedByteStream(stream)

    decoder = amf0.Decoder(stream)

    # read the version
    version = stream.read(2)

    if version != HEADER_VERSION:
        raise pyamf.DecodeError, 'Unknown SOL version in header'

    # read the length
    length = stream.read_ulong()

    if strict and stream.remaining() != length:
        raise pyamf.DecodeError, 'Inconsistent stream header length'

    # read the signature
    signature = stream.read(10)

    if signature != HEADER_SIGNATURE:
        raise pyamf.DecodeError, 'Invalid signature'

    root_name = decoder.readString()

    # read padding
    if stream.read(4) != PADDING_BYTE * 4:
        raise pyamf.DecodeError, 'Invalid padding read'

    values = {}

    while 1:
        if stream.at_eof():
            break

        name = decoder.readString()
        value = decoder.readElement()

        # read the padding
        if stream.read(1) != PADDING_BYTE:
            raise pyamf.DecodeError, 'Missing padding byte'

        values[name] = value

    return (root_name, values)

def encode(name, values, strict=True):
    """
    Produces a SharedObject encoded stream based on the name and values.

    @param name: The root name of the SharedObject.
    @type name: C{basestring}
    @param values: A C{dict} of name value pairs to be encoded in the stream.
    @type values: C{dict}
    @return: A SharedObject encoded stream.
    @rtype: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    """
    stream = util.BufferedByteStream()
    encoder = amf0.Encoder(stream)

    # write the header
    stream.write(HEADER_VERSION)

    if strict is True:
        length_pos = stream.tell()

    stream.write_ulong(0)

    # write the signature
    stream.write(HEADER_SIGNATURE)

    # write the root name
    encoder.writeString(name, False)

    # write the padding
    stream.write(PADDING_BYTE * 4)

    for n, v in values.iteritems():
        encoder.writeString(n, False)
        encoder.writeElement(v)

        # write the padding
        stream.write(PADDING_BYTE)

    if strict:
        stream.seek(length_pos)
        stream.write_ulong(stream.remaining() - 4)

    stream.seek(0)

    return stream
