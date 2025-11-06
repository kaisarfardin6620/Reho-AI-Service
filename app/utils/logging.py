import sys
from pathlib import Path
from loguru import logger

def setup_logging():
    # Remove default logger
    logger.remove()
    
    # Log format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Console handler with color
    logger.add(
        sys.stdout,
        format=log_format,
        level="INFO",
        colorize=True
    )
    
    # File handler for errors
    log_path = Path("logs/error.log")
    log_path.parent.mkdir(exist_ok=True)
    
    logger.add(
        log_path,
        format=log_format,
        level="ERROR",
        rotation="500 MB",
        compression="zip",
        retention="30 days"
    )
    
    # File handler for all logs
    logger.add(
        "logs/app.log",
        format=log_format,
        level="DEBUG",
        rotation="100 MB",
        compression="zip",
        retention="7 days"
    )

    return logger