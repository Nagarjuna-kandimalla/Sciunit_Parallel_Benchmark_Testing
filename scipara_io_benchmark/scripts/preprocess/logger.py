import logging
import os

from paths import PROJECT_ROOT

LOG_FILE = PROJECT_ROOT / "logs" / "preprocess" / "preprocessing.log"


def get_logger(name: str):
    os.makedirs(LOG_FILE.parent, exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # prevent duplicate handlers

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
