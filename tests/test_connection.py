from unittest import mock
from unittest.mock import Mock
import pytest
from python_freeswitch_esl.connection import ESLClient



class TestEventCallbacks:
    def test_init_single_event(self):
        mock_callable = Mock
        client = ESLClient("127.0.0.1", 8021, event_callbacks={"API": mock_callable})
        assert client.event_callbacks["API"] == [mock_callable]


    def test_init_multiple_events(self):
        mock_callable1 = Mock
        mock_callable2 = Mock
        client = ESLClient("127.0.0.1", 8021, event_callbacks={"API": [mock_callable1, mock_callable2]})
        assert client.event_callbacks["API"] == [mock_callable1, mock_callable2]


class TestCommands():

    @pytest.mark.asyncio
    @mock.patch("python_freeswitch_esl.connection.ESLClient.send_command")
    async def test_api_calls_send_command(self, mock_send_command):
        client = ESLClient("127.0.0.1", 8021)
        await client.api("status")
        mock_send_command.assert_called_once_with("api status")

class TestClient():
    
    @pytest.mark.asyncio
    @mock.patch("python_freeswitch_esl.connection.ESLClient.initialize")
    @mock.patch("python_freeswitch_esl.connection.ESLClient.loop")
    async def test_run_calls_initialize(self, mock_initialize, mock_loop):
        client = ESLClient("127.0.0.1", 8021)
        await client.run()
        mock_initialize.assert_called_once()
        mock_loop.assert_called_once()

    def test_add_event_callback_appends_callback(self):
        mock_callable = Mock
        client = ESLClient("127.0.0.1", 8021)
        assert len(client.event_callbacks["API"]) == 0
        client.add_event_callback("API", mock_callable)
        assert len(client.event_callbacks["API"]) == 1
        assert isinstance(client.event_callbacks["API"], list)
