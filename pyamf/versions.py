# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Because there is disparity between Python packaging (and it is being sorted
out ...) we currently provide our own way to get the string of a version tuple.

@since: 0.6
"""


class Version(tuple):
    """
    Provides programmatic version information as well as a way to get a pretty
    printed version number.

    Usage example:
    >>> version = Version(0, 0, 1)
    >>> version[0] == 0
    True
    >>> str(version)
    '0.0.1'
    """

    _version = None

    def __new__(cls, *args):
        return tuple.__new__(cls, args)

    def __str__(self):
        if not self._version:
            self._version = get_version(self)

        return self._version


def get_version(v):
    """
    Returns a prettified version of a tuple that is PEP-345 compliant.

    A major and a minor version must be provided at a minimum.
    """
    version = '%s.%s' % (v[0], v[1])

    try:
        if v[2]:
            version = '%s.%s' % (version, v[2])
        if v[3:] == ('alpha', 0):
            version = '%s pre-alpha' % version
        else:
            version = '%s%s' % (version, v[3])
            if v[3] != 'final':
                version = '%s%s' % (version, v[4])
    except IndexError:
        pass

    return version
