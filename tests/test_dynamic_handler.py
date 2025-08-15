"""Test suite for DynamicContentHandler."""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from web_crawler import DynamicContentHandler


@pytest.mark.asyncio
async def test_javascript_detection():
    """Test detection of JavaScript-heavy content."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    # Test React app detection
    html_react = '<div id="root"></div><script src="bundle.js"></script>'
    assert handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_react
    )
    
    # Test Vue app detection
    html_vue = '<div id="app"></div><script>new Vue({el: "#app"})</script>'
    assert handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_vue
    )
    
    # Test Angular app detection
    html_angular = '<div ng-app="myApp"></div><script src="angular.js"></script>'
    assert handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_angular
    )
    
    # Test static HTML
    html_static = '<html><body><h1>Static Content</h1><p>Lots of text content here that provides substantial information about the topic being discussed in detail with multiple paragraphs and sections.</p></body></html>'
    assert not handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_static
    )


@pytest.mark.asyncio
async def test_javascript_pattern_detection():
    """Test detection of JavaScript patterns."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    # Test window object usage
    html_window = '<script>window.location.href = "/new-page";</script>'
    assert handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_window
    )
    
    # Test document object usage
    html_document = '<script>document.getElementById("content").innerHTML = "Dynamic";</script>'
    assert handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_document
    )
    
    # Test event listeners
    html_events = '<script>addEventListener("load", function() {});</script>'
    assert handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_events
    )
    
    # Test fetch API usage
    html_fetch = '<script>fetch("/api/data").then(r => r.json());</script>'
    assert handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_fetch
    )


@pytest.mark.asyncio
async def test_content_type_filtering():
    """Test that non-HTML content is filtered out."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    # Non-HTML content should not need rendering
    assert not handler._needs_javascript_rendering(
        "https://example.com", "application/json", '{"data": "test"}'
    )
    
    assert not handler._needs_javascript_rendering(
        "https://example.com", "text/plain", "Plain text content"
    )
    
    assert not handler._needs_javascript_rendering(
        "https://example.com", "text/xml", "<xml><data>test</data></xml>"
    )


@pytest.mark.asyncio
async def test_minimal_content_detection():
    """Test detection of minimal content that might be dynamically loaded."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    # Very little text content
    html_minimal = '<html><body><div id="app"></div></body></html>'
    assert handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_minimal
    )
    
    # More substantial content
    html_substantial = '<html><body><h1>Title</h1><p>This is a substantial amount of text content that provides meaningful information about the subject matter being discussed in detail with multiple sentences and paragraphs.</p><p>Additional content here to ensure the page has enough text to be considered complete without JavaScript rendering.</p></body></html>'
    assert not handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_substantial
    )


@pytest.mark.asyncio
async def test_playwright_disabled():
    """Test behavior when Playwright is disabled."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    # Should not need rendering when Playwright is disabled
    html_js = '<div id="root"></div><script>ReactDOM.render(<App />, document.getElementById("root"));</script>'
    assert not handler._needs_javascript_rendering(
        "https://example.com", "text/html", html_js
    )


@pytest.mark.asyncio
async def test_playwright_context_manager():
    """Test Playwright context manager functionality."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    # Test context manager without Playwright
    async with handler:
        assert handler.browser is None
        assert handler.page is None
    
    # Test context manager with Playwright (mocked)
    with patch('web_crawler.dynamic_handler.PLAYWRIGHT_AVAILABLE', True):
        with patch('web_crawler.dynamic_handler.async_playwright') as mock_playwright:
            mock_playwright_instance = Mock()
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            
            mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_browser.new_page.return_value = mock_page
            
            handler = DynamicContentHandler(enable_playwright=True)
            
            async with handler:
                assert handler.browser is not None
                assert handler.page is not None


