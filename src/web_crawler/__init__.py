#!/usr/bin/env python3
"""
Enterprise-Grade Web Crawler Package

A robust, scalable web crawler with dynamic content support, state persistence,
and advanced error handling for developer documentation sites.
"""

__version__ = "3.0.0"  # Major version bump for breaking changes
__author__ = "Your Team"
__license__ = "MIT"

from .crawler import WebCrawler  # Note: renamed from AsyncWebCrawler
from .config_manager import ConfigManager
from .state_manager import StateManager, CrawlState
from .dynamic_handler import DynamicContentHandler

# Convenience function for simple use cases
def crawl_website(url: str, max_urls: int = 0, max_depth: int = 0, **kwargs):
    """
    Simple synchronous function for one-off crawls.
    
    Args:
        url: Starting URL to crawl
        max_urls: Maximum URLs to crawl (0 = unlimited)
        max_depth: Maximum depth to crawl (0 = unlimited)
        **kwargs: Additional configuration options
        
    Returns:
        Set of discovered URLs
        
    Example:
        urls = crawl_website("https://docs.python.org", max_urls=100)
    """
    import asyncio
    from .config_manager import ConfigManager
    
    config = ConfigManager()
    config.set('crawler.start_url', url)
    config.set('crawler.max_urls', max_urls)
    config.set('crawler.max_depth', max_depth)
    
    # Apply any additional kwargs to config
    for key, value in kwargs.items():
        config.set(f'crawler.{key}', value)
    
    crawler = WebCrawler(config)
    return asyncio.run(crawler.crawl())

__all__ = [
    'WebCrawler',
    'ConfigManager',
    'StateManager',
    'CrawlState',
    'DynamicContentHandler',
    'crawl_website',  # Convenience function
]
