#!/usr/bin/env python3
"""
Configuration Manager for Web Crawler

Handles loading and managing configuration from YAML files with CLI override support.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration for the web crawler."""
    
    DEFAULT_CONFIG = {
        'crawler': {
            'start_url': 'https://docs.example.com',
            'delay': 1.0,
            'timeout': 60,
            'max_concurrent': 10,
            'max_urls': 0,
            'max_depth': 0
        },
        'retry': {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 60.0
        },
        'dynamic_content': {
            'enable_playwright': True,
            'page_load_timeout': 30000,
            'network_idle_timeout': 10000,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
            'stealth_mode': True
        },
        'output': {
            'filename': 'crawled_urls.txt',
            'save_state': True,
            'state_file': 'crawl_state.json',
            'database_file': 'crawl_data.db'
        },
        'logging': {
            'level': 'INFO',
            'log_file': 'crawler.log',
            'console_logging': True,
            'file_logging': True,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'robots': {
            'respect_robots': True,
            'user_agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        },
        'rate_limit': {
            'enabled': True,
            'requests_per_second': 1.0,
            'burst_size': 5
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = Path(config_file) if config_file else Path('config.yaml')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Returns:
            Configuration dictionary
        """
        config = self.DEFAULT_CONFIG.copy()
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                
                if file_config:
                    # Deep merge configuration
                    config = self._deep_merge(config, file_config)
                    logger.info(f"Configuration loaded from: {self.config_file}")
                else:
                    logger.warning(f"Configuration file is empty: {self.config_file}")
                    
            except Exception as e:
                logger.error(f"Failed to load configuration from {self.config_file}: {e}")
                logger.info("Using default configuration")
        else:
            logger.info(f"Configuration file not found: {self.config_file}")
            logger.info("Using default configuration")
        
        return config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'crawler.delay')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'crawler.delay')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def update_from_cli(self, cli_args: Dict[str, Any]) -> None:
        """
        Update configuration from CLI arguments.
        
        Args:
            cli_args: Dictionary of CLI arguments
        """
        # Map CLI arguments to configuration keys
        cli_mapping = {
            'start_url': 'crawler.start_url',
            'delay': 'crawler.delay',
            'timeout': 'crawler.timeout',
            'max_concurrent': 'crawler.max_concurrent',
            'max_urls': 'crawler.max_urls',
            'max_depth': 'crawler.max_depth',
            'max_retries': 'retry.max_retries',
            'enable_playwright': 'dynamic_content.enable_playwright',
            'output': 'output.filename',
            'save_state': 'output.save_state',
            'state_file': 'output.state_file',
            'database_file': 'output.database_file',
            'log_level': 'logging.level',
            'log_file': 'logging.log_file',
            'respect_robots': 'robots.respect_robots',
            'user_agent': 'robots.user_agent',
            'rate_limit_enabled': 'rate_limit.enabled',
            'requests_per_second': 'rate_limit.requests_per_second'
        }
        
        for cli_key, config_key in cli_mapping.items():
            if cli_key in cli_args and cli_args[cli_key] is not None:
                self.set(config_key, cli_args[cli_key])
                logger.debug(f"Updated {config_key} from CLI: {cli_args[cli_key]}")
    
    def save_config(self, filename: Optional[str] = None) -> bool:
        """
        Save current configuration to file.
        
        Args:
            filename: Output filename (optional)
            
        Returns:
            True if successful, False otherwise
        """
        output_file = Path(filename) if filename else self.config_file
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_crawler_config(self) -> Dict[str, Any]:
        """
        Get crawler-specific configuration.
        
        Returns:
            Crawler configuration dictionary
        """
        return {
            'start_url': self.get('crawler.start_url'),
            'delay': self.get('crawler.delay'),
            'timeout': self.get('crawler.timeout'),
            'max_concurrent': self.get('crawler.max_concurrent'),
            'max_urls': self.get('crawler.max_urls'),
            'max_depth': self.get('crawler.max_depth'),
            'max_retries': self.get('retry.max_retries'),
            'base_delay': self.get('retry.base_delay'),
            'max_delay': self.get('retry.max_delay'),
            'enable_playwright': self.get('dynamic_content.enable_playwright'),
            'page_load_timeout': self.get('dynamic_content.page_load_timeout'),
            'network_idle_timeout': self.get('dynamic_content.network_idle_timeout'),
            'user_agent': self.get('dynamic_content.user_agent'),
            'respect_robots': self.get('robots.respect_robots'),
            'robots_user_agent': self.get('robots.user_agent'),
            'rate_limit_enabled': self.get('rate_limit.enabled'),
            'requests_per_second': self.get('rate_limit.requests_per_second'),
            'burst_size': self.get('rate_limit.burst_size')
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        """
        Get output-specific configuration.
        
        Returns:
            Output configuration dictionary
        """
        return {
            'filename': self.get('output.filename'),
            'save_state': self.get('output.save_state'),
            'state_file': self.get('output.state_file'),
            'database_file': self.get('output.database_file')
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging-specific configuration.
        
        Returns:
            Logging configuration dictionary
        """
        return {
            'level': self.get('logging.level'),
            'log_file': self.get('logging.log_file'),
            'console_logging': self.get('logging.console_logging'),
            'file_logging': self.get('logging.file_logging'),
            'format': self.get('logging.format')
        }
    
    def validate_config(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            True if valid, False otherwise
        """
        errors = []
        
        # Validate crawler settings
        if self.get('crawler.delay', 0) < 0:
            errors.append("crawler.delay must be non-negative")
        
        if self.get('crawler.timeout', 0) <= 0:
            errors.append("crawler.timeout must be positive")
        
        if self.get('crawler.max_concurrent', 0) <= 0:
            errors.append("crawler.max_concurrent must be positive")
        
        if self.get('crawler.max_urls', 0) < 0:
            errors.append("crawler.max_urls must be non-negative")
        
        if self.get('crawler.max_depth', 0) < 0:
            errors.append("crawler.max_depth must be non-negative")
        
        # Validate retry settings
        if self.get('retry.max_retries', 0) < 0:
            errors.append("retry.max_retries must be non-negative")
        
        if self.get('retry.base_delay', 0) <= 0:
            errors.append("retry.base_delay must be positive")
        
        if self.get('retry.max_delay', 0) <= 0:
            errors.append("retry.max_delay must be positive")
        
        # Validate dynamic content settings
        if self.get('dynamic_content.page_load_timeout', 0) <= 0:
            errors.append("dynamic_content.page_load_timeout must be positive")
        
        if self.get('dynamic_content.network_idle_timeout', 0) <= 0:
            errors.append("dynamic_content.network_idle_timeout must be positive")
        
        # Validate rate limiting
        if self.get('rate_limit.requests_per_second', 0) <= 0:
            errors.append("rate_limit.requests_per_second must be positive")
        
        if self.get('rate_limit.burst_size', 0) <= 0:
            errors.append("rate_limit.burst_size must be positive")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def print_config(self) -> None:
        """Print the current configuration."""
        print("Current Configuration:")
        print("=" * 50)
        
        def print_section(config_dict, prefix=""):
            for key, value in config_dict.items():
                if isinstance(value, dict):
                    print(f"{prefix}{key}:")
                    print_section(value, prefix + "  ")
                else:
                    print(f"{prefix}{key}: {value}")
        
        print_section(self.config)
        print("=" * 50)
