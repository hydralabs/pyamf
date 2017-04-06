# Py3AMF
Py3AMF is fork of [PyAMF](https://github.com/hydralabs/pyamf) to support Python3

### Why Py3AMF
By states of issues and PR in [PyAMF](https://github.com/hydralabs/pyamf), it dosen't seems to be under developing.
And another PR that supports Py3 has been discontinued for over two years.
This is the only Python AMF Project which trying to support Py3 under developing on GitHub.

### State
Pass `setup.py test`
But, adapters were not tested

### Warning
This project isn't completed.
If you want to make it fast, please send PR.

## TODO
- Check adapters

------------------------------------------------------

[PyAMF](http://www.pyamf.org) provides Action Message Format ([AMF](http://en.wikipedia.org/wiki/Action_Message_Format)) support for [Python](http://python.org) that is compatible with the [Adobe Flash Player](http://en.wikipedia.org/wiki/Flash_Player). It includes integration with Python web frameworks like [Django](http://djangoproject.com), [Pylons](http://pylonshq.com), [Twisted](http://twistedmatrix.com), [SQLAlchemy](http://sqlalchemy.org), [web2py](http://www.web2py.com) and [more](http://pyamf.org/tutorials/index.html).

The [Adobe Integrated Runtime](http://en.wikipedia.org/wiki/Adobe_AIR) and [Adobe Flash Player](http://en.wikipedia.org/wiki/Flash_Player) use AMF to communicate between an application and a remote server. AMF encodes remote procedure calls (RPC) into a compact binary representation that can be transferred over HTTP/HTTPS or the [RTMP/RTMPS](http://en.wikipedia.org/wiki/Real_Time_Messaging_Protocol) protocol. Objects and data values are serialized into this binary format, which increases performance, allowing applications to load data up to 10 times faster than with text-based formats such as XML or SOAP.

AMF3, the default serialization for [ActionScript](http://dev.pyamf.org/wiki/ActionScript) 3.0, provides various advantages over AMF0, which is used for ActionScript 1.0 and 2.0. AMF3 sends data over the network more efficiently than AMF0. AMF3 supports sending `int` and `uint` objects as integers and supports data types that are available only in ActionScript 3.0, such as [ByteArray](http://dev.pyamf.org/wiki/ByteArray), [ArrayCollection](http://dev.pyamf.org/wiki/ArrayCollection), [ObjectProxy](http://dev.pyamf.org/wiki/ObjectProxy) and [IExternalizable](http://dev.pyamf.org/wiki/IExternalizable).
