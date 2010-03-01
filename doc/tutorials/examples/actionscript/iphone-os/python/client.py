#!/usr/bin/python
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
iPhone example client.

@see: U{IPhoneOSExample<http://pyamf.org/wiki/IPhoneOSExample>} wiki page.

@since: 0.4
"""

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
)

import server

from pyamf.remoting.client import RemotingService

url = 'http://localhost:8000'
client = RemotingService(url, logger=logging)

service = client.getService('addressbook')
print service.getContacts()
