import psutil
import threading
from app.config import config

class ResourceGuard:
    def __init__(self):
        self.max_ram_mb = config.MAX_RAM_MB
        self.max_cpu_percent = config.MAX_CPU_PERCENT
        self.max_storage_mb = config.MAX_STORAGE_MB
        self.current_requests = 0
        self.lock = threading.Lock()
    
    def check_resources(self):
        # ... (codice dal messaggio precedente)
        pass

resource_guard = ResourceGuard()