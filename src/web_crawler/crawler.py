#!/usr/bin/env python3
"""
Web Crawler for Developer Documentation Sites

A robust, ethical web crawler designed to scrape developer documentation websites
while respecting robots.txt and implementing proper error handling.

Author: AI Assistant
License: MIT
"""

import requests
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import time
import logging
from typing import Set, List, Optional
import argparse
import sys
from collections import deque
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebCrawler:
    """
    A robust web crawler that respects robots.txt and crawls within domain boundaries.
    """
    
    def __init__(self, start_url: str, delay: float = 1.0, timeout: int = 30):
        """
        Initialize the crawler.
        
        Args:
            start_url: The starting URL to begin crawling
            delay: Delay between requests in seconds (default: 1.0)
            timeout: Request timeout in seconds (default: 30)
        """
        self.start_url = start_url
        self.base_domain = self._extract_domain(start_url)
        self.delay = delay
        self.timeout = timeout
        
        # Initialize collections
        self.visited_urls: Set[str] = set()
        self.url_queue: deque = deque([start_url])
        self.unique_urls: Set[str] = set()
        
        # Initialize robots.txt parser
        self.robots_parser = RobotFileParser()
        self._setup_robots_txt()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WebCrawler/1.0 (+https://github.com/your-repo)'
        })
        
        logger.info(f"Initialized crawler for domain: {self.base_domain}")
        logger.info(f"Starting URL: {start_url}")
    
    def _extract_domain(self, url: str) -> str:
        """Extract the base domain from a URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _setup_robots_txt(self):
        """Set up robots.txt parser for the target domain."""
        robots_url = urljoin(self.base_domain, '/robots.txt')
        try:
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
            logger.info(f"Successfully loaded robots.txt from {robots_url}")
        except Exception as e:
            logger.warning(f"Could not load robots.txt from {robots_url}: {e}")
            # Create a permissive robots parser if we can't load the file
            self.robots_parser = None
    
    def _is_allowed_by_robots(self, url: str) -> bool:
        """Check if the URL is allowed by robots.txt."""
        if self.robots_parser is None:
            return True  # If no robots.txt, assume everything is allowed
        
        try:
            return self.robots_parser.can_fetch(self.session.headers['User-Agent'], url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Default to allowing if there's an error
    
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
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico'
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
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page and return its content."""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.info(f"Skipping non-HTML content: {content_type}")
                return None
            
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def crawl(self) -> Set[str]:
        """
        Main crawling method that processes all URLs in the queue.
        
        Returns:
            Set of all unique URLs found during crawling
        """
        logger.info("Starting crawl...")
        
        while self.url_queue:
            current_url = self.url_queue.popleft()
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            # Check robots.txt
            if not self._is_allowed_by_robots(current_url):
                logger.info(f"Skipping {current_url} (not allowed by robots.txt)")
                self.visited_urls.add(current_url)
                continue
            
            # Mark as visited
            self.visited_urls.add(current_url)
            self.unique_urls.add(current_url)
            
            # Fetch the page
            html_content = self._fetch_page(current_url)
            if html_content:
                # Extract new links
                new_links = self._extract_links(html_content, current_url)
                
                # Add new links to queue
                for link in new_links:
                    if link not in self.visited_urls and link not in self.url_queue:
                        self.url_queue.append(link)
                
                logger.info(f"Found {len(new_links)} new links on {current_url}")
                logger.info(f"Queue size: {len(self.url_queue)}, Visited: {len(self.visited_urls)}")
            
            # Respect delay between requests
            if self.delay > 0:
                time.sleep(self.delay)
        
        logger.info(f"Crawl completed! Found {len(self.unique_urls)} unique URLs")
        return self.unique_urls
    
    def save_urls_to_file(self, filename: str = 'crawled_urls.txt'):
        """Save all unique URLs to a text file in alphabetical order."""
        sorted_urls = sorted(self.unique_urls)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Web Crawler Results\n")
                f.write(f"# Domain: {self.base_domain}\n")
                f.write(f"# Start URL: {self.start_url}\n")
                f.write(f"# Total URLs found: {len(sorted_urls)}\n")
                f.write(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for url in sorted_urls:
                    f.write(f"{url}\n")
            
            logger.info(f"Saved {len(sorted_urls)} URLs to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving URLs to file: {e}")


def main():
    """Main function to run the crawler."""
    parser = argparse.ArgumentParser(
        description='Web crawler for developer documentation sites'
    )
    parser.add_argument(
        'url',
        help='Starting URL to begin crawling'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Request timeout in seconds (default: 30)'
    )
    parser.add_argument(
        '--output',
        default='crawled_urls.txt',
        help='Output filename (default: crawled_urls.txt)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize and run crawler
        crawler = WebCrawler(
            start_url=args.url,
            delay=args.delay,
            timeout=args.timeout
        )
        
        # Perform the crawl
        unique_urls = crawler.crawl()
        
        # Save results
        crawler.save_urls_to_file(args.output)
        
        print(f"\n✅ Crawl completed successfully!")
        print(f"📊 Total unique URLs found: {len(unique_urls)}")
        print(f"💾 Results saved to: {args.output}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Crawl interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
