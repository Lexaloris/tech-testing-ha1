#!/usr/bin/env python2.7

import contextlib
import os
import socket
import sys
import unittest

source_dir = os.path.join(os.path.dirname(__file__), 'source')
sys.path.insert(0, source_dir)

from source.tests.test_notification_pusher import NotificationPusherTestCase
from source.tests.test_redirect_checker import RedirectCheckerTestCase
from source.tests.test_lib_utils import LibUtilsTestCase
from source.tests.test_lib_worker import LibWorkerTestCase
from source.tests.test_lib__init import LibInitTestCase


def _create_connection(*args, **kwargs):
    raise AssertionError('Unmocked http request')


@contextlib.contextmanager
def mocked_connection():
    original_connection = socket.create_connection
    socket.create_connection = _create_connection
    yield
    socket._create_connection = original_connection


if __name__ == '__main__':
    suite = unittest.TestSuite((
        unittest.makeSuite(NotificationPusherTestCase),
        unittest.makeSuite(RedirectCheckerTestCase),
        unittest.makeSuite(LibUtilsTestCase),
        unittest.makeSuite(LibWorkerTestCase),
        unittest.makeSuite(LibInitTestCase),
    ))
    with mocked_connection():
        result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
