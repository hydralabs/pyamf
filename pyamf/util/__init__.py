# -*- coding: utf-8 -*-
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
AMF Utilities.

@since: 0.1.0
"""

import calendar
import datetime
import types
import inspect

import pyamf

try:
    from cpyamf.util import BufferedByteStream
except ImportError:
    from pyamf.util.pure import BufferedByteStream

# Required for backwards compatibility
from pyamf.python import (
    int_types, str_types,
    PosInf, NegInf, NaN,
    isNaN, isPosInf, isNegInf)

#: XML types.
xml_types = None
ET = None
#: On some Python versions retrieving a negative timestamp, like
#: C{datetime.datetime.utcfromtimestamp(-31536000.0)} is broken.
negative_timestamp_broken = False


def find_xml_lib():
    """
    Run through a predefined order looking through the various C{ElementTree}
    implementations so that any type can be encoded but PyAMF will return
    elements as the first implementation found.

    We work through the C implementations first - then the pure Python
    versions. The downside to this is that a possible of three libraries will
    be loaded into memory that are not used but the libs are small
    (relatively) and the flexibility that this gives seems to outweigh the
    cost. Time will tell.

    @since: 0.4
    """
    global xml_types, ET

    xml_types = []

    try:
        import xml.etree.cElementTree as cET

        ET = cET
        xml_types.append(type(cET.Element('foo')))
    except ImportError:
        pass

    try:
        import cElementTree as cET

        if ET is None:
            ET = cET

        xml_types.append(type(cET.Element('foo')))
    except ImportError:
        pass

    try:
        import xml.etree.ElementTree as pET

        if ET is None:
            ET = pET

        xml_types.append(pET._ElementInterface)
    except ImportError:
        pass

    try:
        import elementtree.ElementTree as pET

        if ET is None:
            ET = pET

        xml_types.append(pET._ElementInterface)
    except ImportError:
        pass

    for x in xml_types[:]:
        # hack for jython
        if x.__name__ == 'instance':
            xml_types.remove(x)

    xml_types = tuple(xml_types)

    return xml_types


def get_timestamp(d):
    """
    Returns a UTC timestamp for a C{datetime.datetime} object.

    @type d: C{datetime.datetime}
    @param d: The date object.
    @return: UTC timestamp.
    @rtype: C{str}

    @note: Inspiration taken from the U{Intertwingly blog
        <http://intertwingly.net/blog/2007/09/02/Dealing-With-Dates>}.
    """
    if isinstance(d, datetime.date) and not isinstance(d, datetime.datetime):
        d = datetime.datetime.combine(d, datetime.time(0, 0, 0, 0))

    msec = str(d.microsecond).rjust(6).replace(' ', '0')

    return float('%s.%s' % (calendar.timegm(d.utctimetuple()), msec))


def get_datetime(secs):
    """
    Return a UTC date from a timestamp.

    @type secs: C{long}
    @param secs: Seconds since 1970.
    @return: UTC timestamp.
    @rtype: C{datetime.datetime}
    """
    if negative_timestamp_broken and secs < 0:
        return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=secs)

    return datetime.datetime.utcfromtimestamp(secs)


def get_properties(obj):
    """
    Returns a list of properties for L{obj}

    @since: 0.5
    """
    if hasattr(obj, 'keys'):
        return obj.keys()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__.keys()

    return []


def set_attrs(obj, attrs):
    """
    A generic function which applies a collection of attributes C{attrs} to
    object C{obj}.

    @param obj: An instance implementing the C{__setattr__} function
    @param attrs: A collection implementing the C{iteritems} function
    @type attrs: Usually a dict
    """
    o = setattr

    if hasattr(obj, '__setitem__'):
        o = type(obj).__setitem__

    [o(obj, k, v) for k, v in attrs.iteritems()]


def get_class_alias(klass):
    """
    Returns a alias class suitable for klass. Defaults to L{pyamf.ClassAlias}
    """
    for k, v in pyamf.ALIAS_TYPES.iteritems():
        for kl in v:
            if isinstance(kl, types.FunctionType):
                if kl(klass) is True:
                    return k
            elif isinstance(kl, (type, (types.ClassType, types.ObjectType))):
                if issubclass(klass, kl):
                    return k

    return pyamf.ClassAlias


def is_class_sealed(klass):
    """
    Returns a C{boolean} whether or not the supplied class can accept dynamic
    properties.

    @rtype: C{bool}
    @since: 0.5
    """
    mro = inspect.getmro(klass)
    new = False

    if mro[-1] is object:
        mro = mro[:-1]
        new = True

    for kls in mro:
        if new and '__dict__' in kls.__dict__:
            return False

        if not hasattr(kls, '__slots__'):
            return False

    return True


def get_class_meta(klass):
    """
    Returns a C{dict} containing meta data based on the supplied class, useful
    for class aliasing.

    @rtype: C{dict}
    @since: 0.5
    """
    if not isinstance(klass, (type, types.ClassType)) or klass is object:
        raise TypeError('klass must be a class object, got %r' % type(klass))

    meta = {
        'static_attrs': None,
        'exclude_attrs': None,
        'readonly_attrs': None,
        'proxy_attrs': None,
        'amf3': None,
        'dynamic': None,
        'alias': None,
        'external': None,
        'synonym_attrs': None
    }

    if not hasattr(klass, '__amf__'):
        return meta

    a = klass.__amf__

    if type(a) is dict:
        in_func = lambda x: x in a
        get_func = a.__getitem__
    else:
        in_func = lambda x: hasattr(a, x)
        get_func = lambda x: getattr(a, x)

    for prop in ['alias', 'amf3', 'dynamic', 'external']:
        if in_func(prop):
            meta[prop] = get_func(prop)

    for prop in ['static', 'exclude', 'readonly', 'proxy', 'synonym']:
        if in_func(prop):
            meta[prop + '_attrs'] = get_func(prop)

    return meta


def get_module(mod_name):
    """
    Load a module based on `mod_name`.

    :type mod_name: `str`
    :param mod_name: The module name.
    :return: Module.

    :raise ImportError: Unable to import an empty module.
    """
    if mod_name is '':
        raise ImportError("Unable to import empty module")

    mod = __import__(mod_name)
    components = mod_name.split('.')

    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod


# init the module from here

find_xml_lib()

try:
    datetime.datetime.utcfromtimestamp(-31536000.0)
except ValueError:
    negative_timestamp_broken = True