@pytest.mark.asyncio
async def test_link_extraction_from_rendered():
    """Test link extraction from rendered content."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    html_content = '''
    <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
            <a href="https://other.com/page3">External</a>
            <a href="#section">Anchor</a>
            <div data-url="/page4">Dynamic Page 4</div>
        </body>
    </html>
    '''
    
    links = await handler.extract_links_from_rendered("https://example.com", html_content)
    
    # Should extract valid URLs
    assert 'https://example.com/page1' in links
    assert 'https://example.com/page2' in links
    assert 'https://other.com/page3' not in links  # External domain
    assert '#section' not in links  # Anchor links


@pytest.mark.asyncio
async def test_javascript_link_extraction():
    """Test extraction of links embedded in JavaScript."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    html_content = '''
    <html>
        <body>
            <script>
                var urls = [
                    "/page1.html",
                    "/page2.php",
                    "/api/data",
                    "/docs/guide"
                ];
                var config = {
                    url: "/config",
                    href: "/settings",
                    src: "/image.jpg"
                };
            </script>
            <div data-url="/dynamic-page">Dynamic</div>
        </body>
    </html>
    '''
    
    links = await handler.extract_links_from_rendered("https://example.com", html_content)
    
    # Should extract URLs from JavaScript
    assert 'https://example.com/page1.html' in links
    assert 'https://example.com/page2.php' in links
    assert 'https://example.com/api/data' in links
    assert 'https://example.com/docs/guide' in links
    assert 'https://example.com/config' in links
    assert 'https://example.com/settings' in links


@pytest.mark.asyncio
async def test_data_attribute_extraction():
    """Test extraction of links from data attributes."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    html_content = '''
    <html>
        <body>
            <div data-url="/page1" data-href="/page2" data-link="/page3">
                Content
            </div>
            <span data-src="/image.jpg" data-href="/page4">
                More content
            </span>
        </body>
    </html>
    '''
    
    links = await handler.extract_links_from_rendered("https://example.com", html_content)
    
    # Should extract URLs from data attributes
    assert 'https://example.com/page1' in links
    assert 'https://example.com/page2' in links
    assert 'https://example.com/page3' in links
    assert 'https://example.com/page4' in links


@pytest.mark.asyncio
async def test_url_validation():
    """Test URL validation in link extraction."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    # Test valid URLs
    assert handler._is_valid_url('https://example.com/page')
    assert handler._is_valid_url('http://example.com/page')
    
    # Test invalid URLs
    assert not handler._is_valid_url('mailto:user@example.com')
    assert not handler._is_valid_url('tel:+1234567890')
    assert not handler._is_valid_url('javascript:void(0)')
    assert not handler._is_valid_url('https://example.com/file.pdf')
    assert not handler._is_valid_url('https://example.com/image.jpg')
    assert not handler._is_valid_url('https://example.com/style.css')
    assert not handler._is_valid_url('https://example.com/script.js')


@pytest.mark.asyncio
async def test_duplicate_link_removal():
    """Test that duplicate links are removed."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    html_content = '''
    <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="/page1">Page 1 Duplicate</a>
            <a href="/page2">Page 2</a>
            <div data-url="/page1">Page 1 in data attribute</div>
        </body>
    </html>
    '''
    
    links = await handler.extract_links_from_rendered("https://example.com", html_content)
    
    # Should remove duplicates while preserving order
    assert len(links) == 2
    assert 'https://example.com/page1' in links
    assert 'https://example.com/page2' in links


@pytest.mark.asyncio
async def test_relative_url_resolution():
    """Test that relative URLs are resolved correctly."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    html_content = '''
    <html>
        <body>
            <a href="page1">Relative Page 1</a>
            <a href="./page2">Current Directory Page 2</a>
            <a href="../page3">Parent Directory Page 3</a>
            <a href="/absolute/page4">Absolute Page 4</a>
        </body>
    </html>
    '''
    
    links = await handler.extract_links_from_rendered("https://example.com/subdir/", html_content)
    
    # Should resolve relative URLs correctly
    assert 'https://example.com/subdir/page1' in links
    assert 'https://example.com/subdir/page2' in links
    assert 'https://example.com/page3' in links  # Parent directory
    assert 'https://example.com/absolute/page4' in links  # Absolute


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in link extraction."""
    handler = DynamicContentHandler(enable_playwright=False)
    
    # Test with None content
    links = await handler.extract_links_from_rendered("https://example.com", None)
    assert links == []
    
    # Test with empty content
    links = await handler.extract_links_from_rendered("https://example.com", "")
    assert links == []
    
    # Test with malformed HTML
    malformed_html = '<html><body><a href="/page1">Unclosed tag<body>'
    links = await handler.extract_links_from_rendered("https://example.com", malformed_html)
    # Should handle malformed HTML gracefully
    assert isinstance(links, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
