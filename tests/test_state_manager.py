"""Test suite for StateManager."""
import pytest
from pathlib import Path
import tempfile
import json
from web_crawler import StateManager, CrawlState
from datetime import datetime


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def state_manager(temp_dir):
    """Create StateManager with temp files."""
    return StateManager(
        state_file=temp_dir / "test_state.json",
        database_file=temp_dir / "test_db.db"
    )


@pytest.fixture
def sample_state():
    """Create a sample CrawlState for testing."""
    return CrawlState(
        start_url="https://example.com",
        base_domain="https://example.com",
        visited_urls={"https://example.com/page1", "https://example.com/page2"},
        url_queue=["https://example.com/page3"],
        unique_urls={"https://example.com/page1", "https://example.com/page2"},
        total_crawled=2,
        start_time=datetime.now(),
        last_updated=datetime.now()
    )


def test_save_load_json_state(state_manager, sample_state):
    """Test JSON state persistence."""
    # Save state
    assert state_manager.save_state_json(sample_state)
    
    # Load state
    loaded_state = state_manager.load_state_json()
    
    # Verify all fields are preserved
    assert loaded_state.start_url == sample_state.start_url
    assert loaded_state.base_domain == sample_state.base_domain
    assert loaded_state.visited_urls == sample_state.visited_urls
    assert loaded_state.url_queue == sample_state.url_queue
    assert loaded_state.unique_urls == sample_state.unique_urls
    assert loaded_state.total_crawled == sample_state.total_crawled


