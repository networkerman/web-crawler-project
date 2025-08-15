#!/usr/bin/env python3
"""
Test script for the Web Crawler

This script tests the basic functionality of the WebCrawler class
with a simple test case.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from web_crawler import WebCrawler
from urllib.parse import urlparse

class TestWebCrawler(unittest.TestCase):
    """Test cases for the WebCrawler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_url = "https://example.com/docs"
        self.crawler = WebCrawler(self.test_url)
    
    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        test_cases = [
            ("https://docs.example.com/page", "https://docs.example.com"),
            ("http://example.org/path", "http://example.org"),
            ("https://sub.domain.co.uk/", "https://sub.domain.co.uk"),
        ]
        
        for url, expected_domain in test_cases:
            with self.subTest(url=url):
                domain = self.crawler._extract_domain(url)
                self.assertEqual(domain, expected_domain)
    
    def test_is_same_domain(self):
        """Test same domain checking."""
        # Same domain
        self.assertTrue(self.crawler._is_same_domain("https://example.com/page"))
        self.assertTrue(self.crawler._is_same_domain("https://example.com/another/page"))
        
        # Different domain
        self.assertFalse(self.crawler._is_same_domain("https://other.com/page"))
        self.assertFalse(self.crawler._is_same_domain("https://docs.other.com/page"))
    
    def test_is_valid_url(self):
        """Test URL validation."""
        # Valid URLs
        self.assertTrue(self.crawler._is_valid_url("https://example.com/page"))
        self.assertTrue(self.crawler._is_valid_url("http://example.com/page"))
        
        # Invalid URLs
        self.assertFalse(self.crawler._is_valid_url("mailto:user@example.com"))
        self.assertFalse(self.crawler._is_valid_url("javascript:alert('test')"))
        self.assertFalse(self.crawler._is_valid_url("tel:+1234567890"))
        self.assertFalse(self.crawler._is_valid_url("https://example.com/file.pdf"))
        self.assertFalse(self.crawler._is_valid_url("https://example.com/image.jpg"))
        self.assertFalse(self.crawler._is_valid_url(""))
        self.assertFalse(self.crawler._is_valid_url(None))
    
    def test_normalize_url(self):
        """Test URL normalization."""
        test_cases = [
            ("https://example.com/page#section", "https://example.com/page"),
            ("https://example.com/page?param=value", "https://example.com/page?param=value"),
            ("https://example.com/page", "https://example.com/page"),
        ]
        
        for input_url, expected_url in test_cases:
            with self.subTest(input_url=input_url):
                normalized = self.crawler._normalize_url(input_url)
                self.assertEqual(normalized, expected_url)
    
    @patch('web_crawler.requests.Session')
    def test_fetch_page_success(self, mock_session):
        """Test successful page fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "<html><body><a href='/page1'>Link 1</a></body></html>"
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Test fetching
        crawler = WebCrawler(self.test_url)
        content = crawler._fetch_page(self.test_url)
        
        self.assertIsNotNone(content)
        self.assertIn("<html>", content)
    
    @patch('web_crawler.requests.Session')
    def test_fetch_page_error(self, mock_session):
        """Test page fetching with error."""
        # Mock failed response
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = Exception("Connection error")
        mock_session.return_value = mock_session_instance
        
        # Test fetching
        crawler = WebCrawler(self.test_url)
        content = crawler._fetch_page(self.test_url)
        
        self.assertIsNone(content)
    
    def test_extract_links(self):
        """Test link extraction from HTML."""
        html_content = """
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="https://example.com/page2">Page 2</a>
                <a href="https://other.com/page3">External Page</a>
                <a href="mailto:user@example.com">Email</a>
                <a href="/file.pdf">PDF File</a>
            </body>
        </html>
        """
        
        links = self.crawler._extract_links(html_content, "https://example.com")
        
        # Should only include valid, same-domain links
        expected_links = [
            "https://example.com/page1",
            "https://example.com/page2"
        ]
        
        self.assertEqual(set(links), set(expected_links))

def run_tests():
    """Run the test suite."""
    print("🧪 Running Web Crawler Tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWebCrawler)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
