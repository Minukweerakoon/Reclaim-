from prometheus_client import Counter, Histogram, Gauge, start_http_server
import psutil
import time
from functools import wraps
import logging
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MetricsCollector')

_instance = None

class MetricsCollector:
    """
    Prometheus metrics collection for system monitoring.
    
    Metrics:
    - Request counters by endpoint and status
    - Response time histograms by endpoint
    - Current validation confidence scores
    - System resource usage (CPU, memory)
    - Active WebSocket connections
    """
    
    def __new__(cls, *args, **kwargs):
        global _instance
        if _instance is None:
            _instance = super(MetricsCollector, cls).__new__(cls)
        return _instance

    def __init__(self, port: int = 8001):
        # Check if metrics are already registered
        if hasattr(self, '_metrics_initialized'):
            return

        # Request metrics
        self.request_counter = Counter(
            'validation_requests_total',
            'Total validation requests',
            ['endpoint', 'status']
        )
        
        self.response_time_histogram = Histogram(
            'validation_response_time_seconds',
            'Response time for validation requests',
            ['endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        )
        
        # Validation metrics
        self.confidence_gauge = Gauge(
            'validation_confidence_score',
            'Current validation confidence score',
            ['modality']
        )
        
        self.validation_success_counter = Counter(
            'validation_success_total',
            'Total successful validations',
            ['routing']
        )
        
        self.validation_failure_counter = Counter(
            'validation_failure_total',
            'Total failed validations',
            ['modality', 'reason']
        )
        
        # System metrics
        self.system_memory_gauge = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes'
        )
        
        self.system_cpu_gauge = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage'
        )
        
        self.active_connections_gauge = Gauge(
            'active_websocket_connections',
            'Number of active WebSocket connections'
        )
        
        self._metrics_initialized = True
        self._system_metrics_thread = None
        self._stop_event = threading.Event()

    def track_request(self, endpoint: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                status = 'success'
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = 'error'
                    raise
                finally:
                    duration = time.time() - start_time
                    self.request_counter.labels(endpoint=endpoint, status=status).inc()
                    self.response_time_histogram.labels(endpoint=endpoint).observe(duration)
            
            return wrapper
        return decorator
    
    def record_validation_result(self, modality: str, score: float, routing: str):
        """Record validation results"""
        self.confidence_gauge.labels(modality=modality).set(score)
        self.validation_success_counter.labels(routing=routing).inc()
    
    def record_validation_failure(self, modality: str, reason: str):
        """Record validation failures"""
        self.validation_failure_counter.labels(modality=modality, reason=reason).inc()
    
    def start_system_metrics_collection(self):
        """Start background task to collect system metrics"""

        if self._system_metrics_thread and self._system_metrics_thread.is_alive():
            return

        def collect_metrics():
            while not self._stop_event.is_set():
                memory = psutil.virtual_memory()
                self.system_memory_gauge.set(memory.used)

                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_cpu_gauge.set(cpu_percent)

                if self._stop_event.wait(9):
                    break

        self._stop_event.clear()
        self._system_metrics_thread = threading.Thread(
            target=collect_metrics,
            name="metrics-collector",
            daemon=True,
        )
        self._system_metrics_thread.start()
    
    def update_active_connections(self, count: int):
        """Update active WebSocket connections count"""
        self.active_connections_gauge.set(count)
