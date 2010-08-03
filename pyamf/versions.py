# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Because there is disparity between Python packaging (and it is being sorted
out ...) we currently provide our own way to get the string of a version tuple.

@since: 0.6
"""


class Version(tuple):

    _version = None

    def __new__(cls, *args):
        x = tuple.__new__(cls, args)

        return x

    def __str__(self):
        if not self._version:
            self._version = get_version(self)

        return self._version


def get_version(v):
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
