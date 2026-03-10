import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from app.core.request_context import RequestIdFilter

# 1. Konfigurasi Dasar
LOG_DIR = "logs"
LOG_FILENAME = "backend.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(name)s] - [%(request_id)s] - %(message)s"

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    request_id_filter = RequestIdFilter()
    # HAPUS BARIS INI: logger.addFilter(request_id_filter) 

    # --- HANDLER 1: FILE (Rotating) ---
    filepath = os.path.join(LOG_DIR, LOG_FILENAME)
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)
            
        file_handler = RotatingFileHandler(filepath, maxBytes=5*1024*1024, backupCount=3)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, defaults={"request_id": "SYSTEM"}))
        
        # TAMBAHKAN FILTER DI SINI
        file_handler.addFilter(request_id_filter) 
        logger.addHandler(file_handler)
        
    except PermissionError:
        print(f"Warning: Permission denied to write to {filepath}. File logging is disabled.")
    except Exception as e:
        print(f"Warning: Failed to setup file logger: {e}")

    # --- HANDLER 2: CONSOLE (Terminal) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, defaults={"request_id": "SYSTEM"}))
    
    # TAMBAHKAN FILTER DI SINI
    console_handler.addFilter(request_id_filter) 
    
    # KELUPAAN DI KODE SEBELUMNYA, TAMBAHKAN HANDLER KE LOGGER
    logger.addHandler(console_handler) 

    return logger