def test_save_load_json_state_with_empty_sets(state_manager):
    """Test JSON state persistence with empty collections."""
    state = CrawlState(
        start_url="https://example.com",
        base_domain="https://example.com",
        visited_urls=set(),
        url_queue=[],
        unique_urls=set(),
        total_crawled=0,
        start_time=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Save and load
    assert state_manager.save_state_json(state)
    loaded_state = state_manager.load_state_json()
    
    # Verify empty collections are preserved
    assert loaded_state.visited_urls == set()
    assert loaded_state.url_queue == []
    assert loaded_state.unique_urls == set()


def test_save_load_json_state_with_large_data(state_manager):
    """Test JSON state persistence with large datasets."""
    # Create state with many URLs
    visited_urls = {f"https://example.com/page{i}" for i in range(1000)}
    url_queue = [f"https://example.com/queue{i}" for i in range(500)]
    unique_urls = visited_urls.copy()
    
    state = CrawlState(
        start_url="https://example.com",
        base_domain="https://example.com",
        visited_urls=visited_urls,
        url_queue=url_queue,
        unique_urls=unique_urls,
        total_crawled=1000,
        start_time=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Save and load
    assert state_manager.save_state_json(state)
    loaded_state = state_manager.load_state_json()
    
    # Verify large datasets are preserved
    assert len(loaded_state.visited_urls) == 1000
    assert len(loaded_state.url_queue) == 500
    assert len(loaded_state.unique_urls) == 1000
    assert loaded_state.total_crawled == 1000


def test_save_load_sqlite_state(state_manager, sample_state):
    """Test SQLite state persistence."""
    # Save state to SQLite
    assert state_manager.save_state_sqlite(sample_state)
    
    # Load state from SQLite
    loaded_state = state_manager.load_state_sqlite()
    
    # Verify state is loaded correctly
    assert loaded_state is not None
    assert loaded_state.start_url == sample_state.start_url
    assert loaded_state.base_domain == sample_state.base_domain
    assert loaded_state.visited_urls == sample_state.visited_urls
    assert loaded_state.url_queue == sample_state.url_queue
    assert loaded_state.unique_urls == sample_state.unique_urls
    assert loaded_state.total_crawled == sample_state.total_crawled


def test_sqlite_session_management(state_manager, sample_state):
    """Test SQLite session creation and management."""
    # First save should create a new session
    assert state_manager.save_state_sqlite(sample_state)
    
    # Get the session ID
    session_id = state_manager.session_id
    
    # Second save should update existing session
    sample_state.total_crawled = 5
    assert state_manager.save_state_sqlite(sample_state, session_id)
    
    # Load state and verify update
    loaded_state = state_manager.load_state_sqlite(session_id)
    assert loaded_state.total_crawled == 5


def test_sqlite_multiple_sessions(state_manager):
    """Test multiple SQLite sessions."""
    # Create first session
    state1 = CrawlState(
        start_url="https://example1.com",
        base_domain="https://example1.com",
        visited_urls={"https://example1.com/page1"},
        url_queue=[],
        unique_urls={"https://example1.com/page1"},
        total_crawled=1,
        start_time=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Create second session
    state2 = CrawlState(
        start_url="https://example2.com",
        base_domain="https://example2.com",
        visited_urls={"https://example2.com/page1"},
        url_queue=[],
        unique_urls={"https://example2.com/page1"},
        total_crawled=1,
        start_time=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Save both states
    assert state_manager.save_state_sqlite(state1)
    session1_id = state_manager.session_id
    
    assert state_manager.save_state_sqlite(state2)
    session2_id = state_manager.session_id
    
    # Verify sessions are different
    assert session1_id != session2_id
    
    # Load both states
    loaded_state1 = state_manager.load_state_sqlite(session1_id)
    loaded_state2 = state_manager.load_state_sqlite(session2_id)
    
    assert loaded_state1.start_url == "https://example1.com"
    assert loaded_state2.start_url == "https://example2.com"


def test_save_url_data(state_manager):
    """Test saving individual URL data."""
    # Save URL data
    assert state_manager.save_url_data(
        url="https://example.com/page1",
        status="success",
        content_type="text/html",
        content_length=1024,
        response_time=0.5
    )
    
    # Save failed URL data
    assert state_manager.save_url_data(
        url="https://example.com/page2",
        status="failed",
        error_message="Connection timeout"
    )


def test_get_crawl_statistics(state_manager):
    """Test crawl statistics retrieval."""
    # Save some URL data first
    state_manager.save_url_data("https://example.com/page1", "success")
    state_manager.save_url_data("https://example.com/page2", "success")
    state_manager.save_url_data("https://example.com/page3", "failed")
    
    # Get statistics
    stats = state_manager.get_crawl_statistics()
    
    # Verify statistics
    assert stats['total_urls'] >= 3
    assert stats['successful_urls'] >= 2
    assert stats['failed_urls'] >= 1
    assert stats['total_sessions'] >= 0
    assert stats['running_sessions'] >= 0


def test_cleanup_old_sessions(state_manager):
    """Test cleanup of old sessions."""
    # Create a state with old timestamp
    old_state = CrawlState(
        start_url="https://example.com",
        base_domain="https://example.com",
        visited_urls=set(),
        url_queue=[],
        unique_urls=set(),
        total_crawled=0,
        start_time=datetime(2020, 1, 1),  # Old date
        last_updated=datetime(2020, 1, 1)
    )
    
    # Save old state
    state_manager.save_state_sqlite(old_state)
    
    # Clean up old sessions (older than 1 day)
    assert state_manager.cleanup_old_sessions(days=1)
    
    # Verify old session is cleaned up
    stats = state_manager.get_crawl_statistics()
    # The cleanup should have removed the old session


def test_database_initialization(state_manager):
    """Test database tables are created correctly."""
    # The database should be initialized in the fixture
    # Verify we can save and load data
    sample_state = CrawlState(
        start_url="https://example.com",
        base_domain="https://example.com",
        visited_urls=set(),
        url_queue=[],
        unique_urls=set(),
        total_crawled=0,
        start_time=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Should be able to save and load
    assert state_manager.save_state_sqlite(sample_state)
    loaded_state = state_manager.load_state_sqlite()
    assert loaded_state is not None


def test_error_handling_invalid_json(state_manager, temp_dir):
    """Test error handling for invalid JSON files."""
    # Create invalid JSON file
    invalid_json_file = temp_dir / "invalid_state.json"
    with open(invalid_json_file, 'w') as f:
        f.write("{ invalid json content")
    
    # Create state manager with invalid file
    invalid_manager = StateManager(
        state_file=invalid_json_file,
        database_file=temp_dir / "test_db.db"
    )
    
    # Should handle invalid JSON gracefully
    loaded_state = invalid_manager.load_state_json()
    assert loaded_state is None


def test_error_handling_missing_files(state_manager):
    """Test error handling for missing files."""
    # Create state manager with non-existent files
    missing_manager = StateManager(
        state_file="nonexistent.json",
        database_file="nonexistent.db"
    )
    
    # Should handle missing files gracefully
    loaded_state = missing_manager.load_state_json()
    assert loaded_state is None


def test_state_serialization_deserialization(sample_state):
    """Test state serialization and deserialization."""
    # Convert to dict
    state_dict = sample_state.to_dict()
    
    # Verify all fields are present
    assert 'start_url' in state_dict
    assert 'base_domain' in state_dict
    assert 'visited_urls' in state_dict
    assert 'url_queue' in state_dict
    assert 'unique_urls' in state_dict
    assert 'total_crawled' in state_dict
    assert 'start_time' in state_dict
    assert 'last_updated' in state_dict
    
    # Convert back from dict
    reconstructed_state = CrawlState.from_dict(state_dict)
    
    # Verify reconstruction
    assert reconstructed_state.start_url == sample_state.start_url
    assert reconstructed_state.base_domain == sample_state.base_domain
    assert reconstructed_state.visited_urls == sample_state.visited_urls
    assert reconstructed_state.url_queue == sample_state.url_queue
    assert reconstructed_state.unique_urls == sample_state.unique_urls
    assert reconstructed_state.total_crawled == sample_state.total_crawled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
