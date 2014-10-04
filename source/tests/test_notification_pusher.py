import unittest
import mock
import requests
from notification_pusher import create_pidfile
from notification_pusher import install_signal_handlers
from notification_pusher import notification_worker
from notification_pusher import done_with_processed_tasks
from source import notification_pusher


class TaskData:
    def __init__(self, data):
        self.data = data

    def copy(self):
        return self.data


class TestTask:
    def __init__(self, task_id, data):
        self.task_id = task_id
        self.data = TaskData(data)


class NotificationPusherTestCase(unittest.TestCase):
    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('notification_pusher.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_install_signal_handlers(self):
        mock_signal = mock.Mock()
        with mock.patch('gevent.signal', mock_signal):
                install_signal_handlers()
        assert mock_signal.call_count == 4

    def test_notification_worker(self):
        task_queue = mock.Mock()
        data = TaskData({
            "callback_url": "URL",
            "id": 1
        })
        task = TestTask(12, data)
        task.data = TaskData({
            "callback_url": "URL",
            "id": 1
        })
        response = mock.Mock()
        with mock.patch.object(requests, 'post', mock.Mock(return_value=response)):
            notification_worker(task, task_queue)
        task_queue.put.assert_called_once_with((task, 'ack'))

    def test_notification_worker_with_exception(self):
        task_queue = mock.Mock()
        data = TaskData({
            "callback_url": "URL",
            "id": 1
        })
        task = TestTask(12, data)
        task.data = TaskData({
            "callback_url": "URL",
            "id": 1
        })
        response = requests.RequestException
        with mock.patch.object(requests, 'post', mock.Mock(side_effect=response)):
            notification_worker(task, task_queue)
        task_queue.put.assert_called_once_with((task, 'bury'))

    # def test_done_with_processed_tasks(self):
    #     task_queue = mock.Mock()
    #     task_queue.qsize = mock.Mock(return_value=2)
    #     task_queue.get_nowait = mock.Mock(return_value=(3, 6))
    #     with mock.patch('action_name.capitalize', mock.MagicMock()):
    #         with mock.patch('task.task_id', mock.Mock(return_value=12)):
    #             done_with_processed_tasks(task_queue)

    def test_stop_handler(self):
        signum = 3
        old_run_application = notification_pusher.run_application
        old_exit_code = notification_pusher.exit_code
        notification_pusher.stop_handler(signum)
        self.assertEqual(notification_pusher.run_application, False)
        self.assertEqual(notification_pusher.exit_code, notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum)
        run_application = old_run_application
        exit_code = old_exit_code

    # def test_main_loop(self):
    #     self.assertEqual(True, True)
    #
    # def test_main_args_daemon_exist(self):
    #     argv = [1, 1, 1, 1]
    #     notification_pusher.run_application = False
    #     with mock.patch('source.notification_pusher.daemonize', mock.Mock()) as daemonize,\
    #         mock.patch('source.notification_pusher.load_config_from_pyfile', mock.Mock(return_value=self.config)):
    #         notification_pusher.main(['','-d', '-c', './source/tests/config/pusher_config.py'])
    #         daemonize.assert_called_once()
    #     # with mock.patch('parse_cmd_args', mock.MagicMock(return_value='daemon')):
    #     notification_pusher.main(argv)
    #     self.assertEqual(True, True)

    def test_parse_cmd_args_abbr(self):
        import argparse
        app_name = 'app_name'
        config_path = '/file/path'
        pid = 42
        args = '%s -c %s -d -P %d' % (app_name, config_path, pid)
        return_value = notification_pusher.parse_cmd_args(args.split(' ')[1:])
        self.assertEqual(argparse.Namespace(config=config_path, daemon=True, pidfile=str(pid)), return_value)

    def test_parse_cmd_args_full(self):
        import argparse
        app_name = 'app_name'
        config_path = '/file/path'
        pid = 0
        args = '%s --daemon --pid %d --config %s' % (app_name, pid, config_path)
        return_value = notification_pusher.parse_cmd_args(args.split(' ')[1:])
        self.assertEqual(argparse.Namespace(config=config_path, daemon=True, pidfile=str(pid)), return_value)

    # daemonize()
        #positive_tests
    def test_daemonize_parent(self):
        pid = 42
        with mock.patch('os.fork', mock.Mock(return_value=pid)) as os_fork:
            with mock.patch('os._exit', mock.Mock()) as os_exit:
                notification_pusher.daemonize()

        os_fork.assert_called_once_with()
        os_exit.assert_called_once_with(0)

    def test_daemonize_child_child(self):
        pid = 0
        with mock.patch('os.fork', mock.Mock(return_value=pid)) as os_fork:
            with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    notification_pusher.daemonize()

        os_setsid.assert_called_once_with()
        assert os_fork.called
        assert not os_exit.called

    def test_daemonize_child_parent(self):
        child_pid = 0
        parent_pid = 42
        with mock.patch('os.fork', mock.Mock(side_effect=[child_pid, parent_pid])):
            with mock.patch('os.setsid', mock.Mock()):
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    notification_pusher.daemonize()

        os_exit.assert_called_once_with(0)

        #negative_tests
    def test_daemonize_oserror(self):
        exc = OSError("err")
        with mock.patch('os.fork', mock.Mock(side_effect=exc)):
            self.assertRaises(Exception, notification_pusher.daemonize)

    def test_daemonize_child_oserror(self):
        pid = 0
        exc = OSError("err")
        with mock.patch('os.fork', mock.Mock(side_effect=[pid, exc])):
            with mock.patch('os._exit', mock.Mock()):
                with mock.patch('os.setsid', mock.Mock()):
                    self.assertRaises(Exception, notification_pusher.daemonize)

    #load_config_from_pyfile(filepath)
        #positive_tests
    # def test_load_config_from_pyfile(self):
    #     result = notification_pusher.load_config_from_pyfile('source/tests/test_config.py')
    #     self.assertEqual(result.TEST_KEY_1, 1)
    #     self.assertEqual(result.TEST_KEY_2, 'test_value_2')
    #     self.assertEqual(result.TEST_KEY_3, {
    #         'test_key_3_1': 'test_value_3_1',
    #         'test_key_3_2': 'test_value_3_2'
    #     })
    #     self.assertEqual(result.TEST_KEY_4, '')
    #     self.assertFalse(hasattr(result, 'Test_Key_5'))