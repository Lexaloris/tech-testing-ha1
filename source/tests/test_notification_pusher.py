import unittest
import mock
import requests
from source.notification_pusher import create_pidfile
from source.notification_pusher import install_signal_handlers
from source.notification_pusher import notification_worker
from source import notification_pusher
from source.lib.utils import Config
from gevent import queue as gevent_queue


class TaskData:
    def __init__(self, data):
        self.data = data

    def copy(self):
        return self.data


class Task:
    def __init__(self, task_id, data):
        self.task_id = task_id
        self.data = TaskData(data)


class NotificationPusherTestCase(unittest.TestCase):
    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('source.notification_pusher.open', m_open, create=True):
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
        task = Task(12, data)
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
        task = Task(12, data)
        task.data = TaskData({
            "callback_url": "URL",
            "id": 1
        })
        response = requests.RequestException
        with mock.patch.object(requests, 'post', mock.Mock(side_effect=response)):
            with mock.patch('source.notification_pusher.logger', mock.Mock()):
                notification_worker(task, task_queue)
        task_queue.put.assert_called_once_with((task, 'bury'))

    def test_done_with_processed_tasks_all_well(self):
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value=1)
        task = mock.Mock()
        task_queue.get_nowait = mock.Mock(return_value=(task, "some_method"))
        notification_pusher.done_with_processed_tasks(task_queue)
        self.assertTrue(task.some_method.called)

    def test_done_with_processed_tasks_getattr_database_error(self):
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value=1)
        task = mock.Mock()
        task_queue.get_nowait = mock.Mock(return_value=(task, 'some_method'))
        logger = mock.MagicMock()
        import tarantool
        task.some_method = mock.Mock(side_effect=tarantool.DatabaseError())
        with mock.patch('source.notification_pusher.logger', logger):
            notification_pusher.done_with_processed_tasks(task_queue)
        self.assertTrue(logger.exception.called)

    def test_done_with_processed_tasks_gevent_queue_empty(self):
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value=1)
        task_queue.get_nowait = mock.Mock(side_effect=[gevent_queue.Empty()])
        logger = mock.MagicMock()
        task = mock.Mock()
        with mock.patch('source.notification_pusher.logger', logger):
            notification_pusher.done_with_processed_tasks(task_queue)
        self.assertFalse(logger.exception.called)
        self.assertFalse(task.some_method.called)

    def test_stop_handler(self):
        signum = 3
        old_run_application = notification_pusher.run_application
        old_exit_code = notification_pusher.exit_code
        notification_pusher.stop_handler(signum)
        self.assertEqual(notification_pusher.run_application, False)
        self.assertEqual(notification_pusher.exit_code, notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum)
        notification_pusher.run_application = old_run_application
        notification_pusher.exit_code = old_exit_code

    def test_main_loop_task_is_not_exist(self):
        config = Config()
        config.QUEUE_HOST = 'localhost'
        config.QUEUE_PORT = 80
        config.QUEUE_SPACE = 0
        config.QUEUE_TUBE = 'name'
        config.QUEUE_TAKE_TIMEOUT = 0
        config.WORKER_POOL_SIZE = 1
        config.SLEEP = 1
        config.HTTP_CONNECTION_TIMEOUT = 2
        queue = mock.MagicMock()
        tube = mock.MagicMock()
        queue.tube = mock.Mock(return_value=tube)
        tube.take = mock.Mock(return_value=None)
        initial_run_application = notification_pusher.run_application

        def break_run(*args, **kwargs):
            notification_pusher.run_application = False

        notification_pusher.run_application = True
        mock_sleep = mock.Mock(side_effect=break_run)
        mock_done_with_processed_tasks = mock.Mock()
        with mock.patch('source.notification_pusher.tarantool_queue.Queue', mock.Mock(return_value=queue)) as Queue:
            with mock.patch('source.notification_pusher.done_with_processed_tasks', mock_done_with_processed_tasks):
                with mock.patch('source.notification_pusher.sleep', mock_sleep):
                    notification_pusher.main_loop(config)
        mock_done_with_processed_tasks.assert_called_once()
        mock_sleep.assert_called_once_with(config.SLEEP)
        notification_pusher.run_application = initial_run_application

    def test_main_loop_task_is_exist(self):
        config = Config()
        config.QUEUE_HOST = 'localhost'
        config.QUEUE_PORT = 80
        config.QUEUE_SPACE = 0
        config.QUEUE_TUBE = 'name'
        config.QUEUE_TAKE_TIMEOUT = 0
        config.WORKER_POOL_SIZE = 1
        config.SLEEP = 1
        config.HTTP_CONNECTION_TIMEOUT = 2
        queue = mock.MagicMock()
        tube = mock.MagicMock()
        queue.tube = mock.Mock(return_value=tube)
        tube.take = mock.Mock()
        initial_run_application = notification_pusher.run_application

        def break_run(*args, **kwargs):
            notification_pusher.run_application = False

        notification_pusher.run_application = True
        mock_sleep = mock.Mock(side_effect=break_run)
        mock_done_with_processed_tasks = mock.Mock()
        with mock.patch('source.notification_pusher.tarantool_queue.Queue', mock.Mock(return_value=queue)) as Queue:
            with mock.patch('source.notification_pusher.done_with_processed_tasks', mock_done_with_processed_tasks):
                with mock.patch('source.notification_pusher.sleep', mock_sleep):
                    notification_pusher.main_loop(config)
        mock_done_with_processed_tasks.assert_called_once()
        mock_sleep.assert_called_once_with(config.SLEEP)
        notification_pusher.run_application = initial_run_application

    def test_parse_cmd_args(self):
        mock_args = '12'
        with mock.patch('source.lib.utils.argparse.ArgumentParser.parse_args', mock.Mock()) as mock_parse:
            notification_pusher.parse_cmd_args(mock_args)
        mock_parse.assert_called_once()

    def test_daemonize_parent(self):
        pid = 12
        mock_os_fork = mock.Mock(return_value=pid)
        mock_os_exit = mock.Mock()
        with mock.patch('source.notification_pusher.os.fork', mock_os_fork):
            with mock.patch('source.notification_pusher.os._exit', mock_os_exit):
                notification_pusher.daemonize()
        mock_os_exit.assert_called_once_with(0)
        mock_os_fork.assert_called_once_with()

    def test_daemonize_oserror(self):
        mock_os_fork = mock.Mock(side_effect=OSError)
        with mock.patch('source.notification_pusher.os.fork', mock_os_fork):
            self.assertRaises(Exception, notification_pusher.daemonize)

    def test_daemonize_child_parent(self):
        pid = 0
        mock_os_fork = mock.Mock(side_effect=[pid, 12])
        mock_os_exit = mock.Mock()
        mock_os_setsid = mock.Mock()
        with mock.patch('source.notification_pusher.os.fork', mock_os_fork):
            with mock.patch('source.notification_pusher.os._exit', mock_os_exit):
                with mock.patch('source.notification_pusher.os.setsid', mock_os_setsid):
                    notification_pusher.daemonize()
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
                    notification_pusher.daemonize()
        self.assertFalse(mock_os_exit.called)
        mock_os_setsid.assert_called_once_with()
        self.assertTrue(mock_os_fork.call_count, 2)

    def test_daemonize_child_oserror(self):
        pid = 0
        mock_os_setsid = mock.Mock()
        mock_os_fork = mock.Mock(side_effect=[pid, OSError])
        with mock.patch('source.notification_pusher.os.fork', mock_os_fork):
            with mock.patch('source.notification_pusher.os.setsid', mock_os_setsid):
                self.assertRaises(Exception, notification_pusher.daemonize)
        mock_os_setsid.assert_called_once_with()
        self.assertTrue(mock_os_fork.call_count, 2)

    def test_load_config_from_pyfile(self):
        result = notification_pusher.load_config_from_pyfile('source/tests/test_config.py')
        self.assertEqual(result.TEST_KEY_1, 1)
        self.assertEqual(result.TEST_KEY_2, 'test_value_2')
        self.assertEqual(result.TEST_KEY_3, {
            'test_key_3_1': 'test_value_3_1',
            'test_key_3_2': 'test_value_3_2'
        })
        self.assertEqual(result.TEST_KEY_4, '')
        self.assertFalse(hasattr(result, 'Test_Key_5'))

    def test_main_daemon_and_pidfile_given_and_main_loop_is_fine(self):
        mock_argv = [1, 1, 1]
        mock_parse_cmd_args = mock.Mock()
        config = Config()
        config.LOGGING = mock.Mock()
        mock_dictConfig = mock.Mock()
        initial_run_application = notification_pusher.run_application

        def break_run(*args, **kwargs):
            notification_pusher.run_application = False

        mock_main_loop = mock.Mock(side_effect=break_run)
        mock_daemonize = mock.Mock()
        mock_create_pidfile = mock.Mock()
        notification_pusher.run_application = True
        with mock.patch('source.notification_pusher.daemonize', mock_daemonize):
            with mock.patch('source.notification_pusher.parse_cmd_args', mock_parse_cmd_args):
                with mock.patch('source.notification_pusher.dictConfig', mock_dictConfig):
                    with mock.patch('source.notification_pusher.main_loop', mock_main_loop):
                        with mock.patch('source.notification_pusher.load_config_from_pyfile',
                                        mock.Mock(return_value=config)):
                            with mock.patch('source.notification_pusher.os.path.realpath',
                                        mock.Mock()):
                                with mock.patch('source.notification_pusher.os.path.expanduser',
                                        mock.Mock()):
                                    with mock.patch('source.notification_pusher.create_pidfile',
                                                    mock_create_pidfile):
                                        with mock.patch('source.notification_pusher.patch_all', mock.Mock()):
                                            exit_code = notification_pusher.main(mock_argv)
        mock_daemonize.assert_called_once_with()
        mock_create_pidfile.assert_called()
        mock_dictConfig.assert_called_once_with(config.LOGGING)
        mock_main_loop.assert_called_once_with(config)
        assert notification_pusher.exit_code == exit_code
        notification_pusher.run_application = initial_run_application

    def test_main_daemon_and_pidfile_given_and_main_loop_is_bad(self):
        mock_argv = [1, 1, 1]
        mock_parse_cmd_args = mock.Mock()
        config = Config()
        config.LOGGING = mock.Mock()
        config.SLEEP_ON_FAIL = 23
        mock_dictConfig = mock.Mock()
        initial_run_application = notification_pusher.run_application


        def break_run(*args, **kwargs):
            notification_pusher.run_application = False

        mock_main_loop_exseption = mock.Mock(side_effect=Exception)
        mock_daemonize = mock.Mock()
        mock_create_pidfile = mock.Mock()
        mock_sleep = mock.Mock(side_effect=break_run)
        notification_pusher.run_application = True
        with mock.patch('source.notification_pusher.daemonize', mock_daemonize):
            with mock.patch('source.notification_pusher.parse_cmd_args', mock_parse_cmd_args):
                with mock.patch('source.notification_pusher.dictConfig', mock_dictConfig):
                    with mock.patch('source.notification_pusher.main_loop', mock_main_loop_exseption):
                        with mock.patch('source.notification_pusher.load_config_from_pyfile',
                                        mock.Mock(return_value=config)):
                            with mock.patch('source.notification_pusher.os.path.realpath',
                                        mock.Mock()):
                                with mock.patch('source.notification_pusher.os.path.expanduser',
                                        mock.Mock()):
                                    with mock.patch('source.notification_pusher.create_pidfile',
                                                    mock_create_pidfile):
                                        with mock.patch('source.notification_pusher.patch_all', mock.Mock()):
                                            with mock.patch('source.notification_pusher.sleep',
                                                            mock_sleep):
                                                with mock.patch('source.notification_pusher.logger',
                                                            mock.Mock()):
                                                    exit_code = notification_pusher.main(mock_argv)
        mock_daemonize.assert_called_once_with()
        mock_create_pidfile.assert_called()
        mock_dictConfig.assert_called_once_with(config.LOGGING)
        mock_main_loop_exseption.assert_called_once_with(config)
        mock_sleep.assert_called_once_with(config.SLEEP_ON_FAIL)
        assert notification_pusher.exit_code == exit_code
        notification_pusher.run_application = initial_run_application