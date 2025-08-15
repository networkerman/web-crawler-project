#!/usr/bin/env python3
"""
Enterprise-Grade Async Web Crawler Package

A robust, scalable web crawler with dynamic content support, state persistence,
and advanced error handling for developer documentation sites.
"""

__version__ = "2.0.0"
__author__ = "AI Assistant"
__license__ = "MIT"

# Core classes
from .async_crawler import AsyncWebCrawler
from .config_manager import ConfigManager
from .state_manager import StateManager, CrawlState
from .dynamic_handler import DynamicContentHandler

# Legacy support (deprecated)
from .crawler import WebCrawler

__all__ = [
    'AsyncWebCrawler',
    'ConfigManager', 
    'StateManager',
    'CrawlState',
    'DynamicContentHandler',
    'WebCrawler',  # Legacy
]
