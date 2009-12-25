==========================
 PyAMF Installation Guide
==========================

.. contents::

PyAMF requires Python_ 2.3 or newer. Python 3.0 isn't supported yet_.


Easy Installation
=================

If you have setuptools_ or the `easy_install`_ tool already installed,
simply type the following on the command-line to install PyAMF::

    easy_install pyamf

`Note: you might need root permissions or equivalent for these steps.`

If you don't have `setuptools` or `easy_install`, first download
ez_setup.py_ and run::

    python ez_setup.py

After `easy_install` is installed, run `easy_install pyamf` again. If
you run into problems, try the manual installation instructions below.

To upgrade your existing PyAMF installation to the latest version
use::

    easy_install -U pyamf


Manual Installation
===================

To use PyAMF with Python 2.3 or 2.4, the following software packages
must be installed. The ``easy_install`` command will automatically
install them for you, as described above, but you can also choose to
download and install the packages manually.

You **don't** need these packages if you're using Python 2.5 or newer.

- ElementTree_ 1.2.6 or newer
- uuid_ 1.30 or newer

Step 1
------

Download_ and unpack the PyAMF archive of your choice::

    tar zxfv PyAMF-<version>.tar.gz
    cd PyAMF-<version>


Step 2
------

Run the Python-typical setup at the top of the source directory
from a command-prompt::

    python setup.py install

This will byte-compile the Python source code and install it in the
``site-packages`` directory of your Python installation.

To disable the installation of the C-extension, supply the
``--disable-ext`` option::

    python setup.py install --disable-ext

You can run the unit tests like this::

    python setup.py test


Optional Extras
===============

PyAMF integrates with the following optional third-party Python
libraries:

- wsgiref_ 0.1.2 or newer (included in Python 2.5 and newer)
- SQLAlchemy_ 0.4 or newer
- Twisted_ 2.5 or newer
- Django_ 0.97 or newer
- `Google App Engine`_ 1.0 or newer


C-Extension
===========

To modify the cPyAMF extension you need:

- Cython_ 0.10 or newer

And run the command below on the ``.pyx`` files to create the
``.c`` file, which contains the C source for the ``cPyAMF``
extension module::

    cython amf3.pyx


Advanced Options
================

Because of setuptools_ you can do, with the release tag, as well
as with trunk::
    
    easy_install http://svn.pyamf.org/pyamf/tags/release-0.5.1

To find out about other advanced installation options, run::
    
    easy_install --help

Also see `Installing Python Modules`_ for detailed information.

To install PyAMF to a custom location::
   
    easy_install --prefix=/path/to/installdir


.. _Python: 	http://www.python.org
.. _yet:	http://pyamf.org/milestone/Python%203000
.. _setuptools:	http://peak.telecommunity.com/DevCenter/setuptools
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall#installing-easy-install
.. _ez_setup.py: http://svn.pyamf.org/pyamf/trunk/ez_setup.py
.. _Download:	http://pyamf.org/wiki/Download
.. _ElementTree: http://effbot.org/zone/element-index.htm
.. _uuid:	http://pypi.python.org/pypi/uuid
.. _wsgiref:	http://pypi.python.org/pypi/wsgiref
.. _SQLAlchemy:	http://sqlalchemy.org
.. _Twisted:	http://twistedmatrix.com
.. _Django:	http://djangoproject.com
.. _Google App Engine: http://code.google.com/appengine
.. _Cython:	http://cython.org
.. _Installing Python Modules: http://docs.python.org/inst/inst.html