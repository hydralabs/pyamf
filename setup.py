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

from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup, find_packages

setup(name = "PyAMF",
    version = "0.0.2",
    description = "AMF encoder and decoder for Python",
    url = "http://pyamf.org",
    packages = find_packages(exclude=["*.tests"]),
    install_requires = ["elementtree>=1.2.6"], 
    test_suite = "pyamf.tests.suite",
    license = "MIT License",
    entry_points={
        'console_scripts': [
            'amfinfo = pyamf.info:main',
        ],
    },
    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ])
