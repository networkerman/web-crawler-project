#!/usr/bin/env python3
"""
Enhanced Command Line Interface for Async Web Crawler

Provides a modern, user-friendly command-line interface with progress bars,
rich formatting, and comprehensive configuration options.
"""

import asyncio
import click
import sys
from pathlib import Path
from typing import Optional
import structlog

from .config_manager import ConfigManager
from .state_manager import StateManager
from .crawler import WebCrawler

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def setup_logging(log_level: str, log_file: str, console_logging: bool, file_logging: bool):
    """Setup logging configuration."""
    import logging
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if file_logging:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


@click.group()
@click.version_option(version="2.0.0")
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--log-level', default='INFO', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
              help='Logging level')
@click.option('--log-file', default='crawler.log', help='Log file path')
@click.pass_context
def cli(ctx, config, log_level, log_file):
    """Enterprise-Grade Async Web Crawler for Developer Documentation Sites"""
    ctx.ensure_object(dict)
    
    # Load configuration
    config_manager = ConfigManager(config)
    ctx.obj['config'] = config_manager
    
    # Setup logging
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        console_logging=True,
        file_logging=True
    )
    
    # Validate configuration
    if not config_manager.validate_config():
        click.echo("❌ Configuration validation failed. Please check your config file.")
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('--delay', type=float, help='Delay between requests in seconds')
@click.option('--timeout', type=int, help='Request timeout in seconds')
@click.option('--max-concurrent', type=int, help='Maximum concurrent requests')
@click.option('--max-urls', type=int, help='Maximum URLs to crawl (0 = unlimited)')
@click.option('--max-depth', type=int, help='Maximum crawl depth (0 = unlimited)')
@click.option('--max-retries', type=int, help='Maximum retry attempts')
@click.option('--enable-playwright/--disable-playwright', default=None, 
              help='Enable/disable JavaScript rendering')
@click.option('--output', help='Output filename')
@click.option('--save-state/--no-save-state', default=None, help='Save crawl state')
@click.option('--state-file', help='State file path')
@click.option('--database-file', help='Database file path')
@click.option('--respect-robots/--no-respect-robots', default=None, help='Respect robots.txt')
@click.option('--user-agent', help='Custom user agent string')
@click.option('--rate-limit-enabled/--no-rate-limit', default=None, help='Enable rate limiting')
@click.option('--requests-per-second', type=float, help='Requests per second limit')
@click.option('--show-progress/--no-progress', default=True, help='Show progress bar')
@click.option('--resume/--no-resume', default=True, help='Resume from previous state')
@click.pass_context
def crawl(ctx, url, **kwargs):
    """Start crawling from a given URL"""
    config = ctx.obj['config']
    
    # Update configuration from CLI arguments
    cli_args = {k: v for k, v in kwargs.items() if v is not None}
    cli_args['start_url'] = url
    config.update_from_cli(cli_args)
    
    # Display configuration
    if click.get_current_context().get_help_option():
        config.print_config()
        return
    
    click.echo("🕷️  Enterprise-Grade Async Web Crawler")
    click.echo("=" * 60)
    click.echo(f"📍 Starting URL: {url}")
    click.echo(f"⏱️  Delay: {config.get('crawler.delay')} seconds")
    click.echo(f"⏰ Timeout: {config.get('crawler.timeout')} seconds")
    click.echo(f"🚀 Max Concurrent: {config.get('crawler.max_concurrent')}")
    click.echo(f"🔗 Max URLs: {config.get('crawler.max_urls') or 'Unlimited'}")
    click.echo(f"📏 Max Depth: {config.get('crawler.max_depth') or 'Unlimited'}")
    click.echo(f"🔄 Max Retries: {config.get('retry.max_retries')}")
    click.echo(f"🌐 JavaScript Rendering: {'Enabled' if config.get('dynamic_content.enable_playwright') else 'Disabled'}")
    click.echo(f"🤖 Respect Robots: {'Yes' if config.get('robots.respect_robots') else 'No'}")
    click.echo(f"📊 Rate Limiting: {'Enabled' if config.get('rate_limit.enabled') else 'Disabled'}")
    click.echo(f"💾 Save State: {'Yes' if config.get('output.save_state') else 'No'}")
    click.echo(f"🔄 Resume: {'Yes' if cli_args.get('resume', True) else 'No'}")
    click.echo("=" * 60)
    
    # Initialize state manager
    state_manager = StateManager(
        state_file=config.get('output.state_file'),
        database_file=config.get('output.database_file')
    )
    
    # Initialize crawler
    crawler = WebCrawler(config, state_manager)
    
    # Run the crawl
    try:
        if cli_args.get('show_progress', True):
            # Run with progress tracking
            asyncio.run(run_crawl_with_progress(crawler))
        else:
            # Run without progress tracking
            asyncio.run(run_crawl_simple(crawler))
        
        # Save results
        asyncio.run(crawler.save_urls_to_file())
        
        # Display statistics
        stats = crawler.get_statistics()
        click.echo("=" * 60)
        click.echo("✅ Crawl completed successfully!")
        click.echo(f"📊 Total unique URLs found: {stats['total_urls']}")
        click.echo(f"🔗 Total crawled: {stats['total_crawled']}")
        click.echo(f"📏 Max depth reached: {stats['max_depth']}")
        click.echo(f"⏱️  Duration: {stats['duration']}")
        click.echo(f"💾 Results saved to: {config.get('output.filename')}")
        
        if config.get('output.save_state'):
            click.echo(f"💾 State saved to: {config.get('output.state_file')}")
            click.echo(f"🗄️  Database: {config.get('output.database_file')}")
        
    except KeyboardInterrupt:
        click.echo("\n⚠️  Crawl interrupted by user")
        # Save state before exiting
        if config.get('output.save_state'):
            asyncio.run(crawler._save_state())
            click.echo("💾 Crawl state saved. You can resume later with --resume")
        sys.exit(1)
    except Exception as e:
        logger.error("Fatal error during crawl", error=str(e))
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


