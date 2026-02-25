"""
Modulo per il monitoraggio del traffico mensile.
Tiene traccia dei byte trasferiti (upload + download) e resetta automaticamente ogni mese.
I dati sono salvati su disco per persistere tra riavvii dell'applicazione.
"""

import os
import json
import time
from datetime import datetime
from typing import Optional

class TrafficMonitor:
    """
    Monitora il traffico mensile per rispettare il limite di 10GB.
    I dati vengono salvati in un file JSON per persistere tra riavvii.
    """
    
    def __init__(self, max_gb_per_month: float = 10.0, state_file: str = "traffic_state.json"):
        """
        Inizializza il monitor del traffico.
        
        Args:
            max_gb_per_month: Limite massimo di traffico in GB (default: 10.0)
            state_file: Percorso del file dove salvare lo stato
        """
        self.max_bytes = int(max_gb_per_month * 1024 * 1024 * 1024)  # Converti GB in bytes
        self.state_file = state_file
        self.used_bytes = 0
        self.month_start = time.time()
        self.load_state()
    
    def load_state(self) -> None:
        """
        Carica lo stato dal file JSON.
        Se il file non esiste o è corrotto, inizializza con valori predefiniti.
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.used_bytes = data.get('used_bytes', 0)
                    self.month_start = data.get('month_start', time.time())
                    
                    # Verifica se è iniziato un nuovo mese
                    self._check_month_reset()
                    
                print(f"📊 TrafficMonitor: caricato stato - Usati: {self.used_bytes/(1024**3):.2f}GB, "
                      f"Mese iniziato: {time.strftime('%Y-%m-%d', time.localtime(self.month_start))}")
            except Exception as e:
                print(f"⚠️ TrafficMonitor: errore nel caricamento dello stato ({e}), uso valori predefiniti")
                self._reset_month()
        else:
            print("📊 TrafficMonitor: nessuno stato precedente trovato, partenza da zero")
            self._reset_month()
    
    def save_state(self) -> None:
        """
        Salva lo stato corrente su file JSON.
        """
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'used_bytes': self.used_bytes,
                    'month_start': self.month_start,
                    'last_update': time.time()
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ TrafficMonitor: errore nel salvataggio dello stato ({e})")
    
    def _reset_month(self) -> None:
        """Resetta i contatori per un nuovo mese."""
        self.used_bytes = 0
        self.month_start = time.time()
        self.save_state()
        print(f"🔄 TrafficMonitor: nuovo mese iniziato il {time.strftime('%Y-%m-%d', time.localtime(self.month_start))}")
    
    def _check_month_reset(self) -> bool:
        """
        Verifica se è iniziato un nuovo mese e resetta i contatori se necessario.
        
        Returns:
            True se è stato fatto un reset, False altrimenti
        """
        now = time.time()
        # 30 giorni in secondi (approssimazione di un mese)
        month_seconds = 30 * 24 * 3600
        
        if now - self.month_start > month_seconds:
            print(f"🔄 TrafficMonitor: reset mensile automatico - Mese precedente: {self.used_bytes/(1024**3):.2f}GB")
            self._reset_month()
            return True
        return False
    
    def add_traffic(self, upload_bytes: int, download_bytes: int) -> None:
        """
        Aggiunge traffico al contatore mensile.
        
        Args:
            upload_bytes: Byte caricati (upload)
            download_bytes: Byte scaricati (download)
        """
        # Verifica reset mensile
        self._check_month_reset()
        
        # Aggiungi traffico
        self.used_bytes += (upload_bytes + download_bytes)
        
        # Salva stato
        self.save_state()
        
        # Log di warning se ci avviciniamo al limite
        usage_percent = self.get_usage_percent()
        if usage_percent > 90:
            print(f"⚠️ ATTENZIONE: Traffico al {usage_percent:.1f}% del limite mensile ({self.used_bytes/(1024**3):.2f}/{self.max_bytes/(1024**3):.1f}GB)")
        elif usage_percent > 75:
            print(f"📈 Traffico al {usage_percent:.1f}% del limite mensile")
    
    def is_limit_reached(self) -> bool:
        """
        Verifica se il limite di traffico mensile è stato raggiunto.
        
        Returns:
            True se il limite è stato raggiunto, False altrimenti
        """
        # Se è iniziato un nuovo mese, il limite non è raggiunto
        if self._check_month_reset():
            return False
        return self.used_bytes >= self.max_bytes
    
    def get_usage_percent(self) -> float:
        """
        Restituisce la percentuale di traffico utilizzata.
        
        Returns:
            Percentuale di utilizzo (0-100)
        """
        # Se è iniziato un nuovo mese, percentuale = 0
        if self._check_month_reset():
            return 0.0
        return (self.used_bytes / self.max_bytes) * 100
    
    def get_remaining_bytes(self) -> int:
        """
        Restituisce i byte rimanenti nel limite mensile.
        
        Returns:
            Byte ancora disponibili (0 se il limite è raggiunto)
        """
        if self.is_limit_reached():
            return 0
        return self.max_bytes - self.used_bytes
    
    def get_stats(self) -> dict:
        """
        Restituisce statistiche complete sul traffico.
        
        Returns:
            Dizionario con tutte le statistiche
        """
        return {
            "limit_gb": round(self.max_bytes / (1024**3), 1),
            "used_gb": round(self.used_bytes / (1024**3), 2),
            "used_percent": round(self.get_usage_percent(), 1),
            "remaining_gb": round(self.get_remaining_bytes() / (1024**3), 2),
            "month_start": time.strftime('%Y-%m-%d', time.localtime(self.month_start)),
            "limit_reached": self.is_limit_reached()
        }

# Istanza globale del monitor (singleton)
traffic_monitor = TrafficMonitor()

# Esporta esplicitamente ciò che serve
__all__ = ['traffic_monitor']
