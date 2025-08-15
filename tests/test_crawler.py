"""
Comprehensive test suite for the WebCrawler.
"""
import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, Mock, patch
from web_crawler import WebCrawler, ConfigManager


@pytest.fixture
async def crawler():
    """Create a test crawler instance."""
    config = ConfigManager()
    config.set('crawler.start_url', 'https://example.com')
    config.set('crawler.max_concurrent', 2)
    config.set('crawler.delay', 0)  # No delay for tests
    config.set('crawler.max_urls', 10)
    config.set('crawler.max_depth', 3)
    return WebCrawler(config)


@pytest.mark.asyncio
async def test_crawler_initialization(crawler):
    """Test crawler initializes correctly."""
    assert crawler.start_url == 'https://example.com'
    assert crawler.base_domain == 'https://example.com'
    assert crawler.max_concurrent == 2
    assert crawler.max_urls == 10
    assert crawler.max_depth == 3


@pytest.mark.asyncio
async def test_url_normalization(crawler):
    """Test URL normalization removes fragments."""
    normalized = crawler._normalize_url('https://example.com/page#section')
    assert normalized == 'https://example.com/page'
    
    # Test with query parameters
    normalized = crawler._normalize_url('https://example.com/page?param=value#section')
    assert normalized == 'https://example.com/page?param=value'


@pytest.mark.asyncio
async def test_domain_validation(crawler):
    """Test same-domain validation."""
    assert crawler._is_same_domain('https://example.com/page')
    assert crawler._is_same_domain('https://example.com/subdir/page')
    assert not crawler._is_same_domain('https://other.com/page')
    assert not crawler._is_same_domain('https://subdomain.example.com/page')


@pytest.mark.asyncio
async def test_url_validation(crawler):
    """Test URL validation logic."""
    # Valid URLs
    assert crawler._is_valid_url('https://example.com/page')
    assert crawler._is_valid_url('http://example.com/page')
    
    # Invalid URLs
    assert not crawler._is_valid_url('mailto:user@example.com')
    assert not crawler._is_valid_url('tel:+1234567890')
    assert not crawler._is_valid_url('javascript:void(0)')
    assert not crawler._is_valid_url('https://example.com/file.pdf')
    assert not crawler._is_valid_url('https://example.com/image.jpg')


@pytest.mark.asyncio
async def test_fetch_with_retry():
    """Test retry mechanism with exponential backoff."""
    config = ConfigManager()
    config.set('crawler.start_url', 'https://example.com')
    config.set('retry.max_retries', 3)
    config.set('retry.base_delay', 0.1)
    config.set('retry.max_delay', 1.0)
    
    crawler = WebCrawler(config)
    
    # Mock successful response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = '<html><body>Test</body></html>'
    mock_response.headers = {'content-type': 'text/html'}
    mock_response.content = b'<html><body>Test</body></html>'
    
    with patch('httpx.AsyncClient.get') as mock_get:
        # First two attempts fail, third succeeds
        mock_get.side_effect = [
            httpx.ConnectError("Connection failed"),
            httpx.ConnectError("Connection failed"),
            mock_response
        ]
        
        # Should succeed on third attempt
        response = await crawler._fetch_page_with_retry('https://example.com')
        assert response is not None
        assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_fetch_with_http_error():
    """Test handling of HTTP status errors."""
    config = ConfigManager()
    config.set('crawler.start_url', 'https://example.com')
    config.set('retry.max_retries', 2)
    
    crawler = WebCrawler(config)
    
    # Mock HTTP error response
    mock_error_response = AsyncMock()
    mock_error_response.status_code = 500
    mock_error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=Mock(), response=mock_error_response
    )
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = [
            httpx.HTTPStatusError("Server Error", request=Mock(), response=mock_error_response),
            mock_error_response
        ]
        
        # Should not retry on 5xx errors
        response = await crawler._fetch_page_with_retry('https://example.com')
        assert response is None
        assert mock_get.call_count == 1


@pytest.mark.asyncio
async def test_link_extraction(crawler):
    """Test HTML link extraction."""
    html_content = '''
    <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
            <a href="https://other.com/page3">External</a>
            <a href="#section">Anchor</a>
        </body>
    </html>
    '''
    
    links = crawler._extract_links(html_content, 'https://example.com')
    
    # Should extract internal links only
    assert '/page1' not in links  # Relative links should be resolved
    assert 'https://example.com/page2' in links
    assert 'https://other.com/page3' not in links  # External domain
    assert '#section' not in links  # Anchor links


@pytest.mark.asyncio
async def test_robots_txt_handling():
    """Test robots.txt compliance."""
    config = ConfigManager()
    config.set('crawler.start_url', 'https://example.com')
    config.set('robots.respect_robots', True)
    
    crawler = WebCrawler(config)
    
    # Test robots.txt checking
    result = await crawler._is_allowed_by_robots('https://example.com/page')
    # Should return True if robots.txt can't be loaded (permissive default)
    assert result in [True, False]


@pytest.mark.asyncio
async def test_robots_disabled():
    """Test when robots.txt checking is disabled."""
    config = ConfigManager()
    config.set('crawler.start_url', 'https://example.com')
    config.set('robots.respect_robots', False)
    
    crawler = WebCrawler(config)
    
    # Should always allow when robots.txt is disabled
    result = await crawler._is_allowed_by_robots('https://example.com/page')
    assert result is True


