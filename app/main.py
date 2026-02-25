from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import shutil
from datetime import datetime

from app.config import config
from app.resource_guard import resource_guard
from app.storage_manager import storage_manager
from app.auto_cleaner import auto_cleaner
from app.resource_monitor import monitor
from app.utils.file_utils import trim_audio, validate_audio_file
from app.utils.spleeter_utils import separate_stems, create_zip

app = FastAPI(title="Stem Splitter API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware protezione risorse
@app.middleware("http")
async def resource_protection_middleware(request, call_next):
    if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    ok, message = resource_guard.check_resources()
    if not ok:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Server temporarily unavailable",
                "reason": message,
                "retry_after": 60
            }
        )
    
    response = await call_next(request)
    return response

# Endpoints
@app.get("/")
async def root():
    return {
        "message": "Stem Splitter API",
        "status": "online",
        "version": "1.0",
        "limits": {
            "max_file_size_mb": config.MAX_FILE_SIZE_MB,
            "max_duration_sec": config.MAX_FILE_DURATION_SEC,
            "model": config.SPLEETER_MODEL
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "resources": {
            "ram_mb": resource_guard.current_requests
        }
    }

@app.post("/separate")
async def separate_audio(file: UploadFile = File(...)):
    with resource_guard:
        # Validazioni
        validate_audio_file(file.filename)
        
        file_id = str(uuid.uuid4())
        input_path = None
        trimmed_path = None
        zip_path = None
        
        try:
            # Salva file
            input_path = await storage_manager.safe_save_upload(file, file_id)
            
            # Taglia a durata massima
            trimmed_path = os.path.join(
                config.UPLOAD_DIR, 
                f"{file_id}_trimmed.mp3"
            )
            trim_audio(input_path, trimmed_path, config.MAX_FILE_DURATION_SEC)
            
            # Prepara output
            output_folder = os.path.join(config.OUTPUT_DIR, file_id)
            os.makedirs(output_folder, exist_ok=True)
            
            # Separa stems
            stem_folder = separate_stems(trimmed_path, output_folder, file_id)
            
            # Crea zip
            zip_path = os.path.join(config.OUTPUT_DIR, f"{file_id}.zip")
            create_zip(stem_folder, zip_path)
            
            # Pulizia file temporanei (tranne zip)
            os.remove(trimmed_path)
            os.remove(input_path)
            shutil.rmtree(stem_folder)
            
            monitor.metrics['requests_count'] += 1
            
            return FileResponse(
                zip_path, 
                filename="stems.zip",
                media_type="application/zip"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, str(e))
        finally:
            # Pulizia di emergenza
            for f in [input_path, trimmed_path]:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass

@app.get("/admin/metrics")
async def get_metrics():
    # In produzione aggiungi autenticazione!
    return {
        "current": {
            "ram_mb": resource_guard.current_requests,  # placeholder
            "concurrent_requests": resource_guard.current_requests,
            "storage_mb": storage_manager.get_current_usage()
        },
        "history": monitor.metrics,
        "limits": {
            "max_ram_mb": resource_guard.max_ram_mb,
            "max_storage_mb": resource_guard.max_storage_mb,
            "max_concurrent": config.MAX_CONCURRENT_REQUESTS
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    # Avvia cleaner automatico
    await auto_cleaner.start()
    
    # Crea directory necessarie
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.LOG_DIR, exist_ok=True)