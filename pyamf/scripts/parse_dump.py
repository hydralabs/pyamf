# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

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
        default=False, help="Enable debugging")
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

def print_message(req):
    for name, message in req:
        print "  ", message
        print "-" * 80
        
def main():
    """
    Run AMF decoder on input file.
    """
    (options, args) = parse_options()

    for arg in args:
        for fname in glob.glob(arg):

            body = read_file(fname)

            try:
                print "Decoding file: %s\n" % fname
                request = remoting.decode(body)

                if options.debug:
                    print_message(request)
                
            except pyamf.UnknownClassAlias, c:
                if options.debug:
                    print '  WARN: %s\n' % c
                pass  
            
            except:
                raise

            if options.dump:
                print pyamf.util.hexdump(body)

if __name__ == '__main__':
    main()
