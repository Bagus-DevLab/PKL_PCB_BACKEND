import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from app.core.request_context import RequestIdFilter

# 1. Konfigurasi Dasar
LOG_DIR = "logs"
LOG_FILENAME = "backend.log"
# Format log sekarang include [request_id] untuk tracing setiap request
LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(name)s] - [%(request_id)s] - %(message)s"

def setup_logging():
    """
    Mengatur sistem logging agar output ke:
    1. Terminal (Console) -> Biar enak dilihat pas dev.
    2. File (logs/backend.log) -> Biar ada rekam jejak abadi.
    
    Setiap log otomatis punya request_id untuk tracing.
    """
    
    # Buat folder 'logs' kalau belum ada
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    filepath = os.path.join(LOG_DIR, LOG_FILENAME)

    # Ambil Root Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # Level: DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Cek biar handler gak dobel (kalau reload)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Tambahkan filter request_id ke root logger
    # Ini otomatis inject request_id ke SEMUA log di seluruh app
    request_id_filter = RequestIdFilter()
    logger.addFilter(request_id_filter)

    # --- HANDLER 1: FILE (Rotating) ---
    # File akan dipotong kalau ukurannya > 5MB, simpan 3 backup terakhir.
    file_handler = RotatingFileHandler(filepath, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)

    # --- HANDLER 2: CONSOLE (Terminal) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)

    return logger