async def run_crawl_with_progress(crawler: AsyncWebCrawler):
    """Run crawl with progress bar."""
    from tqdm import tqdm
    
    # Create progress bar
    with tqdm(desc="Crawling URLs", unit="url", dynamic_ncols=True) as pbar:
        # Store original worker method
        original_worker = crawler._crawl_worker
        
        async def progress_worker(worker_id: int):
            """Worker with progress tracking."""
            while True:
                try:
                    # Get URL from queue
                    queue_item = await crawler.url_queue.get()
                    if queue_item is None:  # Sentinel value to stop worker
                        break
                    
                    url, depth = queue_item
                    
                    # Check if already visited
                    if url in crawler.visited_urls:
                        crawler.url_queue.task_done()
                        continue
                    
                    # Check robots.txt
                    if not await crawler._is_allowed_by_robots(url):
                        crawler.visited_urls.add(url)
                        crawler.url_queue.task_done()
                        continue
                    
                    # Mark as visited
                    crawler.visited_urls.add(url)
                    crawler.unique_urls.add(url)
                    crawler.url_depths[url] = depth
                    crawler.total_crawled += 1
                    
                    # Update progress bar
                    pbar.set_description(f"Crawling {url[:50]}...")
                    pbar.set_postfix({
                        'URLs': len(crawler.unique_urls),
                        'Queue': crawler.url_queue.qsize(),
                        'Depth': depth
                    })
                    
                    # Process the page
                    new_links = await crawler._process_page(url, depth)
                    
                    # Add new links to queue
                    for link in new_links:
                        await crawler.url_queue.put((link, depth + 1))
                    
                    # Check if we've reached the URL limit
                    if crawler.max_urls > 0 and crawler.total_crawled >= crawler.max_urls:
                        break
                    
                    # Respect delay between requests
                    if crawler.delay > 0:
                        await asyncio.sleep(crawler.delay)
                    
                    # Mark task as done and update progress
                    crawler.url_queue.task_done()
                    pbar.update(1)
                    
                except Exception as e:
                    logger.error("Worker error", worker_id=worker_id, error=str(e))
                    crawler.url_queue.task_done()
                    pbar.update(1)
        
        # Replace worker method temporarily
        crawler._crawl_worker = progress_worker
        
        try:
            # Run the crawl
            await crawler.crawl()
        finally:
            # Restore original worker method
            crawler._crawl_worker = original_worker


async def run_crawl_simple(crawler: AsyncWebCrawler):
    """Run crawl without progress bar."""
    await crawler.crawl()


