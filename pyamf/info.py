#!/usr/bin/python
# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Arnar Birgisson
# Thijs Triemstra
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
Extracts and displays information for files that contain AMF data.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import glob
from optparse import OptionParser

import pyamf
from pyamf import remoting

def parse_options():
    """
    Parse command-line arguments.
    """
    parser = OptionParser()

    parser.add_option("-d", "--debug", action="store_true", dest="debug",
        default=False, help="Turns debugging on")
    parser.add_option("--dump", action="store_true", dest="dump",
        default=False, help="Shows a hexdump of the file")

    return parser.parse_args()

def read_file(fname):
    """
    Read file containing AMF data.
    """
    f = file(fname, "r")
    data = f.read()
    f.close()

    return data

def main():
    """
    Run AMF decoder on input file.
    """
    (options, args) = parse_options()

    for arg in args:
        for fname in glob.glob(arg):
            
            body = read_file(fname)

            try:
                print "Decoding file:", fname.rsplit("\\",1)[-1], "\n"           
                request = remoting.decode(body)
                response = remoting.Envelope(request.amfVersion, request.clientType)

            except:
                raise
            
            else:                    
                if options.debug:
                    for name, message in request:
                        print "  ", message
                        print "-" * 80
                        
                if options.dump:
                    print pyamf.util.hexdump(body)
                    
if __name__ == '__main__':
    main()
