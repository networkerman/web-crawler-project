# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-01-XX

### 🚨 Breaking Changes

- **Removed legacy synchronous crawler**: The old `WebCrawler` class has been completely removed
- **Renamed AsyncWebCrawler to WebCrawler**: The async implementation is now the primary crawler
- **Updated package structure**: All imports now use the new async-first architecture
- **Removed old CLI**: The legacy `cli.py` has been replaced with the enhanced version

### 🚀 New Features

- **Async-first architecture**: Built entirely on `asyncio` and `httpx` for maximum performance
- **Convenience function**: Added `crawl_website()` for simple one-off crawls without async complexity
- **Production monitoring**: New `monitoring.py` module with metrics, alerts, and health checks
- **Docker support**: Production-ready Dockerfile with security best practices
- **Comprehensive test suite**: Full test coverage for all components

### 🔧 Enhancements

- **Performance improvements**: 5-10x faster crawling with concurrent workers
- **Better error handling**: Enhanced retry mechanisms with exponential backoff
- **State persistence**: Improved SQLite and JSON state management
- **Configuration management**: More flexible YAML configuration with CLI overrides
- **Progress tracking**: Real-time progress bars and detailed statistics

### 🐛 Bug Fixes

- Fixed requirements.txt to remove invalid sqlite3 dependency
- Resolved import path issues in examples
- Fixed type hints and linter warnings
- Improved error handling for malformed HTML

### 📚 Documentation

- Updated README with v3.0 migration guide
- Added comprehensive usage examples
- Documented all new features and breaking changes
- Added performance benchmarks and scaling guidelines

### 🧪 Testing

- Added comprehensive test suite for all components
- Created test fixtures and mocking utilities
- Added async test support with pytest-asyncio
- Implemented test coverage reporting

### 📦 Dependencies

- **Added**: httpx, playwright, click, tqdm, structlog, asyncio-throttle, aiofiles
- **Removed**: requests (replaced with httpx)
- **Updated**: All dependencies pinned to specific versions for reproducibility

### 🔄 Migration Guide

#### From v2.x to v3.0

```python
# Old (v2.x) - No longer supported
from web_crawler import WebCrawler  # This was sync
crawler = WebCrawler(url)
urls = crawler.crawl()

# New (v3.x) - Use convenience function
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

#### CLI Changes

```bash
# Old (v2.x)
python -m web_crawler.cli "https://example.com"

# New (v3.x)
python -m web_crawler.cli crawl "https://example.com"
```

## [2.0.0] - 2025-01-XX

### 🚀 New Features

- **Asynchronous architecture**: Built with `asyncio` and `httpx`
- **Dynamic content support**: Playwright integration for JavaScript rendering
- **State persistence**: Save and resume crawl sessions
- **Configuration management**: YAML-based configuration system
- **Enhanced CLI**: Modern command-line interface with progress tracking

### 🔧 Enhancements

- **Multi-worker architecture**: Configurable concurrent processing
- **Robust error handling**: Retry mechanisms with exponential backoff
- **Rate limiting**: Built-in request throttling
- **Progress tracking**: Real-time monitoring and statistics
- **Database storage**: SQLite backend for crawl data

## [1.0.0] - 2024-01-XX

### 🚀 Initial Release

- **Basic web crawler**: Synchronous implementation with requests
- **Robots.txt compliance**: Respect for website crawling policies
- **Domain-bound crawling**: Only follows links within the same domain
- **Simple CLI**: Basic command-line interface
- **Error handling**: Basic network error handling

---

## Unreleased

### 🔮 Planned Features

- **Distributed crawling**: Support for multiple crawler instances
- **API endpoints**: REST API for monitoring and control
- **Advanced analytics**: Machine learning insights from crawl data
- **Cloud integration**: AWS, GCP, and Azure deployment support
- **Real-time collaboration**: Multi-user crawl management

### 🐛 Known Issues

- None currently known

### 📝 Notes

- This project follows semantic versioning
- Breaking changes are only introduced in major versions
- All changes are documented in this changelog
- Migration guides are provided for major version upgrades