@cli.command()
@click.option('--config-file', help='Output configuration file path')
@click.pass_context
def config(ctx, config_file):
    """Show or generate configuration"""
    config_manager = ctx.obj['config']
    
    if config_file:
        # Save configuration to file
        if config_manager.save_config(config_file):
            click.echo(f"✅ Configuration saved to: {config_file}")
        else:
            click.echo("❌ Failed to save configuration")
            sys.exit(1)
    else:
        # Display current configuration
        config_manager.print_config()


@cli.command()
@click.option('--days', type=int, default=30, help='Number of days to keep data')
@click.pass_context
def cleanup(ctx, days):
    """Clean up old crawl data"""
    config = ctx.obj['config']
    state_manager = StateManager(
        state_file=config.get('output.state_file'),
        database_file=config.get('output.database_file')
    )
    
    if state_manager.cleanup_old_sessions(days):
        click.echo(f"✅ Cleaned up data older than {days} days")
    else:
        click.echo("❌ Failed to cleanup old data")
        sys.exit(1)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show crawling statistics"""
    config = ctx.obj['config']
    state_manager = StateManager(
        state_file=config.get('output.state_file'),
        database_file=config.get('output.database_file')
    )
    
    stats = state_manager.get_crawl_statistics()
    
    click.echo("📊 Crawling Statistics")
    click.echo("=" * 40)
    click.echo(f"Total URLs: {stats.get('total_urls', 0)}")
    click.echo(f"Successful: {stats.get('successful_urls', 0)}")
    click.echo(f"Failed: {stats.get('failed_urls', 0)}")
    click.echo(f"Total Sessions: {stats.get('total_sessions', 0)}")
    click.echo(f"Running Sessions: {stats.get('running_sessions', 0)}")


@cli.command()
@click.argument('url')
@click.option('--screenshot', is_flag=True, help='Take a screenshot')
@click.option('--metrics', is_flag=True, help='Get page metrics')
@click.pass_context
def test(ctx, url, screenshot, metrics):
    """Test dynamic content handling for a single URL"""
    config = ctx.obj['config']
    
    click.echo(f"🧪 Testing dynamic content handling for: {url}")
    
    async def test_url():
        from .dynamic_handler import DynamicContentHandler
        
        handler = DynamicContentHandler(
            enable_playwright=config.get('dynamic_content.enable_playwright'),
            page_load_timeout=config.get('dynamic_content.page_load_timeout'),
            network_idle_timeout=config.get('dynamic_content.network_idle_timeout'),
            user_agent=config.get('dynamic_content.user_agent')
        )
        
        async with handler:
            # Test basic rendering
            click.echo("📄 Testing page rendering...")
            rendered_content = await handler.render_page(url)
            
            if rendered_content:
                click.echo("✅ Page rendered successfully")
                click.echo(f"📏 Content length: {len(rendered_content)} characters")
                
                # Test link extraction
                links = await handler.extract_links_from_rendered(url, rendered_content)
                click.echo(f"🔗 Links found: {len(links)}")
                
                # Take screenshot if requested
                if screenshot:
                    filename = await handler.take_screenshot(url)
                    if filename:
                        click.echo(f"📸 Screenshot saved: {filename}")
                
                # Get metrics if requested
                if metrics:
                    page_metrics = await handler.get_page_metrics(url)
                    if page_metrics:
                        click.echo("📊 Page Metrics:")
                        for key, value in page_metrics.items():
                            if key != 'url':
                                click.echo(f"  {key}: {value}")
            else:
                click.echo("❌ Failed to render page")
    
    try:
        asyncio.run(test_url())
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


@cli.command()
def install():
    """Install Playwright browsers"""
    try:
        import subprocess
        click.echo("🔧 Installing Playwright browsers...")
        result = subprocess.run(['playwright', 'install'], capture_output=True, text=True)
        
        if result.returncode == 0:
            click.echo("✅ Playwright browsers installed successfully")
        else:
            click.echo("❌ Failed to install Playwright browsers")
            click.echo(f"Error: {result.stderr}")
            sys.exit(1)
            
    except FileNotFoundError:
        click.echo("❌ Playwright not found. Please install it first:")
        click.echo("   pip install playwright")
        sys.exit(1)


if __name__ == '__main__':
    cli()
