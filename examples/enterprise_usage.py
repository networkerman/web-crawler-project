#!/usr/bin/env python3
"""
Enterprise-Grade Web Crawler Usage Examples

This script demonstrates the advanced features of the new async web crawler
including configuration management, state persistence, dynamic content handling,
and comprehensive error handling.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from web_crawler import (
    AsyncWebCrawler, 
    ConfigManager, 
    StateManager,
    DynamicContentHandler
)


async def basic_async_crawl_example():
    """Basic example of using the async crawler."""
    print("🚀 Basic Async Crawl Example")
    print("=" * 50)
    
    # Create configuration
    config = ConfigManager()
    config.set('crawler.start_url', 'https://docs.python.org/3/')
    config.set('crawler.max_urls', 10)  # Limit for demo
    config.set('crawler.max_depth', 2)
    config.set('crawler.max_concurrent', 5)
    config.set('crawler.delay', 0.5)
    config.set('dynamic_content.enable_playwright', False)  # Disable for basic example
    
    # Initialize crawler
    crawler = AsyncWebCrawler(config)
    
    # Run the crawl
    print(f"Starting crawl of: {config.get('crawler.start_url')}")
    print(f"Max URLs: {config.get('crawler.max_urls')}")
    print(f"Max Depth: {config.get('crawler.max_depth')}")
    print(f"Max Concurrent: {config.get('crawler.max_concurrent')}")
    print()
    
    try:
        unique_urls = await crawler.crawl()
        
        print(f"✅ Crawl completed!")
        print(f"📊 Total URLs found: {len(unique_urls)}")
        print(f"🔗 Total crawled: {crawler.total_crawled}")
        
        # Save results
        await crawler.save_urls_to_file('basic_crawl_results.txt')
        print(f"💾 Results saved to: basic_crawl_results.txt")
        
        # Show statistics
        stats = crawler.get_statistics()
        print(f"📏 Max depth reached: {stats['max_depth']}")
        print(f"⏱️  Duration: {stats['duration']}")
        
    except Exception as e:
        print(f"❌ Error during crawl: {e}")


async def dynamic_content_example():
    """Example using Playwright for JavaScript rendering."""
    print("\n🌐 Dynamic Content Example")
    print("=" * 50)
    
    # Create configuration with Playwright enabled
    config = ConfigManager()
    config.set('crawler.start_url', 'https://reactjs.org/docs/')
    config.set('crawler.max_urls', 5)  # Small limit for demo
    config.set('crawler.max_depth', 1)
    config.set('crawler.max_concurrent', 3)
    config.set('crawler.delay', 1.0)
    config.set('dynamic_content.enable_playwright', True)
    config.set('dynamic_content.page_load_timeout', 10000)
    
    # Initialize crawler
    crawler = AsyncWebCrawler(config)
    
    print(f"Starting dynamic crawl of: {config.get('crawler.start_url')}")
    print("JavaScript rendering: Enabled")
    print(f"Page load timeout: {config.get('dynamic_content.page_load_timeout')}ms")
    print()
    
    try:
        unique_urls = await crawler.crawl()
        
        print(f"✅ Dynamic crawl completed!")
        print(f"📊 Total URLs found: {len(unique_urls)}")
        print(f"🔗 Total crawled: {crawler.total_crawled}")
        
        # Save results
        await crawler.save_urls_to_file('dynamic_crawl_results.txt')
        print(f"💾 Results saved to: dynamic_crawl_results.txt")
        
    except Exception as e:
        print(f"❌ Error during dynamic crawl: {e}")


async def state_persistence_example():
    """Example demonstrating state persistence and resumability."""
    print("\n💾 State Persistence Example")
    print("=" * 50)
    
    # Create configuration
    config = ConfigManager()
    config.set('crawler.start_url', 'https://docs.djangoproject.com/')
    config.set('crawler.max_urls', 15)
    config.set('crawler.max_depth', 2)
    config.set('crawler.max_concurrent', 3)
    config.set('crawler.delay', 0.5)
    config.set('output.save_state', True)
    config.set('output.state_file', 'django_crawl_state.json')
    config.set('output.database_file', 'django_crawl_data.db')
    
    # Initialize state manager
    state_manager = StateManager(
        state_file=config.get('output.state_file'),
        database_file=config.get('output.database_file')
    )
    
    # Initialize crawler with state manager
    crawler = AsyncWebCrawler(config, state_manager)
    
    print(f"Starting crawl with state persistence: {config.get('crawler.start_url')}")
    print(f"State file: {config.get('output.state_file')}")
    print(f"Database file: {config.get('output.database_file')}")
    print()
    
    try:
        # First crawl
        print("🔄 First crawl (will be interrupted)...")
        unique_urls = await crawler.crawl()
        
        print(f"✅ First crawl completed!")
        print(f"📊 Total URLs found: {len(unique_urls)}")
        
        # Save results
        await crawler.save_urls_to_file('django_crawl_results.txt')
        print(f"💾 Results saved to: django_crawl_results.txt")
        
        # Show statistics
        stats = state_manager.get_crawl_statistics()
        print(f"📊 Database stats - Total URLs: {stats.get('total_urls', 0)}")
        print(f"📊 Database stats - Successful: {stats.get('successful_urls', 0)}")
        print(f"📊 Database stats - Failed: {stats.get('failed_urls', 0)}")
        
    except Exception as e:
        print(f"❌ Error during crawl: {e}")


async def configuration_management_example():
    """Example demonstrating configuration management features."""
    print("\n⚙️  Configuration Management Example")
    print("=" * 50)
    
    # Create configuration
    config = ConfigManager()
    
    # Set various configuration options
    config.set('crawler.start_url', 'https://docs.fastapi.tiangolo.com/')
    config.set('crawler.max_urls', 8)
    config.set('crawler.max_depth', 1)
    config.set('crawler.max_concurrent', 4)
    config.set('crawler.delay', 0.3)
    
    config.set('retry.max_retries', 5)
    config.set('retry.base_delay', 0.5)
    config.set('retry.max_delay', 30.0)
    
    config.set('dynamic_content.enable_playwright', True)
    config.set('dynamic_content.page_load_timeout', 8000)
    
    config.set('output.save_state', True)
    config.set('output.state_file', 'fastapi_crawl_state.json')
    
    # Validate configuration
    if config.validate_config():
        print("✅ Configuration validation passed")
    else:
        print("❌ Configuration validation failed")
        return
    
    # Display configuration
    print("\nCurrent Configuration:")
    config.print_config()
    
    # Save configuration to file
    config_file = 'custom_config.yaml'
    if config.save_config(config_file):
        print(f"\n💾 Configuration saved to: {config_file}")
    
    # Initialize crawler with custom config
    crawler = AsyncWebCrawler(config)
    
    print(f"\n🚀 Starting crawl with custom configuration...")
    print(f"Target: {config.get('crawler.start_url')}")
    print(f"Max URLs: {config.get('crawler.max_urls')}")
    print(f"Retry attempts: {config.get('retry.max_retries')}")
    print(f"JavaScript rendering: {'Enabled' if config.get('dynamic_content.enable_playwright') else 'Disabled'}")
    
    try:
        unique_urls = await crawler.crawl()
        
        print(f"\n✅ Custom configuration crawl completed!")
        print(f"📊 Total URLs found: {len(unique_urls)}")
        
        # Save results
        await crawler.save_urls_to_file('fastapi_crawl_results.txt')
        print(f"💾 Results saved to: fastapi_crawl_results.txt")
        
    except Exception as e:
        print(f"❌ Error during custom configuration crawl: {e}")


async def error_handling_example():
    """Example demonstrating error handling and retry mechanisms."""
    print("\n🔄 Error Handling and Retry Example")
    print("=" * 50)
    
    # Create configuration with aggressive retry settings
    config = ConfigManager()
    config.set('crawler.start_url', 'https://httpstat.us/500')  # Will return 500 errors
    config.set('crawler.max_urls', 3)
    config.set('crawler.max_depth', 1)
    config.set('crawler.max_concurrent', 2)
    config.set('crawler.delay', 0.1)
    
    # Set aggressive retry settings
    config.set('retry.max_retries', 3)
    config.set('retry.base_delay', 0.1)
    config.set('retry.max_delay', 5.0)
    
    # Initialize crawler
    crawler = AsyncWebCrawler(config)
    
    print(f"Starting error handling test with: {config.get('crawler.start_url')}")
    print(f"Max retries: {config.get('retry.max_retries')}")
    print(f"Base delay: {config.get('retry.base_delay')}s")
    print(f"Max delay: {config.get('retry.max_delay')}s")
    print()
    
    try:
        unique_urls = await crawler.crawl()
        
        print(f"✅ Error handling test completed!")
        print(f"📊 Total URLs found: {len(unique_urls)}")
        print(f"🔗 Total crawled: {crawler.total_crawled}")
        
        # Show statistics
        stats = crawler.get_statistics()
        print(f"⏱️  Duration: {stats['duration']}")
        
    except Exception as e:
        print(f"❌ Error during error handling test: {e}")


async def main():
    """Run all examples."""
    print("🕷️  Enterprise-Grade Web Crawler Examples")
    print("=" * 60)
    print("This script demonstrates the advanced features of the new async web crawler.")
    print()
    
    try:
        # Run examples
        await basic_async_crawl_example()
        await dynamic_content_example()
        await state_persistence_example()
        await configuration_management_example()
        await error_handling_example()
        
        print("\n" + "=" * 60)
        print("🎉 All examples completed successfully!")
        print("\nGenerated files:")
        print("  - basic_crawl_results.txt")
        print("  - dynamic_crawl_results.txt")
        print("  - django_crawl_results.txt")
        print("  - fastapi_crawl_results.txt")
        print("  - custom_config.yaml")
        print("  - Various state and database files")
        
    except KeyboardInterrupt:
        print("\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    # Check if Playwright is available
    try:
        import playwright
        print("✅ Playwright is available for dynamic content handling")
    except ImportError:
        print("⚠️  Playwright not available. Dynamic content examples will be limited.")
        print("   Install with: pip install playwright")
        print("   Then run: playwright install")
    
    # Run examples
    asyncio.run(main())
