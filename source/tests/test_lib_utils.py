import unittest
import mock
from source.lib import utils


class LibUtilsTestCase(unittest.TestCase):
    # daemonize()
    def test_daemonize_parent(self):
        pid = 12
        mock_os_fork = mock.Mock(return_value=pid)
        mock_os_exit = mock.Mock()
        with mock.patch('source.notification_pusher.os.fork', mock_os_fork):
            with mock.patch('source.notification_pusher.os._exit', mock_os_exit):
                utils.daemonize()
        mock_os_exit.assert_called_once_with(0)
        mock_os_fork.assert_called_once_with()

    def test_daemonize_oserror(self):
        mock_os_fork = mock.Mock(side_effect=OSError)
        with mock.patch('source.notification_pusher.os.fork', mock_os_fork):
            self.assertRaises(Exception, utils.daemonize)

    def test_daemonize_child_parent(self):
        pid = 0
        mock_os_fork = mock.Mock(side_effect=[pid, 12])
        mock_os_exit = mock.Mock()
        mock_os_setsid = mock.Mock()
        with mock.patch('source.notification_pusher.os.fork', mock_os_fork):
            with mock.patch('source.notification_pusher.os._exit', mock_os_exit):
                with mock.patch('source.notification_pusher.os.setsid', mock_os_setsid):
                    utils.daemonize()
        mock_os_exit.assert_called_once_with(0)
        mock_os_setsid.assert_called_once_with()
        self.assertTrue(mock_os_fork.call_count, 2)

    def test_daemonize_child_child(self):
        pid = 0
        mock_os_fork = mock.Mock(return_value=pid)
        mock_os_exit = mock.Mock()
        mock_os_setsid = mock.Mock()
        with mock.patch('source.notification_pusher.os.fork', mock_os_fork):
            with mock.patch('source.notification_pusher.os._exit', mock_os_exit):
                with mock.patch('source.notification_pusher.os.setsid', mock_os_setsid):
                    utils.daemonize()
        self.assertFalse(mock_os_exit.called)
        mock_os_setsid.assert_called_once_with()
        self.assertTrue(mock_os_fork.call_count, 2)

    def test_daemonize_child_oserror(self):
        pid = 0
        mock_os_setsid = mock.Mock()
        mock_os_fork = mock.Mock(side_effect=[pid, OSError])
        with mock.patch('source.notification_pusher.os.fork', mock_os_fork):
            with mock.patch('source.notification_pusher.os.setsid', mock_os_setsid):
                self.assertRaises(Exception, utils.daemonize)
        mock_os_setsid.assert_called_once_with()
        self.assertTrue(mock_os_fork.call_count, 2)

    #create_pidfile(pidfile_path)
        #positive_tests
    def test_create_pidfile(self):
        pid = 42
        pidfile = '/file/path'
        m_open = mock.mock_open()
        with mock.patch('source.lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile(pidfile)

        m_open.assert_called_once_with(pidfile, 'w')
        m_open().write.assert_called_once_with(str(pid))

    #load_config_from_pyfile(filepath)
        #positive_tests
    def test_load_config_from_pyfile(self):
        result = utils.load_config_from_pyfile('source/tests/test_config.py')
        self.assertEqual(result.TEST_KEY_1, 1)
        self.assertEqual(result.TEST_KEY_2, 'test_value_2')
        self.assertEqual(result.TEST_KEY_3, {
            'test_key_3_1': 'test_value_3_1',
            'test_key_3_2': 'test_value_3_2'
        })
        self.assertEqual(result.TEST_KEY_4, '')
        self.assertFalse(hasattr(result, 'Test_Key_5'))

    #parse_cmd_args(args, app_description='')
    def test_parse_cmd_args(self):
        mock_args = 'args'
        with mock.patch('source.lib.utils.argparse.ArgumentParser.parse_args', mock.Mock()) as mock_parse:
            utils.parse_cmd_args(mock_args)
        mock_parse.assert_called_once()

    #get_tube(host, port, space, name)
        #positive_tests
    def test_get_tube(self):
        host = 'localhost'
        port = 80
        space = 0
        name = 'tube_name'
        queue = mock.MagicMock()
        queue.tube = mock.Mock()
        with mock.patch('source.lib.utils.tarantool_queue.Queue', mock.Mock(return_value=queue)) as Queue:
            utils.get_tube(host, port, space, name)

        Queue.assert_called_once_with(host=host, port=port, space=space)

    #spawn_workers(num, target, args, parent_pid)
        #positive_tests
    def test_spawn_workers(self):
        num = 10
        target = mock.Mock()
        args = ''
        parent_pid = 42
        process = mock.MagicMock()
        process.daemon = False
        process.start = mock.Mock()
        with mock.patch('source.lib.utils.Process', mock.Mock(return_value=process)) as Process:
            utils.spawn_workers(num, target, args, parent_pid)

        assert Process.call_count == num
        self.assertTrue(Process.daemon)

    #check_network_status
        #positive_tests
    def test_check_network_status_true(self):
        url = 'url.ru'
        timeout = 30
        with mock.patch('urllib2.urlopen', mock.Mock()):
            self.assertTrue(utils.check_network_status(url, timeout))

    def test_check_network_status_urllib2_error(self):
        url = 'url.ru'
        timeout = 30
        import urllib2
        with mock.patch('urllib2.urlopen', mock.Mock(side_effect=urllib2.URLError('urlerror'))):
            self.assertFalse(utils.check_network_status(url, timeout))

    def test_check_network_status_socket_error(self):
        url = 'url.ru'
        timeout = 30
        import socket
        with mock.patch('urllib2.urlopen', mock.Mock(side_effect=socket.error())):
            self.assertFalse(utils.check_network_status(url, timeout))

    def test_check_network_status_value_error(self):
        url = 'url.ru'
        timeout = 30
        with mock.patch('urllib2.urlopen', mock.Mock(side_effect=ValueError)):
            self.assertFalse(utils.check_network_status(url, timeout))