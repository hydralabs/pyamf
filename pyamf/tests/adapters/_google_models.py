from google.appengine.ext import db


class PetModel(db.Model):
    """
    """

    # 'borrowed' from http://code.google.com/appengine/docs/datastore/entitiesandmodels.html
    name = db.StringProperty(required=True)
    type = db.StringProperty(required=True, choices=set(["cat", "dog", "bird"]))
    birthdate = db.DateProperty()
    weight_in_pounds = db.IntegerProperty()
    spayed_or_neutered = db.BooleanProperty()


class PetExpando(db.Expando):
    """
    """

    name = db.StringProperty(required=True)
    type = db.StringProperty(required=True, choices=set(["cat", "dog", "bird"]))
    birthdate = db.DateProperty()
    weight_in_pounds = db.IntegerProperty()
    spayed_or_neutered = db.BooleanProperty()


class ListModel(db.Model):
    """
    """
    numbers = db.ListProperty(long)


class GettableModelStub(db.Model):
    """
    """

    gets = []

    @staticmethod
    def get(*args, **kwargs):
        GettableModelStub.gets.append([args, kwargs])


class Author(db.Model):
    name = db.StringProperty()


class Novel(db.Model):
    title = db.StringProperty()
    author = db.ReferenceProperty(Author)


class EmptyModel(db.Model):
    """
    A model that has no properties but also has no entities in the datastore.
    """


class LongIntegerProperty(db.IntegerProperty):
    """
    This property exists purely to convert longs on the server to string
    on the client.  We have to do this because Flash sucks and has 32-bit
    ints and 64-bit Numbers that can only contain 53-bit ints.  Flash has
    ruined my day again and forced me to create a property purely so that
    pyAMF will treat longs differently.
    """
    pass


class LongIntegerListProperty(db.ListProperty):
    """
    Same concept as LongIntegerProperty :(.
    """

    def __init__(self, *args, **kwds):
        super(LongIntegerListProperty, self).__init__(long, *args, **kwds)


class ModelStub(db.Model):
    class __amf__:
        as_bytes = ('test', 'test_list')

    test = LongIntegerProperty()
    test_list = LongIntegerListProperty()
