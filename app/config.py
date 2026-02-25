class Config:
    # Limiti di sicurezza (80% delle risorse totali)
    MAX_RAM_MB = 7000
    MAX_CPU_PERCENT = 300
    MAX_STORAGE_MB = 9000
    
    # Limiti utente
    MAX_FILE_SIZE_MB = 50
    MAX_FILE_DURATION_SEC = 45
    MAX_CONCURRENT_REQUESTS = 2
    
    # Spleeter
    SPLEETER_MODEL = "spleeter:2stems"
    
    # Pulizia
    FILE_RETENTION_MINUTES = 30
    CLEANUP_INTERVAL_HOURS = 1
    
    # Path
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "outputs"
    LOG_DIR = "logs"

config = Config()