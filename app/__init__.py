# Pacchetto principale dell'applicazione
# Questo file può essere vuoto, ma lo useremo per esporre le funzioni principali

from app.config import config
from app.resource_guard import resource_guard
from app.storage_manager import storage_manager
from app.auto_cleaner import auto_cleaner
from app.resource_monitor import monitor

__all__ = [
    'config',
    'resource_guard',
    'storage_manager',
    'auto_cleaner',
    'monitor'
]