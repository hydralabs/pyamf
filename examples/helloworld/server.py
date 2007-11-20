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
Echo test server.

You can use this example with the echo_test.swf client on the
U{EchoTest<http://pyamf.org/wiki/EchoTest>} wiki page.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

def echo(data):
    """
    Return data back to the client.

    @type data: mixed
    @param data: Decoded AS->Python data
    """
    # Simply return the data back to the client
    return data

if __name__ == '__main__':
    import sys
    from __init__ import parse_args, run_server

    options = parse_args(sys.argv[1:])
    services = {'echo.echo': echo}

    run_server('Hello World', options[0], services)
