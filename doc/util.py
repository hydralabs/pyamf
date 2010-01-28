# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

import os

from docutils.core import publish_parts


def rst2html( input, output ):
    """
    Create html file from rst file.
    
    :param input: Path to rst source file
    :type: `str`
    :param output: Path to html output file
    :type: `str`
    """
    file = os.path.abspath(input)
    rst = open(file, 'r').read()
    html = publish_parts(rst, writer_name='html')
    body = html['html_body']

    tmp = open(output, 'w')
    tmp.write(body)
    tmp.close()
    
    return body


def copy_file( input, output ):
    """
    Copy file to folder.
    
    :param input: Path to source file
    :type: `str`
    :param output: Path to output file
    :type: `str`
    """
    path = os.path.abspath(input)
    file = open(path, 'r')
    tmp = open(output, 'w')
    tmp.write(file.read())
    tmp.close()
