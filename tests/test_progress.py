import pytest
from unittest.mock import MagicMock
from flask import Flask
from services.task.progress import Progress

PROGRESS_TTL = 60 * 60 * 24


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    mock_client = MagicMock()
    mock_client.hset = MagicMock()
    mock_client.hget = MagicMock()
    mock_client.hincrbyfloat = MagicMock()
    mock_client.hdel = MagicMock()
    mock_client.delete = MagicMock()
    mock_client.expire = MagicMock()
    return mock_client


@pytest.fixture
def flask_app(mock_redis_client):
    """Create Flask app with mocked Redis client"""
    app = Flask(__name__)
    app.redis_client_tasks = mock_redis_client
    return app


@pytest.fixture
def app_context(flask_app):
    """Create Flask application context"""
    with flask_app.app_context():
        yield flask_app


class TestProgress:
    def test_init_sets_max_value(self, app_context, mock_redis_client):
        """Test that __init__ sets max_value in Redis"""
        progress = Progress("test_task", max_value=200)
        
        mock_redis_client.hset.assert_called_once_with("task:test_task", "max_value", 200)
        mock_redis_client.expire.assert_called_once_with("task:test_task", PROGRESS_TTL)
        assert progress.task_id == "test_task"
        assert progress.max_value == 200

    def test_init_default_max_value(self, app_context, mock_redis_client):
        """Test that __init__ uses default max_value=100"""
        progress = Progress("test_task")
        
        mock_redis_client.hset.assert_called_once_with("task:test_task", "max_value", 100)
        assert progress.max_value == 100

    def test_add_increments_progress(self, app_context, mock_redis_client):
        """Test that add() increments progress value"""
        progress = Progress("test_task", max_value=100)
        progress.add(25.5)
        
        mock_redis_client.hincrbyfloat.assert_called_once_with("task:test_task", "progress", 25.5)
        mock_redis_client.expire.assert_called_with("task:test_task", PROGRESS_TTL)

    def test_setValue_sets_progress(self, app_context, mock_redis_client):
        """Test that setValue() sets progress value"""
        progress = Progress("test_task", max_value=100)
        progress.setValue(50)
        
        mock_redis_client.hset.assert_any_call("task:test_task", "progress", 50)
        mock_redis_client.expire.assert_called_with("task:test_task", PROGRESS_TTL)

    def test_getValue_returns_progress(self, app_context, mock_redis_client):
        """Test that getValue() returns progress value"""
        mock_redis_client.hget.return_value = "75.5"
        progress = Progress("test_task", max_value=100)
        
        result = progress.getValue()
        
        assert result == 75.5
        mock_redis_client.hget.assert_called_once_with("task:test_task", "progress")

    def test_getValue_returns_zero_when_no_progress(self, app_context, mock_redis_client):
        """Test that getValue() returns 0.0 when no progress exists"""
        mock_redis_client.hget.return_value = None
        progress = Progress("test_task", max_value=100)
        
        result = progress.getValue()
        
        assert result == 0.0

    def test_getValue_handles_bytes(self, app_context, mock_redis_client):
        """Test that getValue() handles bytes response"""
        mock_redis_client.hget.return_value = b"42.3"
        progress = Progress("test_task", max_value=100)
        
        result = progress.getValue()
        
        assert result == 42.3

    def test_getProgress_calculates_percentage(self, app_context, mock_redis_client):
        """Test that getProgress() calculates percentage correctly"""
        mock_redis_client.hget.side_effect = ["50", "100"]
        progress = Progress("test_task", max_value=100)
        
        result = progress.getProgress()
        
        assert result == 50.0
        assert mock_redis_client.hget.call_count == 2

    def test_getProgress_returns_zero_when_no_data(self, app_context, mock_redis_client):
        """Test that getProgress() returns 0.0 when no data exists"""
        mock_redis_client.hget.return_value = None
        progress = Progress("test_task", max_value=100)
        
        result = progress.getProgress()
        
        assert result == 0.0

    def test_getProgress_respects_decimals(self, app_context, mock_redis_client):
        """Test that getProgress() respects decimals parameter"""
        mock_redis_client.hget.side_effect = ["33.333333", "100"]
        progress = Progress("test_task", max_value=100)
        
        result = progress.getProgress(decimals=1)
        
        assert result == 33.3

    def test_getProgress_limits_to_100(self, app_context, mock_redis_client):
        """Test that getProgress() never returns more than 100"""
        mock_redis_client.hget.side_effect = ["150", "100"]
        progress = Progress("test_task", max_value=100)
        
        result = progress.getProgress()
        
        assert result == 100.0

    def test_getProgress_handles_bytes(self, app_context, mock_redis_client):
        """Test that getProgress() handles bytes response"""
        mock_redis_client.hget.side_effect = [b"25", b"100"]
        progress = Progress("test_task", max_value=100)
        
        result = progress.getProgress()
        
        assert result == 25.0

    def test_clear_deletes_progress(self, app_context, mock_redis_client):
        """Test that clear() deletes progress from Redis"""
        progress = Progress("test_task", max_value=100)
        progress.clear()
        
        mock_redis_client.hdel.assert_called_once_with("task:test_task", "progress")

    def test_drop_deletes_task(self, app_context, mock_redis_client):
        """Test that drop() deletes entire task from Redis"""
        progress = Progress("test_task", max_value=100)
        progress.drop()
        
        mock_redis_client.delete.assert_called_once_with("task:test_task")
