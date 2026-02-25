import os
import time
import aiofiles
import shutil
from pathlib import Path
from fastapi import HTTPException
from app.config import config

class StorageManager:
    def __init__(self):
        self.max_total_mb = config.MAX_STORAGE_MB
        self.max_file_mb = config.MAX_FILE_SIZE_MB
        self.max_duration_sec = config.MAX_FILE_DURATION_SEC
        self.upload_dir = config.UPLOAD_DIR
        self.output_dir = config.OUTPUT_DIR
        
        # Crea le directory se non esistono
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def safe_save_upload(self, file, file_id):
        # ... (codice dal messaggio precedente)
        pass
    
    async def emergency_cleanup(self):
        # ... (codice dal messaggio precedente)
        pass
    
    def get_current_usage(self):
        # ... (codice dal messaggio precedente)
        pass

storage_manager = StorageManager()