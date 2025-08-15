"""
Monitoring and metrics for web crawler.
"""
from typing import Dict, Any, List
import time
from dataclasses import dataclass, field
from datetime import datetime
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class CrawlMetrics:
    """Metrics for monitoring crawl performance."""
    start_time: float = field(default_factory=time.time)
    urls_crawled: int = 0
    urls_failed: int = 0
    bytes_downloaded: int = 0
    response_times: List[float] = field(default_factory=list)
    status_codes: Dict[int, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    content_types: Dict[str, int] = field(default_factory=dict)
    
    def add_response(self, status_code: int, response_time: float, content_size: int, content_type: str = None):
        """Record a response."""
        self.urls_crawled += 1
        self.bytes_downloaded += content_size
        self.response_times.append(response_time)
        
        # Track status codes
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        
        # Track content types
        if content_type:
            self.content_types[content_type] = self.content_types.get(content_type, 0) + 1
    
    def add_error(self, error_message: str):
        """Record an error."""
        self.urls_failed += 1
        self.errors.append(error_message)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        duration = time.time() - self.start_time
        
        # Calculate response time statistics
        if self.response_times:
            avg_response_time = statistics.mean(self.response_times)
            median_response_time = statistics.median(self.response_times)
            min_response_time = min(self.response_times)
            max_response_time = max(self.response_times)
            response_time_95th = statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else None
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = response_time_95th = 0
        
        # Calculate success rate
        total_requests = self.urls_crawled + self.urls_failed
        success_rate = (self.urls_crawled / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate throughput
        urls_per_second = self.urls_crawled / duration if duration > 0 else 0
        bytes_per_second = self.bytes_downloaded / duration if duration > 0 else 0
        
        return {
            'duration_seconds': duration,
            'urls_per_second': urls_per_second,
            'bytes_per_second': bytes_per_second,
            'total_requests': total_requests,
            'successful_requests': self.urls_crawled,
            'failed_requests': self.urls_failed,
            'success_rate_percent': success_rate,
            'bytes_downloaded': self.bytes_downloaded,
            'avg_response_time': avg_response_time,
            'median_response_time': median_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'response_time_95th_percentile': response_time_95th,
            'status_codes': dict(self.status_codes),
            'content_types': dict(self.content_types),
            'error_count': len(self.errors),
            'common_errors': self._get_common_errors()
        }
    
    def _get_common_errors(self) -> List[Dict[str, Any]]:
        """Get most common errors with counts."""
        error_counts = {}
        for error in self.errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        # Sort by count (descending) and return top 10
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'error': error, 'count': count} for error, count in sorted_errors[:10]]
    
    def reset(self):
        """Reset metrics."""
        self.start_time = time.time()
        self.urls_crawled = 0
        self.urls_failed = 0
        self.bytes_downloaded = 0
        self.response_times.clear()
        self.status_codes.clear()
        self.errors.clear()
        self.content_types.clear()


