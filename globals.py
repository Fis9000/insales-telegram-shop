from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import psycopg2

def get_logger(name: str, log_file: str, logs_dir: str = "logs") -> logging.Logger:
    """Логи"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Путь к общей папке логов
        log_path = Path(logs_dir) / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)  # Создать папку при необходимости

        handler = RotatingFileHandler(
            log_path,
            maxBytes=1*1024*1024,
            backupCount=0,
            encoding="utf-8"
        )
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
