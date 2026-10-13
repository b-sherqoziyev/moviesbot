import logging
import sys
from app.core.config import settings


def setup_logger(name: str = "moviesbot") -> logging.Logger:
    """Tizim uchun strukturalashtirilgan logger yaratish."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
