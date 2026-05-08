from unittest.mock import MagicMock, patch

from src.telemetry import TinybirdTracker


def test_track_disabled():
    tracker = TinybirdTracker()
    tracker._enabled = False
    tracker._executor = MagicMock()

    result = tracker.track(
        endpoint="/test", original_tokens=100, compressed_tokens=50, savings_percentage=50.0
    )

    assert result is False
    tracker._executor.submit.assert_not_called()


@patch("src.telemetry.time.time")
def test_track_queues_event(mock_time):
    # Fix the time so we can assert the timestamp reliably
    mock_time.return_value = 1600000000.0

    tracker = TinybirdTracker()
    tracker._enabled = True
    tracker._executor = MagicMock()

    result = tracker.track(
        endpoint="/api/compress",
        original_tokens=1000,
        compressed_tokens=400,
        savings_percentage=60.0,
        latency_ms=120.5,
        extra={
            "doc_type": "OBD_REPORT",
            "priority": "P1",
            "pii_data": "secret_vin_number",
            "unsafe_key": "hidden",
        },
    )

    assert result is True

    # Assert _executor.submit was called once
    tracker._executor.submit.assert_called_once()

    # Check the arguments passed to submit: should be (tracker._send, payload)
    args, kwargs = tracker._executor.submit.call_args
    assert args[0] == tracker._send

    payload = args[1]

    # Verify standard fields
    assert payload["endpoint"] == "/api/compress"
    assert payload["original_tokens"] == 1000
    assert payload["compressed_tokens"] == 400
    assert payload["savings_percentage"] == 60.0
    assert payload["latency_ms"] == 120.5
    assert payload["timestamp"] == 1600000000000

    # Verify extra fields were sanitized
    assert payload["doc_type"] == "OBD_REPORT"
    assert payload["priority"] == "P1"
    assert "pii_data" not in payload
    assert "unsafe_key" not in payload


@patch("src.telemetry.requests.post")
def test_send_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    tracker = TinybirdTracker()
    payload = {"test": "data"}

    tracker._send(payload)

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://eu.tinybird.co/v0/events"
    assert kwargs["params"]["name"] == "comptext_metrics"
    assert "token" in kwargs["params"]
    assert kwargs["data"] == '{"test": "data"}'
    assert kwargs["headers"] == {"Content-Type": "application/json"}
    assert kwargs["timeout"] == 2.0


@patch("src.telemetry.requests.post")
@patch("src.telemetry.log")
def test_send_warning_on_error_status(mock_log, mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    tracker = TinybirdTracker()
    tracker._send({"test": "data"})

    mock_log.warning.assert_called_once_with("Tinybird non-2xx", extra={"status": 500})


@patch("src.telemetry.requests.post")
@patch("src.telemetry.log")
def test_send_catches_exception(mock_log, mock_post):
    mock_post.side_effect = Exception("Network error")

    tracker = TinybirdTracker()
    tracker._send({"test": "data"})

    mock_log.debug.assert_called_once_with("Tinybird send failed (non-critical)")
