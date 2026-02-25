import asyncio
import os
import shutil
from datetime import datetime, timedelta
from app.config import config

class AutoCleaner:
    def __init__(self):
        self.cleanup_task = None
        self.upload_dir = config.UPLOAD_DIR
        self.output_dir = config.OUTPUT_DIR
        self.retention_minutes = config.FILE_RETENTION_MINUTES
    
    async def start(self):
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(3600)  # 1 ora
            try:
                await self._cleanup_old_files()
            except Exception as e:
                print(f"Cleanup error: {e}")
    
    async def _cleanup_old_files(self):
        now = datetime.now()
        cutoff = now - timedelta(minutes=self.retention_minutes)
        
        for folder in [self.upload_dir, self.output_dir]:
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    fpath = os.path.join(folder, f)
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                    if mtime < cutoff:
                        if os.path.isfile(fpath):
                            os.remove(fpath)
                        elif os.path.isdir(fpath):
                            shutil.rmtree(fpath)
                        print(f"Pulito: {fpath}")

auto_cleaner = AutoCleaner()