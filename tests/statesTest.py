import pytest
import time
from unittest.mock import MagicMock
from sentinel_mrhat_cam import Context, IdleState, CreateMessageState


def test_log_and_save_execution_time():
    Context.runtime = 0

    @Context.log_and_save_execution_time("Test Function")
    def test_function():
        time.sleep(0.5)

    test_function()
    assert pytest.approx(Context.runtime, 0.1) == 0.5


def test_schedule_sleep_until_next_cycle():
    app_mock = MagicMock()
    test_state = IdleState()
    waiting_time = 0.1
    period = 0.5

    test_state._schedule_next_cycle(app_mock, period, waiting_time)
    app_mock.reset_runtime.assert_called_once()
    app_mock.set_state.assert_called_once()


def test_schedule_shutdown_until_next_cycle():
    app_mock = MagicMock()
    app_mock.logger = MagicMock()
    test_state = IdleState()
    waiting_time = 10
    period = -1

    test_state._schedule_next_cycle(app_mock, period, waiting_time)
    assert period == -1

def test_no_connection_in_CreateMessageState():
    app_mock = MagicMock()
    test_state = CreateMessageState()
    app_mock.communication.is_connected.return_value = False
    
    test_state.handle(app_mock)
    app_mock.communication.connect.assert_called_once()
    app_mock.logger.start_remote_logging.assert_called_once()
