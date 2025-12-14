import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = os.path.expanduser("~/.rag_mcp/logs")

def setup_logger(name: str = "rag_mcp"):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
        
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File Handler (Rotating)
        log_file = os.path.join(LOG_DIR, "rag_mcp.log")
        file_handler = TimedRotatingFileHandler(
            log_file, when="D", interval=1, backupCount=7, encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
    return logger

logger = setup_logger()
