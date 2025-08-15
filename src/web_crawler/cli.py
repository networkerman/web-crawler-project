#!/usr/bin/env python3
"""
Command Line Interface for Web Crawler

Provides a command-line interface for the WebCrawler class.
"""

import argparse
import sys
import logging
from .crawler import WebCrawler

# Configure logging for CLI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


def main():
    """Main function to run the crawler from command line."""
    parser = argparse.ArgumentParser(
        description='Web crawler for developer documentation sites',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://developers.facebook.com/docs/whatsapp/cloud-api"
  %(prog)s "https://docs.webengage.com/" --delay 2.0
  %(prog)s "https://docs.example.com/" --timeout 60 --output my_urls.txt
        """
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
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        print("🕷️  Web Crawler for Developer Documentation Sites")
        print("=" * 60)
        print(f"📍 Starting URL: {args.url}")
        print(f"⏱️  Delay: {args.delay} seconds")
        print(f"⏰ Timeout: {args.timeout} seconds")
        print(f"💾 Output: {args.output}")
        print("=" * 60)
        
        # Initialize and run crawler
        crawler = WebCrawler(
            start_url=args.url,
            delay=args.delay,
            timeout=args.timeout
        )
        
        # Perform the crawl
        print("🚀 Beginning crawl...")
        unique_urls = crawler.crawl()
        
        # Save results
        crawler.save_urls_to_file(args.output)
        
        print("=" * 60)
        print("✅ Crawl completed successfully!")
        print(f"📊 Total unique URLs found: {len(unique_urls)}")
        print(f"💾 Results saved to: {args.output}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Crawl interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
