# Web Crawler for Developer Documentation Sites

A robust, ethical web crawler designed to scrape developer documentation websites while respecting robots.txt and implementing proper error handling. This tool is perfect for building RAG (Retrieval-Augmented Generation) systems by collecting comprehensive documentation URLs.

## 🚀 Features

- 🕷️ **Domain-Bound Crawling**: Only follows links within the same domain
- 🤖 **Robots.txt Compliance**: Respects website crawling policies
- 🚫 **Smart URL Filtering**: Skips non-content files and invalid URLs
- ⏱️ **Rate Limiting**: Configurable delays between requests
- 📊 **Progress Tracking**: Real-time logging and progress indicators
- 🛡️ **Error Handling**: Robust error handling for network issues
- 💾 **Output Management**: Saves results to organized text files

## 📁 Project Structure

```
web-crawler-project/
├── src/
│   └── web_crawler/
│       ├── __init__.py      # Package initialization
│       ├── crawler.py       # Core WebCrawler class
│       └── cli.py          # Command-line interface
├── tests/
│   ├── __init__.py
│   └── test_crawler.py     # Unit tests
├── examples/
│   └── basic_usage.py      # Usage examples
├── docs/                   # Documentation
├── pyproject.toml          # Project configuration
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Development dependencies
└── README.md               # This file
```

## 🛠️ Installation

### Option 1: Install from source
```bash
# Clone the repository
git clone <your-repo-url>
cd web-crawler-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Option 2: Install development dependencies
```bash
pip install -r requirements-dev.txt
```

## 🚀 Usage

### Command Line Interface

```bash
# Basic usage
python -m web_crawler.cli "https://developers.facebook.com/docs/whatsapp/cloud-api"

# With custom settings
python -m web_crawler.cli "https://docs.webengage.com/" --delay 2.0 --timeout 60

# Custom output file
python -m web_crawler.cli "https://docs.example.com/" --output my_urls.txt

# Verbose logging
python -m web_crawler.cli "https://docs.example.com/" --verbose
```

### Programmatic Usage

```python
from web_crawler import WebCrawler

# Initialize crawler
crawler = WebCrawler(
    start_url="https://docs.example.com/",
    delay=1.5,
    timeout=45
)

# Perform crawl
unique_urls = crawler.crawl()

# Save results
crawler.save_urls_to_file("output.txt")
```

### Examples

Run the included examples:
```bash
# Basic usage example
python examples/basic_usage.py

# Run tests
python -m pytest tests/
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_crawler.py -v
```

## 🔧 Configuration

The project includes several configuration files:

- **`pyproject.toml`**: Modern Python project configuration
- **`pyrightconfig.json`**: Pyright/PyLance configuration for VS Code
- **`.vscode/settings.json`**: VS Code workspace settings
- **`requirements.txt`**: Runtime dependencies
- **`requirements-dev.txt`**: Development dependencies

## 📊 Output Format

The crawler generates a structured output file:

```
# Web Crawler Results
# Domain: https://developers.facebook.com
# Start URL: https://developers.facebook.com/docs/whatsapp/cloud-api
# Total URLs found: 150
# Generated at: 2024-01-15 14:30:25

https://developers.facebook.com/docs/whatsapp/cloud-api
https://developers.facebook.com/docs/whatsapp/cloud-api/guides
https://developers.facebook.com/docs/whatsapp/cloud-api/reference
...
```

## 🏗️ Architecture

### Core Components

1. **WebCrawler Class**: Main crawler implementation
2. **URL Queue Management**: Efficient deque-based processing
3. **Link Discovery**: HTML parsing with BeautifulSoup
4. **Robots.txt Handling**: Automatic compliance checking
5. **Error Handling**: Robust network and parsing error management

### Key Methods

- `crawl()`: Main crawling loop
- `_fetch_page()`: HTTP request handling
- `_extract_links()`: HTML link extraction
- `_is_allowed_by_robots()`: Robots.txt compliance
- `save_urls_to_file()`: Output generation

## 🚨 Ethical Considerations

This crawler is designed with ethical web scraping in mind:

- **Respects robots.txt** - Follows website crawling policies
- **Rate limiting** - Configurable delays prevent server overload
- **User-Agent identification** - Clear identification of the crawler
- **Domain boundaries** - Only crawls within the target domain
- **Content filtering** - Skips non-HTML content and binary files

## 🎯 Use Cases

### RAG Implementation
Perfect for building documentation-based RAG systems:
1. **Crawl documentation sites** to collect all relevant URLs
2. **Process content** from discovered URLs
3. **Build vector database** for semantic search
4. **Generate responses** based on documentation context

### Documentation Auditing
- **Find broken links** in documentation
- **Map documentation structure** and coverage
- **Identify missing content** areas

### Content Migration
- **Inventory existing content** before migration
- **Plan content restructuring** based on current structure
- **Validate migration completeness**

## 🚀 Performance Tips

- **Adjust delay** based on target server capacity
- **Monitor logs** for optimal crawling speed
- **Use appropriate timeouts** for your network conditions
- **Consider running during off-peak hours** for large sites

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run code formatting
black src/ tests/ examples/

# Run linting
flake8 src/ tests/ examples/

# Run type checking
mypy src/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [requests](https://requests.readthedocs.io/) for HTTP handling
- HTML parsing powered by [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- XML parsing with [lxml](https://lxml.de/)

---

**Happy Crawling! 🕷️✨**