class CrawlMonitor:
    """Monitor for tracking crawl performance and health."""
    
    def __init__(self):
        """Initialize the monitor."""
        self.metrics = CrawlMetrics()
        self.alerts: List[Dict[str, Any]] = []
        self.thresholds = {
            'error_rate': 0.1,  # 10% error rate threshold
            'response_time_95th': 5.0,  # 5 seconds 95th percentile threshold
            'success_rate': 0.9,  # 90% success rate threshold
        }
    
    def record_response(self, status_code: int, response_time: float, content_size: int, content_type: str = None):
        """Record a response."""
        self.metrics.add_response(status_code, response_time, content_size, content_type)
        self._check_alerts()
    
    def record_error(self, error_message: str):
        """Record an error."""
        self.metrics.add_error(error_message)
        self._check_alerts()
    
    def _check_alerts(self):
        """Check if any thresholds have been exceeded."""
        summary = self.metrics.get_summary()
        
        # Check error rate
        if summary['failed_requests'] > 0:
            error_rate = summary['failed_requests'] / summary['total_requests']
            if error_rate > self.thresholds['error_rate']:
                self._add_alert('HIGH_ERROR_RATE', f"Error rate {error_rate:.2%} exceeds threshold {self.thresholds['error_rate']:.2%}")
        
        # Check response time
        if summary['response_time_95th_percentile'] and summary['response_time_95th_percentile'] > self.thresholds['response_time_95th']:
            self._add_alert('HIGH_RESPONSE_TIME', f"95th percentile response time {summary['response_time_95th_percentile']:.2f}s exceeds threshold {self.thresholds['response_time_95th']}s")
        
        # Check success rate
        if summary['success_rate_percent'] < (self.thresholds['success_rate'] * 100):
            self._add_alert('LOW_SUCCESS_RATE', f"Success rate {summary['success_rate_percent']:.1f}% below threshold {self.thresholds['success_rate'] * 100:.1f}%")
    
    def _add_alert(self, alert_type: str, message: str):
        """Add an alert."""
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics.get_summary()
        }
        self.alerts.append(alert)
        logger.warning(f"ALERT: {alert_type} - {message}")
    
    def get_health_status(self) -> str:
        """Get overall health status."""
        if not self.alerts:
            return 'HEALTHY'
        elif len([a for a in self.alerts if a['type'] in ['HIGH_ERROR_RATE', 'LOW_SUCCESS_RATE']]) > 0:
            return 'CRITICAL'
        else:
            return 'WARNING'
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        summary = self.metrics.get_summary()
        
        return {
            'health_status': self.get_health_status(),
            'metrics': summary,
            'alerts': self.alerts,
            'recommendations': self._get_recommendations(summary)
        }
    
    def _get_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Get performance improvement recommendations."""
        recommendations = []
        
        # Response time recommendations
        if summary['avg_response_time'] > 2.0:
            recommendations.append("Consider increasing concurrent workers to reduce response times")
        
        if summary['response_time_95th_percentile'] and summary['response_time_95th_percentile'] > 5.0:
            recommendations.append("95th percentile response time is high - consider optimizing network requests")
        
        # Error rate recommendations
        if summary['success_rate_percent'] < 95:
            recommendations.append("Success rate below 95% - review error handling and retry mechanisms")
        
        # Throughput recommendations
        if summary['urls_per_second'] < 1.0:
            recommendations.append("Crawl rate is low - consider reducing delays or increasing concurrency")
        
        # Content type recommendations
        if summary['content_types'].get('text/html', 0) < summary['total_requests'] * 0.8:
            recommendations.append("Many non-HTML responses - review content type filtering")
        
        return recommendations
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format."""
        if format.lower() == 'json':
            import json
            return json.dumps(self.get_performance_report(), indent=2)
        elif format.lower() == 'csv':
            return self._export_csv()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_csv(self) -> str:
        """Export metrics as CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Metric', 'Value', 'Unit'])
        
        # Write metrics
        summary = self.metrics.get_summary()
        for key, value in summary.items():
            if isinstance(value, (int, float, str)):
                writer.writerow([key, value, ''])
        
        return output.getvalue()
    
    def reset(self):
        """Reset monitor state."""
        self.metrics.reset()
        self.alerts.clear()


# Global monitor instance
_global_monitor = CrawlMonitor()


def get_global_monitor() -> CrawlMonitor:
    """Get the global monitor instance."""
    return _global_monitor


def record_response(status_code: int, response_time: float, content_size: int, content_type: str = None):
    """Record a response using the global monitor."""
    _global_monitor.record_response(status_code, response_time, content_size, content_type)


def record_error(error_message: str):
    """Record an error using the global monitor."""
    _global_monitor.record_error(error_message)


def get_performance_report() -> Dict[str, Any]:
    """Get performance report from global monitor."""
    return _global_monitor.get_performance_report()
