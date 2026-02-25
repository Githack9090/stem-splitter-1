from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import shutil
import time
from datetime import datetime

# Import dei moduli interni
from app.config import config
from app.resource_guard import resource_guard
from app.storage_manager import storage_manager
from app.auto_cleaner import auto_cleaner
from app.resource_monitor import monitor
from app.traffic_monitor import traffic_monitor
from app.utils.file_utils import trim_audio, validate_audio_file
from app.utils.spleeter_utils import separate_stems, create_zip

# Inizializzazione app FastAPI
app = FastAPI(
    title="Stem Splitter API",
    description="API per separazione tracce audio in stems (voce, batteria, basso, altri)",
    version="1.0.0"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# MIDDLEWARE DI PROTEZIONE RISORSE E TRAFFICO
# ============================================
@app.middleware("http")
async def resource_protection_middleware(request, call_next):
    # Lista degli endpoint pubblici (senza protezione)
    public_endpoints = [
        "/", 
        "/health", 
        "/docs", 
        "/openapi.json", 
        "/redoc",
        "/admin/metrics", 
        "/admin/traffic"
    ]
    
    # Se è un endpoint pubblico, passa direttamente
    if request.url.path in public_endpoints:
        return await call_next(request)
    
    # 1. Controllo risorse di sistema (RAM/CPU)
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
    
    # 2. Controllo traffico mensile (limite 10GB)
    if traffic_monitor.is_limit_reached():
        return JSONResponse(
            status_code=503,
            content={
                "error": "Monthly traffic limit reached",
                "message": "Il limite mensile di 10GB è stato raggiunto. Riprova il mese prossimo.",
                "usage_percent": traffic_monitor.get_usage_percent()
            }
        )
    
    # Se tutti i controlli sono superati, procedi
    response = await call_next(request)
    return response

# ============================================
# ENDPOINT: ROOT
# ============================================
@app.get("/")
async def root():
    """
    Endpoint principale con informazioni sull'API
    """
    return {
        "message": "Stem Splitter API",
        "status": "online",
        "version": "1.0",
        "limits": {
            "max_file_size_mb": config.MAX_FILE_SIZE_MB,
            "max_duration_sec": config.MAX_FILE_DURATION_SEC,
            "model": config.SPLEETER_MODEL
        },
        "documentation": "/docs"
    }

# ============================================
# ENDPOINT: HEALTH CHECK
# ============================================
@app.get("/health")
async def health():
    """Health check per monitoraggio"""
    # Calcola RAM in modo sicuro
    ram_mb = 0
    try:
        # Se resource_guard ha un metodo per ottenere RAM, usalo
        if hasattr(resource_guard, 'get_current_ram_mb'):
            ram_mb = resource_guard.get_current_ram_mb()
        else:
            # Altrimenti usa psutil direttamente
            import psutil
            ram_mb = psutil.virtual_memory().used / (1024 * 1024)
    except:
        pass  # Se fallisce, lascia 0
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "resources": {
            "current_requests": resource_guard.current_requests,
            "ram_mb": ram_mb
        }
    }
