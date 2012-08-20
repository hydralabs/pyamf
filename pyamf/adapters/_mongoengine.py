
import pyamf
import pyamf.alias
from bson.dbref import (
        DBRef
    )
from bson.objectid import (
        ObjectId
    )
from mongoengine.base import (
        BaseDocument, BaseField
    )
from mongoengine import (
        ObjectIdField
    )

class MongoEngineDocumentAlias( pyamf.alias.ClassAlias ):
    """
        Encode a mongoengine document into something appropriate for transport.

        * Changes the "_id" attribute to "id", and makes it into a string.
        * Resolves any DBRef objects to their actual object
    """
    def getEncodableAttributes( self, obj, **kwargs ):
        data = {}
        for field_name, field in obj._fields.items():
            value = getattr(obj, field_name, None)
            if value is not None:
                data[field.db_field] = field.to_mongo(value)
                if isinstance( data[field.db_field], ObjectId ):
                    data[field.db_field] = str( data[field.db_field] )
                if isinstance( data[field.db_field], DBRef ):
                    data[field.db_field] = value
        if '_id' in data and data['_id'] is None:
            del data['_id']

        # ID should be id, not _id
        data['id'] = str(data['_id'])
        del( data['_id'] )

        if not obj._dynamic:
            return data

        for name, field in obj._dynamic_fields.items():
            data[name] = field.to_mongo(obj._data.get(name, None))
        return data
    def getDecodableAttributes( self, obj, attrs, codec=None ):
        data = {}
        fields = obj.__class__._fields
        for key,value in attrs.items():
            try:
                if isinstance( fields[key], ObjectIdField ) and value:
                    data[key] = ObjectId( value )
                else:
                    data[key] = value
            except KeyError:
                print "Got unknown key '%s' for %r" % ( key, obj )
        print data
        return data

def map_mongoengine_document(klass):
    if not isinstance( klass, type ):
        klass = type( klass )
    if issubclass( klass, BaseDocument ):
        return True
    return False

pyamf.register_alias_type( MongoEngineDocumentAlias, map_mongoengine_document )
