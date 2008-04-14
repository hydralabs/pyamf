# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Google App Engine adapter module.

Sets up basic type mapping and class mappings for using the Google App Engine
db api.

@see: U{Google App Engine<http://code.google.com/appengine/>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}
@since: 0.3
"""

from google.appengine.ext import db

import pyamf

def get_attrs_for_model(obj):
    """
    Returns a list of properties on an C{db.Model} instance
    """
    return list(obj.__class__._properties)

def get_attrs_for_expando(obj):
    """
    Returns a list of dynamic properties on a L{db.Expando} instance
    """
    return obj.dynamic_properties()

pyamf.register_class(db.Model, attr_func=get_attrs_for_model, metadata=['dynamic'])
pyamf.register_class(db.Expando, attr_func=get_attrs_for_expando, metadata=['dynamic'])