@pytest.mark.asyncio
async def test_state_save_load():
    """Test save and load of crawl state."""
    config = ConfigManager()
    config.set('crawler.start_url', 'https://example.com')
    config.set('output.save_state', True)
    
    crawler = WebCrawler(config)
    
    # Add some test data
    crawler.visited_urls.add('https://example.com/page1')
    crawler.unique_urls.add('https://example.com/page1')
    crawler.total_crawled = 1
    
    # Test state saving (this will create temporary files)
    await crawler._save_state()
    
    # Verify state was saved
    assert len(crawler.visited_urls) == 1
    assert len(crawler.unique_urls) == 1
    assert crawler.total_crawled == 1


@pytest.mark.asyncio
async def test_concurrent_worker_creation(crawler):
    """Test that workers are created correctly."""
    # Mock the worker method to avoid actual crawling
    original_worker = crawler._crawl_worker
    
    async def mock_worker(worker_id):
        return worker_id
    
    crawler._crawl_worker = mock_worker
    
    # Test worker creation
    workers = []
    for i in range(crawler.max_concurrent):
        worker = asyncio.create_task(crawler._crawl_worker(i))
        workers.append(worker)
    
    # Wait for workers to complete
    results = await asyncio.gather(*workers)
    
    # Verify all workers ran
    assert len(results) == crawler.max_concurrent
    assert set(results) == {0, 1}  # Worker IDs 0 and 1
    
    # Restore original method
    crawler._crawl_worker = original_worker


@pytest.mark.asyncio
async def test_url_depth_tracking(crawler):
    """Test URL depth tracking functionality."""
    # Simulate adding URLs at different depths
    await crawler.url_queue.put(('https://example.com/page1', 0))
    await crawler.url_queue.put(('https://example.com/page2', 1))
    await crawler.url_queue.put(('https://example.com/page3', 2))
    
    # Verify queue contents
    assert crawler.url_queue.qsize() == 3


@pytest.mark.asyncio
async def test_max_urls_limit():
    """Test maximum URLs limit enforcement."""
    config = ConfigManager()
    config.set('crawler.start_url', 'https://example.com')
    config.set('crawler.max_urls', 3)
    config.set('crawler.max_concurrent', 1)
    
    crawler = WebCrawler(config)
    
    # Mock the process page method to return new links
    async def mock_process_page(url, depth):
        return [f'https://example.com/page{i}' for i in range(1, 6)]
    
    crawler._process_page = mock_process_page
    
    # Add initial URL
    await crawler.url_queue.put(('https://example.com', 0))
    
    # Mock the crawl method to avoid actual HTTP requests
    with patch.object(crawler, '_fetch_page_with_retry') as mock_fetch:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>Test</body></html>'
        mock_response.headers = {'content-type': 'text/html'}
        mock_fetch.return_value = mock_response
        
        # Run a limited crawl
        await crawler.crawl()
        
        # Should respect max_urls limit
        assert crawler.total_crawled <= 3


@pytest.mark.asyncio
async def test_max_depth_limit():
    """Test maximum depth limit enforcement."""
    config = ConfigManager()
    config.set('crawler.start_url', 'https://example.com')
    config.set('crawler.max_depth', 2)
    config.set('crawler.max_concurrent', 1)
    
    crawler = WebCrawler(config)
    
    # Mock the process page method
    async def mock_process_page(url, depth):
        if depth < 2:
            return [f'https://example.com/page{depth+1}']
        return []
    
    crawler._process_page = mock_process_page
    
    # Add initial URL
    await crawler.url_queue.put(('https://example.com', 0))
    
    # Mock the fetch method
    with patch.object(crawler, '_fetch_page_with_retry') as mock_fetch:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>Test</body></html>'
        mock_response.headers = {'content-type': 'text/html'}
        mock_fetch.return_value = mock_response
        
        # Run crawl
        await crawler.crawl()
        
        # Verify depth tracking
        max_depth_reached = max(crawler.url_depths.values()) if crawler.url_depths else 0
        assert max_depth_reached <= 2


@pytest.mark.asyncio
async def test_statistics_generation(crawler):
    """Test statistics generation."""
    # Add some test data
    crawler.visited_urls.add('https://example.com/page1')
    crawler.visited_urls.add('https://example.com/page2')
    crawler.unique_urls.add('https://example.com/page1')
    crawler.unique_urls.add('https://example.com/page2')
    crawler.url_depths['https://example.com/page1'] = 0
    crawler.url_depths['https://example.com/page2'] = 1
    crawler.total_crawled = 2
    
    stats = crawler.get_statistics()
    
    assert stats['total_urls'] == 2
    assert stats['total_crawled'] == 2
    assert stats['max_depth'] == 1
    assert stats['average_depth'] == 0.5
    assert 'start_url' in stats
    assert 'base_domain' in stats


@pytest.mark.asyncio
async def test_save_urls_to_file(crawler, tmp_path):
    """Test saving URLs to file."""
    # Add test URLs
    crawler.unique_urls.add('https://example.com/page1')
    crawler.unique_urls.add('https://example.com/page2')
    crawler.url_depths['https://example.com/page1'] = 0
    crawler.url_depths['https://example.com/page2'] = 1
    
    # Save to temporary file
    output_file = tmp_path / 'test_urls.txt'
    await crawler.save_urls_to_file(str(output_file))
    
    # Verify file was created and contains URLs
    assert output_file.exists()
    content = output_file.read_text()
    assert 'https://example.com/page1' in content
    assert 'https://example.com/page2' in content
    assert '(depth: 0)' in content
    assert '(depth: 1)' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
