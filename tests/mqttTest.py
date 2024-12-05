import pytest
import logging
from unittest.mock import MagicMock, patch
from sentinel_mrhat_cam import (
    MQTT, BROKER, PORT, QOS,
    USERNAME, PASSWORD
)


class MQTTTest:
    @pytest.fixture
    def mock_mqtt(self):
        mqtt = MQTT()
        mqtt.client = MagicMock()
        return mqtt

    """ @pytest.fixture
    def mqtt(self):
        mqtt = MQTT()
        mqtt.client = MagicMock()
        def on_message(client, userdata, message):
            mqtt.client.on_message(client, userdata, message)
        mqtt.client.on_message = on_message
        return mqtt """

    def test_connect(self, mock_mqtt):
        with patch("sentinel_mrhat_cam.MQTT._is_broker_available", return_value=True):
            mock_mqtt.connect()
        mock_mqtt.client.username_pw_set.assert_called_with(USERNAME, PASSWORD)
        mock_mqtt.client.connect.assert_called_with(BROKER, PORT)
        mock_mqtt.client.loop_start.assert_called_once()

    def test_disconnect(self, mock_mqtt):
        mock_mqtt.disconnect()
        mock_mqtt.client.loop_stop.assert_called_once()
        mock_mqtt.client.disconnect.assert_called_once()

    def test_send(self, mock_mqtt):
        topic = "test/topic"
        message = "test_message"
        mock_mqtt.send(message, topic)
        mock_mqtt.client.publish.assert_called_once_with(topic, message, qos=QOS)

    def test_broker_check_success(self, mock_mqtt):
        with patch.object(mock_mqtt, "_is_broker_available", return_value=True) as mock_is_available:
            mock_mqtt._broker_check()
            mock_is_available.assert_called_once()
            assert mock_mqtt._broker_connect_counter == 0

    def test_broker_check_failure(self, mock_mqtt, caplog):
        caplog.set_level(logging.INFO)
        mock_mqtt._broker_connect_counter = 19
        with patch.object(mock_mqtt, "_is_broker_available", return_value=False):
            with pytest.raises(SystemExit):
                mock_mqtt._broker_check()
            assert "Waiting for broker to become available..." in caplog.text
            assert "Connecting to network failed 20 times, restarting script..." in caplog.text
            assert mock_mqtt._broker_connect_counter == 20

    @patch("socket.create_connection")
    def test_broker_available(self, mock_create_connection, mock_mqtt):
        mock_create_connection.return_value = MagicMock()
        assert mock_mqtt._is_broker_available() is True

    @patch("socket.create_connection")
    def test_broker_unavailable(self, mock_create_connection, mock_mqtt):
        mock_create_connection.side_effect = OSError
        assert mock_mqtt._is_broker_available() is False

    @patch("socket.create_connection")
    def test_unexpected_exception(self, mock_create_connection, mock_mqtt, caplog):
        caplog.set_level(logging.INFO)
        mock_create_connection.side_effect = Exception("Unexpected error")
        with pytest.raises(SystemExit):
            mock_mqtt._is_broker_available()
        assert "Unexpected error" in caplog.text

    """ @patch("sentinel_mrhat_cam.Config.validate_config", return_value=True)
    @patch("sentinel_mrhat_cam.shutil.copyfile")
    def test_on_message_valid_config(self, mock_copyfile, mock_validate_config, mock_mqtt):
        message = json.dumps({"key": "value"})
        mock_mqtt.client.on_message(None, None, message)
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_open.assert_called_once_with(TEMP_CONFIG_PATH, "w")
        #mock_validate_config.assert_called_once_with({"key": "value"})
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_validate_config.assert_called_once_with({"key": "value"})
            mock_open.assert_called_once_with(TEMP_CONFIG_PATH, "w")
            mock_copyfile.assert_called_once_with(TEMP_CONFIG_PATH, CONFIG_PATH)
            assert mock_mqtt.config_confirm_message == "config-ok"
            assert mock_mqtt.new_config is True """

    @patch("sentinel_mrhat_cam.MAX_WAIT_TIME_FOR_CONFG", 0.001)
    def test_wait_for_config_timeout(self, mock_mqtt):
        with patch.object(mock_mqtt.config_received_event, "wait", return_value=False):
            result = mock_mqtt.wait_for_config()
        assert not result
        assert mock_mqtt.config_confirm_message == "config-nok | Timed out waiting for config"

    @patch("sentinel_mrhat_cam.MAX_WAIT_TIME_FOR_CONFG", 0.001)
    def test_wait_for_config(self, mock_mqtt, caplog):
        caplog.set_level(logging.INFO)
        mock_mqtt.config_received_event.set()
        mock_mqtt.new_config = True
        result = mock_mqtt.wait_for_config()
        assert result
        assert "Config received" in caplog.text
