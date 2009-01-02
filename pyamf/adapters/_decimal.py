# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
Adapter for the C{decimal} module.

@since: 0.4
"""

import decimal

import pyamf

def convert_Decimal(x, encoder):
    """
    Called when an instance of L{decimal.Decimal} is about to be encoded to
    an AMF stream.

    @param x: The L{decimal.Decimal} instance to encode.
    @param encoder: The L{pyamf.BaseEncoder} instance about to perform the
        operation.
    @return: If the encoder is in 'strict' mode then C{x} will be converted to
        a float. Otherwise an L{pyamf.EncodeError} with a friendly message is
        raised.
    """
    if encoder is not None and isinstance(encoder, pyamf.BaseEncoder):
        if encoder.strict is False:
            return float(x)

    raise pyamf.EncodeError('Unable to encode decimal.Decimal instances as '
        'there is no way to guarantee exact conversion. Use strict=False to '
        'convert to a float.')

if hasattr(decimal, 'Decimal'):
    pyamf.add_type(decimal.Decimal, convert_Decimal)
