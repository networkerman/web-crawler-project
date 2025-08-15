#!/usr/bin/env python3
"""
State Manager for Web Crawler

Handles persistence and resumability of crawl state using both JSON and SQLite storage.
"""

import json
import sqlite3
import asyncio
from pathlib import Path
from typing import Set, Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class CrawlState:
    """Represents the current state of a crawl operation."""
    start_url: str
    base_domain: str
    visited_urls: Set[str]
    url_queue: List[str]
    unique_urls: Set[str]
    total_crawled: int
    start_time: datetime
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            'start_url': self.start_url,
            'base_domain': self.base_domain,
            'visited_urls': list(self.visited_urls),
            'url_queue': list(self.url_queue),
            'unique_urls': list(self.unique_urls),
            'total_crawled': self.total_crawled,
            'start_time': self.start_time.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrawlState':
        """Create state from dictionary."""
        return cls(
            start_url=data['start_url'],
            base_domain=data['base_domain'],
            visited_urls=set(data['visited_urls']),
            url_queue=data['url_queue'],
            unique_urls=set(data['unique_urls']),
            total_crawled=data['total_crawled'],
            start_time=datetime.fromisoformat(data['start_time']),
            last_updated=datetime.fromisoformat(data['last_updated'])
        )


class StateManager:
    """Manages crawl state persistence and resumability."""
    
    def __init__(self, state_file: str = "crawl_state.json", 
                 database_file: str = "crawl_data.db"):
        """
        Initialize the state manager.
        
        Args:
            state_file: Path to JSON state file
            database_file: Path to SQLite database file
        """
        self.state_file = Path(state_file)
        self.database_file = Path(database_file)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()
                
                # Create URLs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS urls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT UNIQUE NOT NULL,
                        status TEXT NOT NULL,
                        crawled_at TIMESTAMP,
                        content_type TEXT,
                        content_length INTEGER,
                        response_time REAL,
                        error_message TEXT
                    )
                """)
                
                # Create crawl_sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crawl_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        start_url TEXT NOT NULL,
                        base_domain TEXT NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        total_urls INTEGER DEFAULT 0,
                        successful_urls INTEGER DEFAULT 0,
                        failed_urls INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'running'
                    )
                """)
                
                # Create crawl_state table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crawl_state (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        visited_urls TEXT,
                        url_queue TEXT,
                        unique_urls TEXT,
                        total_crawled INTEGER DEFAULT 0,
                        last_updated TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES crawl_sessions (id)
                    )
                """)
                
                conn.commit()
                logger.info(f"Database initialized: {self.database_file}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def save_state_json(self, state: CrawlState) -> bool:
        """
        Save crawl state to JSON file.
        
        Args:
            state: The crawl state to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            state_dict = state.to_dict()
            state_dict['last_updated'] = datetime.now().isoformat()
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"State saved to JSON: {self.state_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save state to JSON: {e}")
            return False
    
    def load_state_json(self) -> Optional[CrawlState]:
        """
        Load crawl state from JSON file.
        
        Returns:
            CrawlState object if successful, None otherwise
        """
        try:
            if not self.state_file.exists():
                logger.info(f"No state file found: {self.state_file}")
                return None
            
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = CrawlState.from_dict(data)
            logger.info(f"State loaded from JSON: {self.state_file}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to load state from JSON: {e}")
            return None
    
    def save_state_sqlite(self, state: CrawlState, session_id: Optional[int] = None) -> bool:
        """
        Save crawl state to SQLite database.
        
        Args:
            state: The crawl state to save
            session_id: Optional session ID to link state to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()
                
                # If no session_id, create a new session
                if session_id is None:
                    cursor.execute("""
                        INSERT INTO crawl_sessions (start_url, base_domain, start_time, status)
                        VALUES (?, ?, ?, ?)
                    """, (state.start_url, state.base_domain, state.start_time, 'running'))
                    session_id = cursor.lastrowid
                
                # Save or update crawl state
                cursor.execute("""
                    INSERT OR REPLACE INTO crawl_state 
                    (session_id, visited_urls, url_queue, unique_urls, total_crawled, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    json.dumps(list(state.visited_urls)),
                    json.dumps(state.url_queue),
                    json.dumps(list(state.unique_urls)),
                    state.total_crawled,
                    datetime.now()
                ))
                
                conn.commit()
                logger.info(f"State saved to SQLite database, session_id: {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save state to SQLite: {e}")
            return False
    
    def load_state_sqlite(self, session_id: Optional[int] = None) -> Optional[CrawlState]:
        """
        Load crawl state from SQLite database.
        
        Args:
            session_id: Session ID to load state for (None for latest)
            
        Returns:
            CrawlState object if successful, None otherwise
        """
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()
                
                # If no session_id, get the latest running session
                if session_id is None:
                    cursor.execute("""
                        SELECT id FROM crawl_sessions 
                        WHERE status = 'running' 
                        ORDER BY start_time DESC 
                        LIMIT 1
                    """)
                    result = cursor.fetchone()
                    if not result:
                        logger.info("No running crawl session found")
                        return None
                    session_id = result[0]
                
                # Load crawl state
                cursor.execute("""
                    SELECT cs.start_url, cs.base_domain, cs.start_time,
                           cst.visited_urls, cst.url_queue, cst.unique_urls, 
                           cst.total_crawled, cst.last_updated
                    FROM crawl_sessions cs
                    JOIN crawl_state cst ON cs.id = cst.session_id
                    WHERE cs.id = ?
                """, (session_id,))
                
                result = cursor.fetchone()
                if not result:
                    logger.info(f"No state found for session_id: {session_id}")
                    return None
                
                state = CrawlState(
                    start_url=result[0],
                    base_domain=result[1],
                    start_time=datetime.fromisoformat(result[2]),
                    visited_urls=set(json.loads(result[3])),
                    url_queue=json.loads(result[4]),
                    unique_urls=set(json.loads(result[5])),
                    total_crawled=result[6],
                    last_updated=datetime.fromisoformat(result[7])
                )
                
                logger.info(f"State loaded from SQLite database, session_id: {session_id}")
                return state
                
        except Exception as e:
            logger.error(f"Failed to load state from SQLite: {e}")
            return None
    
    def save_url_data(self, url: str, status: str, **kwargs) -> bool:
        """
        Save individual URL data to database.
        
        Args:
            url: The URL that was crawled
            status: Status of the crawl (success, failed, etc.)
            **kwargs: Additional data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO urls 
                    (url, status, crawled_at, content_type, content_length, 
                     response_time, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    url,
                    status,
                    datetime.now(),
                    kwargs.get('content_type'),
                    kwargs.get('content_length'),
                    kwargs.get('response_time'),
                    kwargs.get('error_message')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to save URL data: {e}")
            return False
    
    def get_crawl_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about all crawl sessions.
        
        Returns:
            Dictionary containing crawl statistics
        """
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()
                
                # Get total URLs
                cursor.execute("SELECT COUNT(*) FROM urls")
                total_urls = cursor.fetchone()[0]
                
                # Get successful URLs
                cursor.execute("SELECT COUNT(*) FROM urls WHERE status = 'success'")
                successful_urls = cursor.fetchone()[0]
                
                # Get failed URLs
                cursor.execute("SELECT COUNT(*) FROM urls WHERE status = 'failed'")
                failed_urls = cursor.fetchone()[0]
                
                # Get total sessions
                cursor.execute("SELECT COUNT(*) FROM crawl_sessions")
                total_sessions = cursor.fetchone()[0]
                
                # Get running sessions
                cursor.execute("SELECT COUNT(*) FROM crawl_sessions WHERE status = 'running'")
                running_sessions = cursor.fetchone()[0]
                
                return {
                    'total_urls': total_urls,
                    'successful_urls': successful_urls,
                    'failed_urls': failed_urls,
                    'total_sessions': total_sessions,
                    'running_sessions': running_sessions
                }
                
        except Exception as e:
            logger.error(f"Failed to get crawl statistics: {e}")
            return {}
    
    def cleanup_old_sessions(self, days: int = 30) -> bool:
        """
        Clean up old crawl sessions and related data.
        
        Args:
            days: Number of days to keep data for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
                
                # Delete old sessions
                cursor.execute("""
                    DELETE FROM crawl_sessions 
                    WHERE start_time < ?
                """, (cutoff_date,))
                
                # Delete old URL data
                cursor.execute("""
                    DELETE FROM urls 
                    WHERE crawled_at < ?
                """, (cutoff_date,))
                
                conn.commit()
                logger.info(f"Cleaned up data older than {days} days")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return False
