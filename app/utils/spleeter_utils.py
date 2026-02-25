import subprocess
import os
import shutil
from fastapi import HTTPException
from app.config import config

def separate_stems(input_path, output_folder, file_id):
    """Esegue Spleeter con modello configurato"""
    cmd = [
        "spleeter", "separate",
        "-p", config.SPLEETER_MODEL,
        "-o", output_folder,
        input_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise Exception(f"Spleeter error: {result.stderr}")
        
        # Trova la cartella generata
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        stem_folder = os.path.join(output_folder, base_name)
        
        if not os.path.exists(stem_folder):
            raise Exception("Stem folder not found")
        
        return stem_folder
        
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Spleeter timeout")
    except Exception as e:
        raise HTTPException(500, str(e))

def create_zip(stem_folder, zip_path):
    """Crea zip dagli stems"""
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', stem_folder)
    return zip_path