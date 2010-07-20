# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
XML handling helpers

@since: 0.6
"""

__all__ = [
    'find_xml_lib',
    'is_xml_type',
    'set_xml_type'
]

#: list of supported third party packages that support the C{ElementTree}
#: interface. At least enough for our needs anyway.
ETREE_MODULES = [
    'xml.etree.cElementTree',
    'cElementTree',
    'xml.etree.ElementTree',
    'elementtree.ElementTree'
]

#: XML types.
xml_types = None
xml_modules = None

ET = None


def find_xml_lib():
    """
    Run through L{ETREE_MODULES} and find C{ElementTree} implementations so
    that any type can be encoded.

    We work through the C implementations first, then the pure Python versions.
    The downside to this is that B{all} libraries will be imported but I{only}
    one is ever used. The libs are small (relatively) and the flexibility that
    this gives seems to outweigh the cost. Time will tell.

    @since: 0.4
    """
    from pyamf.util import get_module

    types = []
    modules = []

    for mod in ETREE_MODULES:
        try:
            etree = get_module(mod)
        except ImportError:
            continue

        modules.append(etree)
        e = etree.Element('foo')

        try:
            types.append(e.__class__)
        except AttributeError:
            types.append(type(e))

    # hack for jython
    for x in types[:]:
        if x.__name__ == 'instance':
            types.remove(x)

    return tuple(types), tuple(modules)


def set_xml_type(t):
    """
    Sets the default type that PyAMF will use to construct XML objects,
    supplying the stringified XML to the caller.
    """
    global xml_modules, ET

    if xml_modules is None:
        xml_modules = (t,)
    else:
        types = set(xml_modules)
        types.update([t])

        xml_modules = tuple(types)

    ET = t


def is_xml_type(t):
    """
    Determines if the type object is a valid XML type.

    If L{xml_types} is not populated then it will call L{find_xml_lib}.
    """
    global xml_types, xml_modules, ET

    if xml_types is None:
        xml_types, xml_modules = find_xml_lib()

    if ET is None:
        try:
            ET = xml_modules[0]
        except IndexError:
            return False

    return isinstance(t, xml_types)
