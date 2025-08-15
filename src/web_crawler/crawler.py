#!/usr/bin/env python3
"""
Asynchronous Web Crawler for Developer Documentation Sites

An enterprise-grade, asynchronous web crawler with dynamic content support,
state persistence, retry mechanisms, and advanced error handling.
"""

import asyncio
import httpx
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import time
import logging
from typing import Set, List, Optional, Dict, Any
from collections import deque
import re
from datetime import datetime
import structlog

from .state_manager import StateManager, CrawlState
from .config_manager import ConfigManager
from .dynamic_handler import DynamicContentHandler

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class WebCrawler:
    """
    Enterprise-grade web crawler for developer documentation sites.
    
    This is the primary crawler implementation using async/await for
    high-performance concurrent crawling.
    """
    
    def __init__(self, config: ConfigManager, state_manager: StateManager = None):
        """
        Initialize the web crawler.
        
        Args:
            config: Configuration manager instance
            state_manager: State manager instance (optional)
        """
        self.config = config
        self.crawler_config = config.get_crawler_config()
        self.output_config = config.get_output_config()
        self.logging_config = config.get_logging_config()
        
        # Initialize state manager
        self.state_manager = state_manager or StateManager(
            state_file=self.output_config['state_file'],
            database_file=self.output_config['database_file']
        )
        
        # Crawler state
        self.start_url = self.crawler_config['start_url']
        self.base_domain = self._extract_domain(self.start_url)
        self.delay = self.crawler_config['delay']
        self.timeout = self.crawler_config['timeout']
        self.max_concurrent = self.crawler_config['max_concurrent']
        self.max_urls = self.crawler_config['max_urls']
        self.max_depth = self.crawler_config['max_depth']
        
        # Retry configuration
        self.max_retries = self.crawler_config['max_retries']
        self.base_delay = self.crawler_config['base_delay']
        self.max_delay = self.crawler_config['max_delay']
        
        # Initialize collections
        self.visited_urls: Set[str] = set()
        self.url_queue: asyncio.Queue = asyncio.Queue()
        self.unique_urls: Set[str] = set()
        self.url_depths: Dict[str, int] = {}
        self.total_crawled = 0
        
        # Initialize robots.txt parser
        self.robots_parser = RobotFileParser()
        self._setup_robots_txt()
        
        # HTTP client
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Dynamic content handler
        self.dynamic_handler = DynamicContentHandler(
            enable_playwright=self.crawler_config['enable_playwright'],
            page_load_timeout=self.crawler_config['page_load_timeout'],
            network_idle_timeout=self.crawler_config['network_idle_timeout'],
            user_agent=self.crawler_config['user_agent']
        )
        
        # Rate limiting
        self.rate_limiter = asyncio.Semaphore(self.max_concurrent)
        
        # Crawl session
        self.start_time = datetime.now()
        self.session_id: Optional[int] = None
        
        logger.info("WebCrawler initialized", 
                   domain=self.base_domain, 
                   start_url=self.start_url,
                   max_concurrent=self.max_concurrent)
    
    def _extract_domain(self, url: str) -> str:
        """Extract the base domain from a URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _setup_robots_txt(self):
        """Set up robots.txt parser for the target domain."""
        if not self.crawler_config['respect_robots']:
            logger.info("Robots.txt checking disabled")
            self.robots_parser = None
            return
        
        robots_url = urljoin(self.base_domain, '/robots.txt')
        try:
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
            logger.info("Robots.txt loaded", robots_url=robots_url)
        except Exception as e:
            logger.warning("Could not load robots.txt", robots_url=robots_url, error=str(e))
            self.robots_parser = None
    
    async def _is_allowed_by_robots(self, url: str) -> bool:
        """Check if the URL is allowed by robots.txt."""
        if self.robots_parser is None:
            return True
        
        try:
            user_agent = self.crawler_config['robots_user_agent']
            return self.robots_parser.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning("Error checking robots.txt", url=url, error=str(e))
            return True
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if the URL belongs to the same domain."""
        parsed = urlparse(url)
        return parsed.netloc == urlparse(self.base_domain).netloc
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and query parameters if needed."""
        parsed = urlparse(url)
        # Remove fragments (anchor links)
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        return clean_url
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if the URL is valid and should be crawled."""
        if not url:
            return False
        
        # Skip non-HTTP/HTTPS URLs
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Skip common non-content file types
        skip_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.tar', '.gz', '.mp3', '.mp4', '.avi',
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.css', '.js'
        }
        
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip URLs with certain patterns
        skip_patterns = [
            r'#.*$',  # Anchor links
            r'mailto:',  # Email links
            r'tel:',  # Phone links
            r'javascript:',  # JavaScript links
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True
    
    async def _fetch_page_with_retry(self, url: str, depth: int = 0) -> Optional[httpx.Response]:
        """
        Fetch a web page with retry mechanism and exponential backoff.
        
        Args:
            url: URL to fetch
            depth: Current crawl depth
            
        Returns:
            HTTP response or None if failed
        """
        if not self.http_client:
            return None
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                async with self.rate_limiter:
                    response = await self.http_client.get(
                        url,
                        timeout=self.timeout,
                        follow_redirects=True
                    )
                
                response_time = time.time() - start_time
                
                # Log successful request
                logger.info("Page fetched successfully",
                           url=url,
                           status_code=response.status_code,
                           response_time=response_time,
                           attempt=attempt + 1)
                
                # Save URL data to database
                self.state_manager.save_url_data(
                    url=url,
                    status='success',
                    content_type=response.headers.get('content-type'),
                    content_length=len(response.content),
                    response_time=response_time
                )
                
                return response
                
            except httpx.ConnectError as e:
                logger.warning("Connection error", url=url, attempt=attempt + 1, error=str(e))
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retries exceeded for connection error", url=url, error=str(e))
                    self.state_manager.save_url_data(url=url, status='failed', error_message=str(e))
                    
            except httpx.HTTPStatusError as e:
                logger.warning("HTTP status error", url=url, status_code=e.response.status_code, attempt=attempt + 1)
                if attempt < self.max_retries and e.response.status_code >= 500:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
                else:
                    logger.error("HTTP status error", url=url, status_code=e.response.status_code, error=str(e))
                    self.state_manager.save_url_data(url=url, status='failed', error_message=str(e))
                    return None
                    
            except httpx.TimeoutException as e:
                logger.warning("Timeout error", url=url, attempt=attempt + 1, error=str(e))
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retries exceeded for timeout", url=url, error=str(e))
                    self.state_manager.save_url_data(url=url, status='failed', error_message=str(e))
                    
            except Exception as e:
                logger.error("Unexpected error fetching page", url=url, error=str(e))
                self.state_manager.save_url_data(url=url, status='failed', error_message=str(e))
                return None
        
        return None
    
    def _extract_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract all links from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            if self._is_valid_url(absolute_url) and self._is_same_domain(absolute_url):
                normalized_url = self._normalize_url(absolute_url)
                links.append(normalized_url)
        
        return links
    
    async def _process_page(self, url: str, depth: int = 0) -> List[str]:
        """
        Process a single page and extract links.
        
        Args:
            url: URL to process
            depth: Current crawl depth
            
        Returns:
            List of new URLs found
        """
        # Fetch the page
        response = await self._fetch_page_with_retry(url, depth)
        if not response:
            return []
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            logger.debug("Skipping non-HTML content", url=url, content_type=content_type)
            return []
        
        html_content = response.text
        
        # Check if JavaScript rendering is needed
        if self.dynamic_handler.enable_playwright:
            needs_rendering = self.dynamic_handler._needs_javascript_rendering(
                url, content_type, html_content
            )
            
            if needs_rendering:
                logger.info("Rendering page with JavaScript", url=url)
                rendered_content = await self.dynamic_handler.render_page(url, html_content)
                if rendered_content:
                    html_content = rendered_content
                    # Extract links from rendered content
                    new_links = await self.dynamic_handler.extract_links_from_rendered(url, html_content)
                else:
                    # Fall back to regular link extraction
                    new_links = self._extract_links(html_content, url)
            else:
                # Regular link extraction
                new_links = self._extract_links(html_content, url)
        else:
            # Regular link extraction
            new_links = self._extract_links(html_content, url)
        
        # Filter and validate links
        valid_links = []
        for link in new_links:
            if (link not in self.visited_urls and 
                link not in [item[0] for item in self.url_queue._queue] and
                self._is_valid_url(link)):
                
                # Check depth limit
                if self.max_depth > 0 and depth >= self.max_depth:
                    logger.debug("Skipping link due to depth limit", url=link, depth=depth, max_depth=self.max_depth)
                    continue
                
                valid_links.append(link)
        
        logger.info("Links extracted", url=url, total_links=len(new_links), valid_links=len(valid_links))
        return valid_links
    
    async def _crawl_worker(self, worker_id: int):
        """
        Worker coroutine for processing URLs from the queue.
        
        Args:
            worker_id: Unique identifier for the worker
        """
        logger.info("Worker started", worker_id=worker_id)
        
        while True:
            try:
                # Get URL from queue
                queue_item = await self.url_queue.get()
                if queue_item is None:  # Sentinel value to stop worker
                    break
                
                url, depth = queue_item
                
                # Check if already visited
                if url in self.visited_urls:
                    self.url_queue.task_done()
                    continue
                
                # Check robots.txt
                if not await self._is_allowed_by_robots(url):
                    logger.info("URL not allowed by robots.txt", url=url)
                    self.visited_urls.add(url)
                    self.url_queue.task_done()
                    continue
                
                # Mark as visited
                self.visited_urls.add(url)
                self.unique_urls.add(url)
                self.url_depths[url] = depth
                self.total_crawled += 1
                
                # Process the page
                new_links = await self._process_page(url, depth)
                
                # Add new links to queue
                for link in new_links:
                    await self.url_queue.put((link, depth + 1))
                
                # Check if we've reached the URL limit
                if self.max_urls > 0 and self.total_crawled >= self.max_urls:
                    logger.info("Reached maximum URL limit", max_urls=self.max_urls)
                    break
                
                # Respect delay between requests
                if self.delay > 0:
                    await asyncio.sleep(self.delay)
                
                # Mark task as done
                self.url_queue.task_done()
                
                logger.debug("Worker processed URL", 
                           worker_id=worker_id, 
                           url=url, 
                           depth=depth, 
                           new_links=len(new_links),
                           total_crawled=self.total_crawled)
                
            except Exception as e:
                logger.error("Worker error", worker_id=worker_id, error=str(e))
                self.url_queue.task_done()
        
        logger.info("Worker stopped", worker_id=worker_id)
    
    async def _save_state(self):
        """Save current crawl state."""
        if not self.output_config['save_state']:
            return
        
        try:
            state = CrawlState(
                start_url=self.start_url,
                base_domain=self.base_domain,
                visited_urls=self.visited_urls,
                url_queue=[item[0] for item in self.url_queue._queue],
                unique_urls=self.unique_urls,
                total_crawled=self.total_crawled,
                start_time=self.start_time,
                last_updated=datetime.now()
            )
            
            # Save to both JSON and SQLite
            self.state_manager.save_state_json(state)
            self.state_manager.save_state_sqlite(state, self.session_id)
            
            logger.debug("Crawl state saved", 
                        visited_urls=len(self.visited_urls),
                        queue_size=self.url_queue.qsize(),
                        total_crawled=self.total_crawled)
            
        except Exception as e:
            logger.error("Failed to save crawl state", error=str(e))
    
    async def _load_state(self) -> bool:
        """Load previous crawl state if available."""
        try:
            # Try to load from SQLite first, then JSON
            state = self.state_manager.load_state_sqlite()
            if not state:
                state = self.state_manager.load_state_json()
            
            if state:
                self.visited_urls = state.visited_urls
                self.unique_urls = state.unique_urls
                self.total_crawled = state.total_crawled
                self.start_time = state.start_time
                
                # Rebuild queue
                for url in state.url_queue:
                    if url not in self.visited_urls:
                        depth = self.url_depths.get(url, 0)
                        await self.url_queue.put((url, depth))
                
                logger.info("Crawl state loaded", 
                           visited_urls=len(self.visited_urls),
                           queue_size=self.url_queue.qsize(),
                           total_crawled=self.total_crawled)
                return True
            
        except Exception as e:
            logger.error("Failed to load crawl state", error=str(e))
        
        return False
    
    async def crawl(self) -> Set[str]:
        """
        Main crawling method that processes all URLs in the queue.
        
        Returns:
            Set of all unique URLs found during crawling
        """
        logger.info("Starting crawl", 
                   start_url=self.start_url,
                   max_concurrent=self.max_concurrent,
                   max_urls=self.max_urls,
                   max_depth=self.max_depth)
        
        # Initialize HTTP client
        async with httpx.AsyncClient(
            headers={'User-Agent': self.crawler_config['user_agent']},
            follow_redirects=True
        ) as client:
            self.http_client = client
            
            # Initialize dynamic content handler
            async with self.dynamic_handler:
                
                # Load previous state if available
                await self._load_state()
                
                # Add start URL to queue if not already processed
                if self.start_url not in self.visited_urls:
                    await self.url_queue.put((self.start_url, 0))
                
                # Create workers
                workers = []
                for i in range(self.max_concurrent):
                    worker = asyncio.create_task(self._crawl_worker(i))
                    workers.append(worker)
                
                # Wait for all URLs to be processed
                await self.url_queue.join()
                
                # Stop workers
                for _ in workers:
                    await self.url_queue.put(None)
                
                # Wait for workers to finish
                await asyncio.gather(*workers, return_exceptions=True)
                
                # Save final state
                await self._save_state()
        
        logger.info("Crawl completed", 
                   total_urls=len(self.unique_urls),
                   total_crawled=self.total_crawled)
        
        return self.unique_urls
    
    async def save_urls_to_file(self, filename: str = None):
        """Save all unique URLs to a text file."""
        if not filename:
            filename = self.output_config['filename']
        
        sorted_urls = sorted(self.unique_urls)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Async Web Crawler Results\n")
                f.write(f"# Domain: {self.base_domain}\n")
                f.write(f"# Start URL: {self.start_url}\n")
                f.write(f"# Total URLs found: {len(sorted_urls)}\n")
                f.write(f"# Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Crawl duration: {datetime.now() - self.start_time}\n\n")
                
                for url in sorted_urls:
                    depth = self.url_depths.get(url, 0)
                    f.write(f"{url} (depth: {depth})\n")
            
            logger.info("URLs saved to file", filename=filename, count=len(sorted_urls))
            
        except Exception as e:
            logger.error("Failed to save URLs to file", filename=filename, error=str(e))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get crawling statistics."""
        return {
            'start_url': self.start_url,
            'base_domain': self.base_domain,
            'total_urls': len(self.unique_urls),
            'total_crawled': self.total_crawled,
            'queue_size': self.url_queue.qsize(),
            'start_time': self.start_time.isoformat(),
            'duration': str(datetime.now() - self.start_time),
            'max_depth': max(self.url_depths.values()) if self.url_depths else 0,
            'average_depth': sum(self.url_depths.values()) / len(self.url_depths) if self.url_depths else 0
        }
