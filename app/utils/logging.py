import sys
from pathlib import Path
from loguru import logger

def setup_logging():
    logger.remove()
    
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        format=log_format,
        level="INFO",
        colorize=True
    )
    
    try:
        log_path = Path("logs/error.log")
        
        if not log_path.parent.exists():
            log_path.parent.mkdir(exist_ok=True, parents=True)
        
        logger.add(
            log_path,
            format=log_format,
            level="ERROR",
            rotation="500 MB",
            compression="zip",
            retention="30 days"
        )
        
        logger.add(
            "logs/app.log",
            format=log_format,
            level="DEBUG",
            rotation="100 MB",
            compression="zip",
            retention="7 days"
        )
    except PermissionError:
        print("⚠️  WARNING: Insufficient permissions to create 'logs' directory. File logging disabled (Console only).")
    except Exception as e:
        print(f"⚠️  WARNING: Failed to setup file logging: {e}")

    return logger