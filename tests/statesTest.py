import pytest
import time
from unittest.mock import MagicMock
from sentinel_mrhat_cam import (
    Context,
    InitState,
    CreateMessageState,
    ConfigCheckState,
    TransmitState,
    IdleState,
    SHUTDOWN_THRESHOLD
)


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


def test_negative_period_shutdown():
    app_mock = MagicMock()
    test_state = IdleState()
    waiting_time = 10
    period = -1
    test_state._schedule_next_cycle(app_mock, period, waiting_time)
    app_mock.rtc.localize_time.assert_called_once()


def test_schedule_shutdown_until_next_cycle():
    app_mock = MagicMock()
    test_state = IdleState()
    waiting_time = SHUTDOWN_THRESHOLD + 10
    period = 10
    test_state._schedule_next_cycle(app_mock, period, waiting_time)
    app_mock.logger.stop_remote_logging.assert_called_once()


def test_no_connection_in_CreateMessageState():
    app_mock = MagicMock()
    test_state = CreateMessageState()
    app_mock.communication.is_connected.return_value = False
    test_state.handle(app_mock)
    app_mock.communication.connect.assert_called_once()
    app_mock.logger.start_remote_logging.assert_called_once()


def test_init_state_camera_start():
    app_mock = MagicMock()
    test_state = InitState()
    test_state.handle(app_mock)
    app_mock.camera.start.assert_called_once()
    app_mock.set_state.assert_called_once()
    assert isinstance(app_mock.set_state.call_args[0][0], CreateMessageState)


def test_create_message_state_with_connection():
    app_mock = MagicMock()
    app_mock.communication.is_connected.return_value = True
    test_state = CreateMessageState()
    test_state.handle(app_mock)
    app_mock.message_creator.create_message.assert_called_once()
    app_mock.communication.connect.assert_not_called()
    app_mock.logger.start_remote_logging.assert_not_called()
    app_mock.set_state.assert_called_once()
    assert isinstance(app_mock.set_state.call_args[0][0], ConfigCheckState)


def test_config_check_state_no_new_config():
    app_mock = MagicMock()
    app_mock.communication.wait_for_config.return_value = False
    test_state = ConfigCheckState()
    test_state.handle(app_mock)
    app_mock.config.load.assert_not_called()
    app_mock.set_state.assert_called_once()
    assert isinstance(app_mock.set_state.call_args[0][0], TransmitState)


def test_transmit_state():
    app_mock = MagicMock()
    test_state = TransmitState()
    test_state.handle(app_mock)
    app_mock.communication.send.assert_called_once()
    app_mock.set_state.assert_called_once()
    assert isinstance(app_mock.set_state.call_args[0][0], IdleState)


def test_idle_state_zero_period():
    app_mock = MagicMock()
    app_mock.config.active = {"period": 0}
    app_mock.runtime = 1.0
    test_state = IdleState()
    test_state.handle(app_mock)
    app_mock.reset_runtime.assert_called_once()
    app_mock.set_state.assert_called_once()
    assert isinstance(app_mock.set_state.call_args[0][0], CreateMessageState)
