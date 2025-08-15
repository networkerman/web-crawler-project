#!/usr/bin/env python3
"""
Dynamic Content Handler for Web Crawler

Handles JavaScript-rendered content using Playwright for dynamic websites.
"""

import asyncio
from typing import Optional, List, Dict, Any
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Dynamic content handling will be disabled.")


class DynamicContentHandler:
    """Handles dynamic content rendering using Playwright."""
    
    def __init__(self, enable_playwright: bool = True, 
                 page_load_timeout: int = 10000,
                 network_idle_timeout: int = 2000,
                 user_agent: str = None):
        """
        Initialize the dynamic content handler.
        
        Args:
            enable_playwright: Whether to enable Playwright
            page_load_timeout: Page load timeout in milliseconds
            network_idle_timeout: Network idle timeout in milliseconds
            user_agent: Custom user agent string
        """
        self.enable_playwright = enable_playwright and PLAYWRIGHT_AVAILABLE
        self.page_load_timeout = page_load_timeout
        self.network_idle_timeout = network_idle_timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None
        
        if self.enable_playwright:
            logger.info("Dynamic content handler initialized with Playwright support")
        else:
            logger.info("Dynamic content handler initialized without Playwright support")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self):
        """Start the Playwright browser."""
        if not self.enable_playwright:
            return
        
        try:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-extensions'
                ]
            )
            
            self.page = await self.browser.new_page()
            
            # Set user agent
            if self.user_agent:
                await self.page.set_extra_http_headers({
                    'User-Agent': self.user_agent
                })
            
            # Set viewport
            await self.page.set_viewport_size({'width': 1920, 'height': 1080})
            
            logger.info("Playwright browser started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Playwright browser: {e}")
            self.enable_playwright = False
    
    async def stop(self):
        """Stop the Playwright browser."""
        if self.page:
            try:
                await self.page.close()
                self.page = None
            except Exception as e:
                logger.error(f"Error closing page: {e}")
        
        if self.browser:
            try:
                await self.browser.close()
                self.browser = None
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
        
        if self._playwright:
            try:
                await self._playwright.stop()
                self._playwright = None
            except Exception as e:
                logger.error(f"Error stopping Playwright: {e}")
        
        logger.info("Playwright browser stopped")
    
    def _needs_javascript_rendering(self, url: str, content_type: str, html_content: str) -> bool:
        """
        Determine if a page needs JavaScript rendering.
        
        Args:
            url: The URL being processed
            content_type: Content type header
            html_content: HTML content of the page
            
        Returns:
            True if JavaScript rendering is needed
        """
        if not self.enable_playwright:
            return False
        
        # Check content type
        if 'text/html' not in content_type.lower():
            return False
        
        # Check for common JavaScript frameworks and dynamic content indicators
        js_indicators = [
            'react', 'vue', 'angular', 'ember', 'backbone',
            'spa', 'single-page-application',
            'data-reactroot', 'ng-', 'v-', 'x-data',
            'window.__INITIAL_STATE__', 'window.__PRELOADED_STATE__',
            'id="app"', 'id="root"', 'id="main"',
            'class="app"', 'class="root"', 'class="main"'
        ]
        
        html_lower = html_content.lower()
        for indicator in js_indicators:
            if indicator in html_lower:
                logger.debug(f"JavaScript rendering needed for {url}: found indicator '{indicator}'")
                return True
        
        # Check for dynamic content patterns
        dynamic_patterns = [
            r'<script[^>]*src[^>]*>',  # External scripts
            r'<script[^>]*>.*?</script>',  # Inline scripts
            r'window\.',  # Window object usage
            r'document\.',  # Document object usage
            r'addEventListener',  # Event listeners
            r'fetch\(',  # Fetch API usage
            r'XMLHttpRequest',  # XHR usage
        ]
        
        for pattern in dynamic_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                logger.debug(f"JavaScript rendering needed for {url}: found pattern '{pattern}'")
                return True
        
        # Check for minimal content that might be dynamically loaded
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(strip=True)
        
        if len(text_content) < 100:  # Very little text content
            logger.debug(f"JavaScript rendering needed for {url}: minimal text content")
            return True
        
        return False
    
    async def render_page(self, url: str, html_content: str = None) -> Optional[str]:
        """
        Render a page using Playwright to handle JavaScript.
        
        Args:
            url: The URL to render
            html_content: Optional HTML content (for comparison)
            
        Returns:
            Rendered HTML content or None if failed
        """
        if not self.enable_playwright or not self.page:
            logger.warning("Playwright not available for rendering")
            return html_content
        
        try:
            logger.info(f"Rendering page with JavaScript: {url}")
            
            # Navigate to the page
            await self.page.goto(url, timeout=self.page_load_timeout)
            
            # Wait for network to be idle
            await self.page.wait_for_load_state('networkidle', timeout=self.network_idle_timeout)
            
            # Additional wait for dynamic content
            await asyncio.sleep(2)
            
            # Get the rendered content
            rendered_content = await self.page.content()
            
            # Check if content changed significantly
            if html_content:
                original_soup = BeautifulSoup(html_content, 'html.parser')
                rendered_soup = BeautifulSoup(rendered_content, 'html.parser')
                
                original_text = original_soup.get_text(strip=True)
                rendered_text = rendered_soup.get_text(strip=True)
                
                if len(rendered_text) > len(original_text) * 1.5:
                    logger.info(f"Content significantly enhanced by JavaScript rendering: {url}")
                    logger.debug(f"Original text length: {len(original_text)}, Rendered: {len(rendered_text)}")
                else:
                    logger.debug(f"JavaScript rendering provided minimal enhancement: {url}")
            
            logger.info(f"Successfully rendered page: {url}")
            return rendered_content
            
        except Exception as e:
            logger.error(f"Failed to render page {url}: {e}")
            return html_content
    
    async def extract_links_from_rendered(self, url: str, html_content: str) -> List[str]:
        """
        Extract links from rendered HTML content.
        
        Args:
            url: The base URL
            html_content: Rendered HTML content
            
        Returns:
            List of extracted URLs
        """
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Extract all anchor tags
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            
            # Basic URL validation
            if self._is_valid_url(absolute_url):
                links.append(absolute_url)
        
        # Extract links from JavaScript data attributes
        js_links = self._extract_js_links(soup, url)
        links.extend(js_links)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        logger.debug(f"Extracted {len(unique_links)} links from rendered page: {url}")
        return unique_links
    
    def _extract_js_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract links that might be embedded in JavaScript code.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of extracted URLs
        """
        links = []
        
        # Look for script tags with URLs
        for script in soup.find_all('script'):
            if script.string:
                script_content = script.string
                
                # Look for URL patterns in JavaScript
                url_patterns = [
                    r'["\']([^"\']*\.html?[^"\']*)["\']',  # HTML files
                    r'["\']([^"\']*\.php[^"\']*)["\']',    # PHP files
                    r'["\']([^"\']*\.aspx[^"\']*)["\']',   # ASPX files
                    r'["\']([^"\']*\.jsp[^"\']*)["\']',    # JSP files
                    r'["\']([^"\']*/[^"\']*)["\']',         # Paths with slashes
                    r'url:\s*["\']([^"\']*)["\']',          # URL properties
                    r'href:\s*["\']([^"\']*)["\']',         # Href properties
                    r'src:\s*["\']([^"\']*)["\']',          # Src properties
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, script_content, re.IGNORECASE)
                    for match in matches:
                        if match and not match.startswith('#'):
                            absolute_url = urljoin(base_url, match)
                            if self._is_valid_url(absolute_url):
                                links.append(absolute_url)
        
        # Look for data attributes that might contain URLs
        for element in soup.find_all(attrs=True):
            for attr_name, attr_value in element.attrs.items():
                if isinstance(attr_value, str) and any(keyword in attr_name.lower() for keyword in ['url', 'href', 'src', 'link']):
                    if attr_value and not attr_value.startswith('#'):
                        absolute_url = urljoin(base_url, attr_value)
                        if self._is_valid_url(absolute_url):
                            links.append(absolute_url)
        
        return links
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid and should be crawled.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid
        """
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
    
    async def take_screenshot(self, url: str, filename: str = None) -> Optional[str]:
        """
        Take a screenshot of the rendered page.
        
        Args:
            url: The URL to screenshot
            filename: Output filename (optional)
            
        Returns:
            Path to screenshot file or None if failed
        """
        if not self.enable_playwright or not self.page:
            return None
        
        try:
            if not filename:
                filename = f"screenshot_{urlparse(url).netloc}_{int(asyncio.get_event_loop().time())}.png"
            
            await self.page.screenshot(path=filename, full_page=True)
            logger.info(f"Screenshot saved: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to take screenshot of {url}: {e}")
            return None
    
    async def get_page_metrics(self, url: str) -> Dict[str, Any]:
        """
        Get performance metrics for a page.
        
        Args:
            url: The URL to analyze
            
        Returns:
            Dictionary containing page metrics
        """
        if not self.enable_playwright or not self.page:
            return {}
        
        try:
            # Navigate to the page
            await self.page.goto(url, timeout=self.page_load_timeout)
            
            # Wait for load
            await self.page.wait_for_load_state('networkidle', timeout=self.network_idle_timeout)
            
            # Get performance metrics
            metrics = await self.page.evaluate("""
                () => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    return {
                        loadTime: perfData.loadEventEnd - perfData.loadEventStart,
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
                        resourceCount: performance.getEntriesByType('resource').length
                    };
                }
            """)
            
            # Get page size
            content = await self.page.content()
            page_size = len(content.encode('utf-8'))
            
            metrics['pageSize'] = page_size
            metrics['url'] = url
            
            logger.debug(f"Page metrics for {url}: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get page metrics for {url}: {e}")
            return {}
