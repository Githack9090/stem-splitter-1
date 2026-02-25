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

class TrafficMonitor:
    def __init__(self, max_gb_per_month=10):
        self.max_bytes = max_gb_per_month * 1024 * 1024 * 1024  # 10 GB in bytes
        self.used_bytes = 0
        self.month_start = time.time()
        # In un'implementazione reale, dovresti salvare questi dati su disco/db
        
    def add_traffic(self, upload_bytes, download_bytes):
        """Aggiunge traffico e controlla se si supera il limite"""
        self.used_bytes += (upload_bytes + download_bytes)
        
        # Se superiamo il 90% del limite, logga un avviso
        if self.used_bytes > self.max_bytes * 0.9:
            print(f"⚠️ ATTENZIONE: Traffico al {self.used_bytes/self.max_bytes*100:.1f}% del limite mensile")
            
    def is_limit_reached(self):
        """Restituisce True se abbiamo superato il limite"""
        return self.used_bytes >= self.max_bytes

monitor = ResourceMonitor()
