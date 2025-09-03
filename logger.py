import logging
import subprocess
import sys
from logging.handlers import TimedRotatingFileHandler

from args import get_arguments
from config import Config


def logger_from_config(config: Config) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(get_arguments().log_level)
    subprocess.run(["mkdir", "-p", config.logdir], capture_output=True, check=True)
    file_handler = TimedRotatingFileHandler(
        f"{config.logdir}/log.txt",
        when="midnight",  # rotate once per month at midnight
        interval=30,  # ~monthly rotation (in days)
        backupCount=12,  # Keep a year's worth of backups
        utc=True,
    )
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d_%I-%M-%S_%p_%Z%z",
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
