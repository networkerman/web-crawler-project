# Enterprise-Grade Web Crawler

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/your-username/web-crawler)

## ⚡ Performance First

This crawler is built with async/await from the ground up for maximum performance:
- **100% Asynchronous**: Built on httpx and asyncio
- **Concurrent Processing**: Configure up to 100+ concurrent workers
- **Smart Rendering**: Playwright integration for JavaScript-heavy sites
- **State Persistence**: Resume interrupted crawls without losing progress

## 🚀 Quick Start

### Simple One-Liner
```python
from web_crawler import crawl_website

# Crawl a website with a single function call
urls = crawl_website("https://docs.python.org", max_urls=100)
```

### Advanced Usage
```python
import asyncio
from web_crawler import WebCrawler, ConfigManager

async def main():
    config = ConfigManager()
    config.set('crawler.start_url', 'https://docs.python.org')
    config.set('crawler.max_concurrent', 20)
    config.set('dynamic_content.enable_playwright', True)
    
    crawler = WebCrawler(config)
    urls = await crawler.crawl()
    await crawler.save_urls_to_file('results.txt')
    
    print(f"Found {len(urls)} URLs")

asyncio.run(main())
```

## 🔄 Migration from v2.x

Version 3.0 removes the legacy synchronous crawler. If you're upgrading:

```python
# Old (v2.x) - No longer supported
from web_crawler import WebCrawler  # This was sync
crawler = WebCrawler(url)
urls = crawler.crawl()

# New (v3.x) - Use async or convenience function
from web_crawler import crawl_website
urls = crawl_website(url)  # Simple sync wrapper

# Or use async directly for more control
import asyncio
from web_crawler import WebCrawler, ConfigManager

async def crawl():
    config = ConfigManager()
    config.set('crawler.start_url', url)
    crawler = WebCrawler(config)
    return await crawler.crawl()

urls = asyncio.run(crawl())
```

## 🚀 Features

### Core Capabilities
- **Asynchronous Architecture**: Built with `asyncio` and `httpx` for high-performance concurrent crawling
- **Dynamic Content Support**: Integrates Playwright for JavaScript-rendered content
- **State Persistence**: Save and resume crawl sessions with JSON and SQLite storage
- **Robust Error Handling**: Configurable retry mechanisms with exponential backoff
- **Rate Limiting**: Built-in rate limiting and request throttling
- **Robots.txt Compliance**: Respects robots.txt files for ethical crawling

### Enterprise Features
- **Configuration Management**: YAML-based configuration with CLI overrides
- **Progress Tracking**: Real-time progress bars with detailed statistics
- **Comprehensive Logging**: Structured logging with multiple output formats
- **Database Storage**: SQLite backend for crawl data and statistics
- **Resumability**: Interrupt and resume crawls without losing progress
- **Performance Metrics**: Detailed timing and performance analytics

### Advanced Capabilities
- **Intelligent JavaScript Detection**: Automatically determines when rendering is needed
- **Depth and URL Limits**: Configurable crawling boundaries
- **Concurrent Processing**: Multi-worker architecture for scalability
- **Content Type Filtering**: Smart filtering of non-HTML content
- **URL Normalization**: Consistent URL handling and deduplication

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Basic Installation
```bash
# Clone the repository
git clone https://github.com/your-username/web-crawler.git
cd web-crawler

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for dynamic content support)
playwright install
```

### Development Installation
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

## 🛠️ Usage

### Command Line Usage
```bash
# Basic crawl
python -m web_crawler.cli crawl "https://docs.python.org/3/"

# With custom configuration
python -m web_crawler.cli crawl "https://docs.python.org/3/" \
    --max-urls 100 \
    --max-depth 3 \
    --max-concurrent 10 \
    --enable-playwright

# Show configuration
python -m web_crawler.cli config

# View statistics
python -m web_crawler.cli stats

# Clean up old data
python -m web_crawler.cli cleanup --days 30
```

## ⚙️ Configuration

### Configuration File (config.yaml)
```yaml
crawler:
  start_url: "https://docs.example.com"
  delay: 1.0
  timeout: 30
  max_concurrent: 10
  max_urls: 0
  max_depth: 0

retry:
  max_retries: 3
  base_delay: 1.0
  max_delay: 60.0

dynamic_content:
  enable_playwright: true
  page_load_timeout: 10000
  network_idle_timeout: 2000

output:
  filename: "crawled_urls.txt"
  save_state: true
  state_file: "crawl_state.json"
  database_file: "crawl_data.db"

logging:
  level: "INFO"
  log_file: "crawler.log"
  console_logging: true
  file_logging: true
```

