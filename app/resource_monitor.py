import logging
import psutil
from typing import Dict
from app.storage_manager import storage_manager

class ResourceMonitor:
    def __init__(self):
        self.metrics: Dict[str, list] = {
            'ram_usage': [],
            'cpu_usage': [],
            'storage_usage': [],
            'requests_count': 0
        }
        self.logger = logging.getLogger(__name__)
        
    def log_metrics(self):
        # ... (codice dal messaggio precedente)
        pass

monitor = ResourceMonitor()