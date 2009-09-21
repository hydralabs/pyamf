import os

from docutils import core

from genshi.input import HTML


def rst2html( input, output ):
    """
    Write rst to html.
    """
    file = open(os.path.abspath(input), 'r')
    html = HTML(core.publish_file(file, writer_name='html'))
    body = html.select('body/div').render()

    tmp = open(output, 'w')
    tmp.write(body)
    tmp.close()
    
    return body

def copyrst( input, output ):
    """
    Write file to rst.
    """
    file = open(os.path.abspath(input), 'r')
    tmp = open(output, 'w')
    tmp.write(file.read())
    tmp.close()