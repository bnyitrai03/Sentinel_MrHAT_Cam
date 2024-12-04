import pytest
from unittest.mock import Mock, patch, MagicMock
from sentinel_mrhat_cam import Logger
import logging


class LoggerTest:
    @pytest.fixture
    def logger(self):
        mock_remote = Mock()
        mock_remote.is_connected.return_value = True
        logger = Logger()
        logger._remote = mock_remote
        return logger

    @pytest.fixture
    def record(self):
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg="Log",
            args=(),
            exc_info=None
        )
        return record

    @pytest.fixture
    def mock_yaml_config(self):
        return {
            'version': 1,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard'
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console'],
                    'level': 'INFO'
                }
            }
        }

    def test_publish_loop_empty_queue(self, logger):
        logger._publish_loop("test_topic")
        logger._remote.send.assert_not_called()

    def test_publish_loop_multiple_messages(self, logger):
        test_logs = ["Log 1", "Log 2", "Log 3"]
        for msg in test_logs:
            logger._log_queue.put(msg)
        logger._publish_loop("test_topic")
        assert logger._remote.send.call_count == len(test_logs)
        assert logger._log_queue.empty()

    def test_publish_loop_queue_get_timeout(self, logger):
        logger._log_queue.put("Log")
        with patch.object(logger._log_queue, 'get', side_effect=TimeoutError):
            logger._publish_loop("test_topic")
        logger._remote.send.assert_not_called()
        assert "Log" in list(logger._log_queue.queue)  # Queue is not iterable

    def test_publish_loop_not_connected(self, logger):
        logger._log_queue.put("Log")
        logger._remote.is_connected.return_value = False
        logger._publish_loop("test_topic")
        logger._remote.send.assert_not_called()
        assert "Log" in list(logger._log_queue.queue)

    def test_emit_no_start_event(self, logger, record):
        formatted_msg = logger.format(record)
        logger.emit(record)
        assert formatted_msg in list(logger._log_queue.queue)

    def test_emit_successful_with_start_event(self, logger, record):
        logger._start_event.set()
        logger.emit(record)
        assert logger._log_queue.empty()

    def test_emit_format_exception(self, logger):
        with pytest.raises(Exception):
            logger.emit()
        assert logger._log_queue.empty()

    def test_start_remote_logging_sets_mqtt(self, logger):
        mock_mqtt = MagicMock()
        logger.start_remote_logging(mock_mqtt)
        assert logger._remote == mock_mqtt
        assert logger._start_event.is_set() is True

    def test_stop_remote_logging(self, logger):
        logger.stop_remote_logging()
        assert logger._start_event.is_set() is False
