import unittest
import mock
from source.lib import utils


class LibUtilsTestCase(unittest.TestCase):
    # daemonize()
        #positive_tests
    def test_daemonize_parent(self):
        pid = 42
        with mock.patch('os.fork', mock.Mock(return_value=pid)) as os_fork:
            with mock.patch('os._exit', mock.Mock()) as os_exit:
                utils.daemonize()

        os_fork.assert_called_once_with()
        os_exit.assert_called_once_with(0)

    def test_daemonize_child_child(self):
        pid = 0
        with mock.patch('os.fork', mock.Mock(return_value=pid)) as os_fork:
            with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    utils.daemonize()

        os_setsid.assert_called_once_with()
        assert os_fork.called
        assert not os_exit.called

    def test_daemonize_child_parent(self):
        child_pid = 0
        parent_pid = 42
        with mock.patch('os.fork', mock.Mock(side_effect=[child_pid, parent_pid])):
            with mock.patch('os.setsid', mock.Mock()):
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    utils.daemonize()

        os_exit.assert_called_once_with(0)

        #negative_tests
    def test_daemonize_oserror(self):
        exc = OSError("err")
        with mock.patch('os.fork', mock.Mock(side_effect=exc)):
            self.assertRaises(Exception, utils.daemonize)

    def test_daemonize_child_oserror(self):
        pid = 0
        exc = OSError("err")
        with mock.patch('os.fork', mock.Mock(side_effect=[pid, exc])):
            with mock.patch('os._exit', mock.Mock()):
                with mock.patch('os.setsid', mock.Mock()):
                    self.assertRaises(Exception, utils.daemonize)

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
        #positive_tests
    def test_parse_cmd_args_abbr(self):
        import argparse

        app_name = 'app_name'
        app_description = 'app_description'
        config_path = '/file/path'
        pid = 42
        args = '%s -c %s -d -P %d' % (app_name, config_path, pid)
        return_value = utils.parse_cmd_args(args.split(' ')[1:], app_description)
        self.assertEqual(argparse.Namespace(config=config_path, daemon=True, pidfile=str(pid)), return_value)

    def test_parse_cmd_args_full(self):
        import argparse

        app_name = 'app_name'
        app_description = 'app_description'
        config_path = '/file/path'
        pid = 0
        args = '%s --daemon --pid %d --config %s' % (app_name, pid, config_path)
        return_value = utils.parse_cmd_args(args.split(' ')[1:], app_description)
        self.assertEqual(argparse.Namespace(config=config_path, daemon=True, pidfile=str(pid)), return_value)

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

    def test_check_network_status_false(self):
        import urllib2
        import socket
        url = 'url.ru'
        timeout = 30
        with mock.patch('urllib2.urlopen', mock.Mock(side_effect=[urllib2.URLError('because'),
                                                                  socket.error(),
                                                                  ValueError])):
            self.assertFalse(utils.check_network_status(url, timeout))
            self.assertFalse(utils.check_network_status(url, timeout))
            self.assertFalse(utils.check_network_status(url, timeout))