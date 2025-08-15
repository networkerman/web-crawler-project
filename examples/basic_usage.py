#!/usr/bin/env python3
"""
Example usage of the Web Crawler

This script demonstrates how to use the WebCrawler class programmatically
instead of using the command-line interface.
"""

from web_crawler import WebCrawler
import time

def main():
    """Example of using the WebCrawler programmatically."""
    
    # Example starting URL (Facebook WhatsApp Cloud API docs)
    start_url = "https://developers.facebook.com/docs/whatsapp/cloud-api"
    
    print("🚀 Starting Web Crawler Example")
    print(f"📍 Target URL: {start_url}")
    print("=" * 60)
    
    try:
        # Initialize the crawler with custom settings
        crawler = WebCrawler(
            start_url=start_url,
            delay=1.5,  # 1.5 second delay between requests
            timeout=45   # 45 second timeout
        )
        
        print("✅ Crawler initialized successfully")
        print(f"🌐 Domain: {crawler.base_domain}")
        print(f"⏱️  Delay: {crawler.delay} seconds")
        print(f"⏰ Timeout: {crawler.timeout} seconds")
        print("=" * 60)
        
        # Start the crawling process
        print("🕷️  Beginning crawl...")
        start_time = time.time()
        
        unique_urls = crawler.crawl()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 60)
        print("🎉 Crawl completed successfully!")
        print(f"📊 Total unique URLs found: {len(unique_urls)}")
        print(f"⏱️  Total time: {duration:.2f} seconds")
        print(f"🚀 Average speed: {len(unique_urls)/duration:.2f} URLs/second")
        
        # Save results to a custom filename
        output_file = "facebook_whatsapp_urls.txt"
        crawler.save_urls_to_file(output_file)
        print(f"💾 Results saved to: {output_file}")
        
        # Display first 10 URLs as a preview
        print("\n📋 First 10 URLs found:")
        print("-" * 40)
        sorted_urls = sorted(unique_urls)
        for i, url in enumerate(sorted_urls[:10], 1):
            print(f"{i:2d}. {url}")
        
        if len(sorted_urls) > 10:
            print(f"   ... and {len(sorted_urls) - 10} more URLs")
        
    except KeyboardInterrupt:
        print("\n⚠️  Crawl interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during crawl: {e}")
        raise

if __name__ == "__main__":
    main()
