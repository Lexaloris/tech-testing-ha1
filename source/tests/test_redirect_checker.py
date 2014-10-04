import unittest
import mock
from source.lib.utils import Config
from source import redirect_checker
from lib.worker import worker
from multiprocessing import active_children
import argparse
from logging.config import dictConfig
# from source.lib import utils
# from lib.utils import (check_network_status, create_pidfile, daemonize,
#                        load_config_from_pyfile, parse_cmd_args, spawn_workers)


class TestActiveChildren:
    child = mock.Mock()

    def __init__(self, length):
        self.children = [self.child] * length

    def __len__(self):
        return len(self.children)

    def __call__(self):
        return self.children

    def __iter__(self):
        return iter(self.children)


class RedirectCheckerTestCase(unittest.TestCase):
    def test_main_loop_network_status_is_fine_and_workers_exist(self):
        pid = 23
        config = Config()
        config.SLEEP = 8
        config.CHECK_URL = 'test_url'
        config.HTTP_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 50
        mock_spawn_workers = mock.Mock()
        mock_check_network_status = mock.Mock(return_value=True)

        def break_run(*args, **kwargs):
            redirect_checker.run_checker = False

        active_children = TestActiveChildren(2)
        required_workers_count = config.WORKER_POOL_SIZE - len(active_children())
        mock_sleep = mock.Mock(side_effect=break_run)
        with mock.patch('source.redirect_checker.check_network_status', mock_check_network_status):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                with mock.patch('source.redirect_checker.active_children', active_children):
                    with mock.patch('source.redirect_checker.spawn_workers', mock_spawn_workers):
                        with mock.patch('source.redirect_checker.sleep', mock_sleep):
                            redirect_checker.main_loop(config)
        num = mock_spawn_workers.call_args[1]['num']
        parent_id = mock_spawn_workers.call_args[1]['parent_pid']
        mock_sleep.assert_called_once_with(config.SLEEP)
        mock_spawn_workers.assert_called_once()
        assert num == required_workers_count
        assert pid == parent_id
        redirect_checker.run_checker = True

    def test_main_loop_network_status_is_fine_and_workers_not_exist(self):
        pid = 23
        config = Config()
        config.SLEEP = 8
        config.CHECK_URL = 'test_url'
        config.HTTP_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 2
        mock_spawn_workers = mock.Mock()
        mock_check_network_status = mock.Mock(return_value=True)

        def break_run(*args, **kwargs):
            redirect_checker.run_checker = False

        active_children = TestActiveChildren(2)
        required_workers_count = config.WORKER_POOL_SIZE - len(active_children())
        mock_sleep = mock.Mock(side_effect=break_run)
        with mock.patch('source.redirect_checker.check_network_status', mock_check_network_status):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                with mock.patch('source.redirect_checker.active_children', active_children):
                    with mock.patch('source.redirect_checker.spawn_workers', mock_spawn_workers):
                        with mock.patch('source.redirect_checker.sleep', mock_sleep):
                            redirect_checker.main_loop(config)
        assert mock_spawn_workers.call_count == 0
        mock_sleep.assert_called_once_with(config.SLEEP)
        redirect_checker.run_checker = True

    def test_main_loop_network_status_is_not_fine(self):
        pid = 23
        config = Config()
        config.SLEEP = 8
        config.CHECK_URL = 'test_url'
        config.HTTP_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 2
        mock_spawn_workers = mock.Mock()
        mock_check_network_status = mock.Mock(return_value=False)

        def break_run(*args, **kwargs):
            redirect_checker.run_checker = False

        test_active_children = mock.Mock()
        mock_sleep = mock.Mock(side_effect=break_run)
        with mock.patch('source.redirect_checker.check_network_status', mock_check_network_status):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                with mock.patch('source.redirect_checker.active_children',
                                mock.Mock(return_value=[test_active_children])):
                        with mock.patch('source.redirect_checker.sleep', mock_sleep):
                            redirect_checker.main_loop(config)
        assert mock_spawn_workers.call_count == 0
        test_active_children.terminate.assert_called_once()
        mock_sleep.assert_called_once_with(config.SLEEP)
        redirect_checker.run_checker = True

    def test_main_args_daemon_exist(self):
        mock_argv = mock.MagicMock()
        mock_parse_cmd_args = mock.Mock()
        config = Config()
        config.LOGGING = mock.Mock()
        config.EXIT_CODE = 100
        mock_dictConfig = mock.Mock()
        mock_main_loop = mock.Mock()
        mock_daemonize = mock.Mock()
        mock_create_pidfile = mock.Mock()
        mock_argv.daemon = mock.Mock()
        with mock.patch('source.redirect_checker.daemonize', mock_daemonize):
            with mock.patch('source.redirect_checker.parse_cmd_args', mock_parse_cmd_args):
                with mock.patch('source.redirect_checker.dictConfig', mock_dictConfig):
                    with mock.patch('source.redirect_checker.main_loop', mock_main_loop):
                        with mock.patch('source.redirect_checker.load_config_from_pyfile',
                                        mock.Mock(return_value=config)):
                            with mock.patch('source.redirect_checker.os.path.realpath',
                                        mock.Mock()):
                                with mock.patch('source.redirect_checker.os.path.expanduser',
                                        mock.Mock()):
                                    with mock.patch('source.redirect_checker.create_pidfile', mock_create_pidfile):
                                        exit_code = redirect_checker.main(mock_argv)
        mock_daemonize.assert_called_once_with()
        mock_create_pidfile.assert_called()
        mock_dictConfig.assert_called_once_with(config.LOGGING)
        mock_main_loop.assert_called_once_with(config)
        assert config.EXIT_CODE == exit_code

