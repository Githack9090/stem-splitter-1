import subprocess
import os
from fastapi import HTTPException

def trim_audio(input_path, output_path, max_duration):
    """Taglia file audio con ffmpeg"""
    cmd = [
        "ffmpeg", "-i", input_path,
        "-t", str(max_duration),
        "-c", "copy", output_path, "-y"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise HTTPException(500, f"FFmpeg error: {result.stderr}")
        return output_path
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "FFmpeg timeout")
    except Exception as e:
        raise HTTPException(500, str(e))

def validate_audio_file(filename: str):
    """Valida estensione file"""
    allowed = ('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg')
    if not filename.lower().endswith(allowed):
        raise HTTPException(400, f"Formato non supportato. Usa: {allowed}")
    return True