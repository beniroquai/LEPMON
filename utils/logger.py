# lepmon/utils/logger.py
import logging
import os
from datetime import datetime

def init_logger(log_path):
    """
    Configure Python's logging system to write to a file and optionally to console
    """
    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s; %(levelname)s; %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Also attach a console handler if you want
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger("").addHandler(console)

def write_log(msg, level="info"):
    if level == "info":
        logging.info(msg)
    elif level == "error":
        logging.error(msg)
    # etc.