# ============================================
# ENDPOINT: SEPARAZIONE AUDIO
# ============================================
@app.post("/separate")
async def separate_audio(file: UploadFile = File(...)):
    """
    Endpoint principale per la separazione delle tracce audio.
    - Accetta un file audio
    - Valida dimensioni e formato
    - Separa in stems (voce, batteria, basso, altri)
    - Restituisce uno zip con tutti i file
    """
    # === CONTEXT MANAGER PER RICHIESTE CONCORRENTI ===
    with resource_guard:
        
        # === 1. VALIDAZIONI PRELIMINARI ===
        validate_audio_file(file.filename)
        
        # === 2. LETTURA FILE E CALCOLO DIMENSIONI ===
        try:
            file_content = await file.read()
            upload_size = len(file_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Errore nella lettura del file: {str(e)}")
        
        if upload_size == 0:
            raise HTTPException(status_code=400, detail="Il file è vuoto")
        
        # === 3. PREPARAZIONE ID E PATH ===
        file_id = str(uuid.uuid4())
        input_path = None
        trimmed_path = None
        zip_path = None
        stem_folder = None
        
        try:
            # === 4. SALVATAGGIO FILE ORIGINALE ===
            input_path = await storage_manager.safe_save_upload_bytes(
                file_content=file_content,
                original_filename=file.filename,
                file_id=file_id
            )
            
            # === 5. TAGLIO A DURATA MASSIMA ===
            trimmed_path = os.path.join(
                config.UPLOAD_DIR, 
                f"{file_id}_trimmed.mp3"
            )
            trim_audio(input_path, trimmed_path, config.MAX_FILE_DURATION_SEC)
            
            # === 6. PREPARAZIONE OUTPUT ===
            output_folder = os.path.join(config.OUTPUT_DIR, file_id)
            os.makedirs(output_folder, exist_ok=True)
            
            # === 7. SEPARAZIONE SPLEETER ===
            stem_folder = separate_stems(
                input_path=trimmed_path, 
                output_folder=output_folder, 
                file_id=file_id
            )
            
            # === 8. CREAZIONE ZIP ===
            zip_path = os.path.join(config.OUTPUT_DIR, f"{file_id}.zip")
            create_zip(stem_folder, zip_path)
            zip_size = os.path.getsize(zip_path)
            
            # === 9. PULIZIA FILE INTERMEDI ===
            if os.path.exists(trimmed_path):
                os.remove(trimmed_path)
            if os.path.exists(input_path):
                os.remove(input_path)
            if stem_folder and os.path.exists(stem_folder):
                shutil.rmtree(stem_folder)
            
            # === 10. AGGIORNAMENTO METRICHE ===
            monitor.metrics['requests_count'] += 1
            traffic_monitor.add_traffic(upload_size, zip_size)
            
            print(f"✅ Richiesta {file_id} completata. Upload: {upload_size/1024:.1f}KB, Download: {zip_size/1024:.1f}KB")
            
            # === 11. INVIO ZIP ===
            return FileResponse(
                zip_path, 
                filename="stems.zip",
                media_type="application/zip",
                headers={
                    "X-Traffic-Usage": f"{traffic_monitor.get_usage_percent():.1f}%",
                    "X-Request-ID": file_id
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Errore nella richiesta {file_id}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Errore durante l'elaborazione: {str(e)}"
            )
            
        finally:
            # === 12. PULIZIA DI EMERGENZA ===
            # Rimuovi solo i file che non sono lo zip (lo zip verrà pulito dopo l'invio)
            for file_path in [input_path, trimmed_path]:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"⚠️ Errore nella pulizia di {file_path}: {e}")

# ============================================
# ENDPOINT: METRICHE DI SISTEMA
# ============================================
@app.get("/admin/metrics")
async def get_metrics():
    """Metriche dettagliate del sistema (solo per admin)"""
    # Calcola RAM in modo sicuro
    ram_mb = 0
    try:
        if hasattr(resource_guard, 'get_current_ram_mb'):
            ram_mb = resource_guard.get_current_ram_mb()
        else:
            import psutil
            ram_mb = psutil.virtual_memory().used / (1024 * 1024)
    except:
        pass
    
    return {
        "current": {
            "ram_mb": ram_mb,
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

# ============================================
# ENDPOINT: STATISTICHE TRAFFICO
# ============================================
@app.get("/admin/traffic")
async def get_traffic_stats():
    """
    Statistiche traffico mensile (solo per admin)
    """
    return {
        "limit_gb": 10,
        "used_gb": round(traffic_monitor.used_bytes / (1024**3), 2),
        "used_percent": round(traffic_monitor.get_usage_percent(), 1),
        "remaining_gb": round((10 - (traffic_monitor.used_bytes / (1024**3))), 2),
        "month_start": time.strftime('%Y-%m-%d', time.localtime(traffic_monitor.month_start))
    }

# ============================================
# STARTUP EVENT
# ============================================
@app.on_event("startup")
async def startup_event():
    """
    Operazioni all'avvio dell'applicazione
    """
    # Avvia cleaner automatico
    await auto_cleaner.start()
    
    # Crea directory necessarie
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.LOG_DIR, exist_ok=True)
    
    print(f"🚀 Stem Splitter API avviata - PID: {os.getpid()}")
    print(f"📊 Limiti: File max {config.MAX_FILE_SIZE_MB}MB, Durata max {config.MAX_DURATION_SEC}s, Modello {config.SPLEETER_MODEL}")
    print(f"📈 Traffico mensile: 10GB (attuale: {traffic_monitor.used_bytes/(1024**3):.2f}GB)")

# ============================================
# SHUTDOWN EVENT
# ============================================
@app.on_event("shutdown")
async def shutdown_event():
    """
    Operazioni allo spegnimento dell'applicazione
    """
    print("🛑 Stem Splitter API in arresto...")
    # Salva stato traffico
    traffic_monitor.save_state()
    print("✅ Stato salvato")
