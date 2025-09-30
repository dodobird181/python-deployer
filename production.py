from __future__ import unicode_literals

import json
import logging
import re
import sys
from dataclasses import asdict

from gunicorn.app.base import BaseApplication

from main import app as flask_app
from main import config, logger

"""
Entrypoint for running the app as a Gunicorn process that does three main things:
    1. Wraps main.py's Flask app in a Gunicorn process;
    2. Overrides any Gunicorn config vars with the values in `config.gunicorn.run_args`; and,
    3. Normalizes Gunicorn logs and sends them to the Python logger.
"""


class StreamToLoggerFromGunicornProcess:
    """
    Stream-like object that takes messages that gunicorn writes to the buffer, parses them,
    and sends them to the Python logger for console output and logging to the app's logfile.
    """

    def __init__(self):
        self._buffer = ""

    def write(self, message):
        message = message.rstrip()
        if message:

            # Remove Gunicorn's timestamp like "[2025-09-03 17:17:55 -0400]"
            message = re.sub(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}\]", "", message)

            # Remove Apache-style timestamp [03/Sep/2025:17:53:48 -0400], which come from gunicorn workers logging requests
            message = re.sub(r"\[(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})\]", "", message)

            # Replace any PID like [82608] with (worker_pid: 82608)
            message = re.sub(r"\[(\d+)\]", r"(worker_pid: \1)", message)

            def _log(level: int, gunicorn_level_txt: str) -> None:
                """
                Inner log function that removes the gunicorn log level text and normalizes whitespace
                by splitting on any whitespace and re-joining with a single space.
                """
                msg = " ".join(message.replace(gunicorn_level_txt, "").split())
                logger.log(level=level, msg=msg)

            # Simple heuristic to determine what level to log gunicorn messages at.
            gunicorn_levels = {
                logging.DEBUG: "[DEBUG]",
                logging.INFO: "[INFO]",
                logging.WARNING: "[WARNING]",
                logging.ERROR: "[ERROR]",
            }
            logged = False
            for level, gunicorn_level_txt in gunicorn_levels.items():
                if gunicorn_level_txt in message:
                    _log(level, gunicorn_level_txt)
                    logged = True
                    break
            if logged == False:
                # Default to INFO since gunicorn workers don't have any prefix when logging requests
                _log(logging.INFO, "")

    def flush(self):
        pass  # needed for file-like interface


class GunicornApp(BaseApplication):
    """
    Gunicorn app wrapper for Flask that inherits `gunicorn.options` from the `config.yaml` file.
    """

    def __init__(self, app):
        self.application = app
        super(GunicornApp, self).__init__()

    def load_config(self):
        # Keep any configuration from the base class instance and add options from config.yaml.
        for key, value in config.gunicorn.options.items():
            self.cfg.set(key.lower(), value)  # type: ignore

    def load(self):
        return self.application


if __name__ == "__main__":
    logger.debug(
        "Starting gunicorn app '{}' for production environment with options: {}".format(
            config.gunicorn.app_name,
            json.dumps(asdict(config), indent=2),
        )
    )
    sys.stdout = StreamToLoggerFromGunicornProcess()
    sys.stderr = StreamToLoggerFromGunicornProcess()
    GunicornApp(flask_app).run()
