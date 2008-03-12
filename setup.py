# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup, find_packages
from setuptools.command import test

class TestCommand(test.test):
    def run_twisted(self):
        from twisted.trial import runner
        from twisted.trial import reporter

        from pyamf.tests import suite

        r = runner.TrialRunner(reporter.VerboseTextReporter)
        r.run(suite())

    def run_tests(self):
        try:
            import twisted

            self.run_twisted()
        except ImportError:
            test.test.run_tests(self)

import sys

install_requires = ["fpconst>=0.7.2", "Importing>=1.9.2"]
if sys.version_info < (2, 5):
    install_requires.extend(["elementtree >= 1.2.6", "uuid>=1.30"])

long_desc = """\
PyAMF provides Action Message Format (AMF) support for Python that is
compatible with the Flash Player.

The Adobe Integrated Runtime and Flash Player use AMF to communicate
between an application and a remote server. AMF encodes remote procedure
calls (RPC) into a compact binary representation that can be transferred
over HTTP/HTTPS or the RTMP/RTMPS protocol. Objects and data values are
serialized into this binary format, which increases performance,
allowing applications to load data up to 10 times faster than with
text-based formats such as XML or SOAP.

AMF 3, the default serialization for ActionScript 3.0, provides various
advantages over AMF0, which is used for ActionScript 1.0 and 2.0. AMF 3
sends data over the network more efficiently than AMF 0. AMF 3 supports
sending int and uint objects as integers and supports data types that are
available only in ActionScript 3.0, such as ByteArray, ArrayCollection,
and IExternalizable."""

keyw = """\
amf amf0 amf3 flex flash remoting rpc http flashplayer air bytearray
objectproxy arraycollection recordset actionscript decoder encoder
gateway"""

setup(name = "PyAMF",
    version = "0.3",
    description = "AMF support for Python",
    long_description = long_desc,
    url = "http://pyamf.org",
    author = "The PyAMF Project",
    author_email = "dev@pyamf.org",
    keywords = keyw,
    packages = find_packages(exclude=["*.tests"]),
    install_requires = install_requires,
    test_suite = "pyamf.tests.suite",
    zip_safe=True,
    license = "MIT License",
    cmdclass = {'test': TestCommand},
    extras_require={
        'wsgi': ['wsgiref'],
        'twisted': ['Twisted>=2.5.0'],
        'django': ['Django>=0.96']
    },
    classifiers = [
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ])
