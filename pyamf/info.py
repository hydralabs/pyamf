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
#

import glob
from optparse import OptionParser

import pyamf

def parse_options():
    parser = OptionParser()

    parser.add_option("-d", "--debug", action="store_true", dest="debug",
        default=False, help="Turns debugging on")
    parser.add_option("--dump", action="store_true", dest="dump",
        default=False, help="Shows a hexdump of the file")

    return parser.parse_args()

def read_file(fname):
    f = file(fname, "r")
    data = f.read()
    f.close()

    return data

def main():
    (options, args) = parse_options()

    for arg in args:
        for fname in glob.glob(arg):
            
            data = read_file(fname)

            if options.debug:
                print "=" * 120

            print "Decoding file:", fname.rsplit("\\",1)[-1]

            try:
                p = pyamf.decode(data)
            except:
                raise
            else:
                if options.dump:
                    print pyamf.util.hexdump(data)
                    
                if options.debug:
                    print repr(p)
                    
if __name__ == '__main__':
    main()
