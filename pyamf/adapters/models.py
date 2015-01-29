"""
A large number of adapters interact with models of various kinds.

SQLAlchemy, Django, Google AppEngine etc.

This provides a place to have common functionality for interacting with those
types of models.

@since: 0.7.0
"""

#: mapping of Model property class -> handler
#: See L{register_property_decoder}
_property_decoders = {}


def register_property_decoder(prop_class, replace=False):
    """
    Decorator that will call the handler when decoding an attribute of a model.

    The handler will be given 2 parameters: The property instance being decoded
    and the value of the property that has been decoded. It is the job of the
    handler to return the value.

    @param prop_class: A L{db.Property} class.
    @param replace: Whether to replace an existing handler for a given
        property.
    @since: 0.7.0
    """
    def wrapped(handler):
        if not replace and prop_class in _property_decoders:
            raise KeyError('Handler %r already exists for prop %r' % (
                _property_decoders[prop_class],
                prop_class,
            ))

        _property_decoders[prop_class] = handler

        return wrapped

    return wrapped


def decode_model_properties(model_properties, attrs):
    """
    Given a dict of model properties (name -> property instance), and a set
    of decoded attributes (name -> value); apply each handler to a property, if
    available.
    """
    property_attrs = [k for k in attrs if k in model_properties]

    for name in property_attrs:
        prop = model_properties[name]
        handler = _property_decoders.get(prop.__class__, None)

        if not handler:
            continue

        attrs[name] = handler(prop, attrs[name])

    return attrs