### CLI Configuration Overrides
All configuration options can be overridden via command line arguments:
```bash
python -m web_crawler.cli crawl "https://example.com" \
    --delay 0.5 \
    --max-concurrent 20 \
    --max-urls 1000 \
    --enable-playwright \
    --max-retries 5
```

## 🔧 Advanced Usage

### Dynamic Content Handling
```python
from web_crawler import DynamicContentHandler

async def handle_dynamic_content():
    async with DynamicContentHandler(
        enable_playwright=True,
        page_load_timeout=10000
    ) as handler:
        # Render JavaScript-heavy page
        content = await handler.render_page("https://spa.example.com")
        
        # Extract links from rendered content
        links = await handler.extract_links_from_rendered("https://spa.example.com", content)
        
        # Take screenshot
        screenshot = await handler.take_screenshot("https://spa.example.com")
        
        # Get performance metrics
        metrics = await handler.get_page_metrics("https://spa.example.com")
```

### State Management
```python
from web_crawler import StateManager

# Initialize state manager
state_manager = StateManager(
    state_file="crawl_state.json",
    database_file="crawl_data.db"
)

# Save state
state_manager.save_state_json(crawl_state)

# Load state
crawl_state = state_manager.load_state_json()

# Get statistics
stats = state_manager.get_crawl_statistics()
```

### Custom Configuration
```python
from web_crawler import ConfigManager

# Create configuration
config = ConfigManager()

# Set values using dot notation
config.set('crawler.max_concurrent', 20)
config.set('retry.max_retries', 5)
config.set('dynamic_content.enable_playwright', True)

# Get values
max_concurrent = config.get('crawler.max_concurrent')
max_retries = config.get('retry.max_retries')

# Validate configuration
if config.validate_config():
    print("Configuration is valid")
```

## 📊 Performance and Monitoring

### Progress Tracking
The crawler provides real-time progress updates:
- URLs crawled vs. total discovered
- Current crawl depth
- Queue size
- Processing rate
- Estimated completion time

### Statistics and Metrics
Comprehensive statistics are available:
- Total URLs discovered and crawled
- Success/failure rates
- Response times
- Content types and sizes
- Crawl duration and efficiency

### Database Analytics
SQLite backend provides:
- Historical crawl data
- Performance trends
- Error analysis
- Session management

## 🚨 Error Handling

### Retry Mechanisms
- **Exponential Backoff**: Intelligent retry delays
- **Configurable Limits**: Set maximum retry attempts
- **Error Classification**: Different handling for different error types
- **Graceful Degradation**: Continue crawling despite individual failures

### Error Types Handled
- Network connection errors
- HTTP status errors (4xx, 5xx)
- Timeout errors
- Content parsing errors
- JavaScript rendering errors

## 🔒 Security and Ethics

### Robots.txt Compliance
- Automatic robots.txt parsing
- Respect for crawl-delay directives
- User-agent identification
- Configurable compliance levels

### Rate Limiting
- Configurable requests per second
- Burst handling
- Domain-specific limits
- Automatic throttling

### Ethical Considerations
- Respect for server resources
- Configurable delays between requests
- User-agent identification
- Compliance with website terms of service

## 🧪 Testing and Development

### Running Examples
```bash
# Run comprehensive examples
python examples/enterprise_usage.py

# Test dynamic content handling
python -m web_crawler.cli test "https://example.com" --screenshot --metrics
```

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/
```

## 📈 Scaling Considerations

### Performance Optimization
- **Concurrent Workers**: Configurable worker pool size
- **Connection Pooling**: Efficient HTTP client reuse
- **Memory Management**: Streaming content processing
- **Async I/O**: Non-blocking operations throughout

### Resource Management
- **Browser Instances**: Efficient Playwright browser management
- **Database Connections**: Connection pooling for SQLite
- **File I/O**: Asynchronous file operations
- **Memory Usage**: Configurable limits and cleanup

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [httpx](https://www.python-httpx.org/) for async HTTP operations
- [Playwright](https://playwright.dev/) for dynamic content rendering
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [Click](https://click.palletsprojects.com/) for CLI framework
- [tqdm](https://tqdm.github.io/) for progress bars

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/web-crawler/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/web-crawler/discussions)
- **Documentation**: [Wiki](https://github.com/your-username/web-crawler/wiki)

## 🔄 Migration from v1.0

If you're upgrading from version 1.0, see our [Migration Guide](MIGRATION.md) for details on the new async API and configuration system.

---

**Note**: This crawler is designed for ethical web scraping. Please respect robots.txt files, implement appropriate delays, and comply with website terms of service.
