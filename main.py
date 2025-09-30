import hashlib
import hmac
import subprocess
import time
from datetime import datetime
from uuid import uuid4

import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config, load_config
from logger import logger_from_config
from utils import request_to_sanitized_json

app = flask.Flask(__name__)
config = load_config()
logger = logger_from_config(config)

# Attach rate-limiter
limiter = Limiter(
    get_remote_address,  # identify clients by IP
    app=app,
    default_limits=["200 per day", "50 per hour"],
)


def now() -> datetime:
    return datetime.now().astimezone()


# Custom error handler for all HTTP exceptions.
@app.errorhandler(Exception)
def handle_exception(e):
    """
    Transform all exceptions from 'flask.abort' to JSON error responses.
    """
    # If it's an HTTPException, use its code; otherwise 500
    code = getattr(e, "code", 500)
    return flask.jsonify(error=str(e), code=code, success=False), code


def _abort_if_payload_too_large() -> None:
    """
    Abort request if the content is too large.
    """
    max_bytes = config.max_email_payload_bytes
    content_length = flask.request.content_length if flask.request.content_length else 0
    if content_length > max_bytes:
        logger.warning(
            "Rejected request with payload = {} KB > {} KB: {}.".format(
                content_length / 1000,
                max_bytes / 1000,
                request_to_sanitized_json(flask.request),
            )
        )
        flask.abort(413, description="Payload too large.")


def _abort_if_invalid_signature() -> None:
    """
    Abort if the request is missing auth headers, it's timestamp is too old, or it has an invalid signature.
    """
    signature = flask.request.headers.get("X-Signature")
    timestamp = flask.request.headers.get("X-Timestamp")
    body = flask.request.get_data(as_text=True)

    if not signature or not timestamp:
        logger.warning(
            "Rejected request because it was missing 'X-Signature': '{}', or 'X-Timestamp': '{}'. Request: {}".format(
                signature,
                timestamp,
                request_to_sanitized_json(flask.request),
            )
        )
        flask.abort(403, "Missing auth header(s). Make sure you're sending 'X-Signature' and 'X-Timestamp'.")

    # Check timestamp is from the last 5 minutes
    if abs(time.time() - int(timestamp)) > 300:
        logger.warning(
            "Rejected request with timestamp '{}' because it's too old. Request: {}.".format(
                timestamp,
                request_to_sanitized_json(flask.request),
            )
        )
        flask.abort(403, "Too old.")

    # Compute the expected request signature and compare
    message = timestamp + body
    secret_bytes = config.api_secret.encode("utf-8")
    expected_sig = hmac.new(secret_bytes, message.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        logger.warning(
            "Rejected request with invalid signature. Request: {}.".format(
                request_to_sanitized_json(flask.request),
            )
        )
        flask.abort(403, "Invalid Signature.")


@app.route("/", methods=["GET"])
def index():
    return flask.Response("Python-Deployer v1.0.", status=200)


for deploy_app in config.apps:

    def make_route(_deploy_app: Config.App):
        def handler():

            _abort_if_payload_too_large()
            _abort_if_invalid_signature()

            start = now()
            try:
                logger.info(
                    f"Starting deploy for '{_deploy_app.name}' using \"{' '.join(_deploy_app.run_args)}\"..."
                )
                with subprocess.Popen(
                    _deploy_app.run_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                ) as proc:
                    if proc.stdout:
                        for line in proc.stdout:
                            logger.info(f"<{_deploy_app.name}> {line.strip()}")
                    if proc.stderr:
                        for line in proc.stderr:
                            # some processes use stderr for normal logging. Try to interpret what
                            # they are saying and also rely on exit_code for failure condition.
                            if "error" in line.lower() or "failed" in line.lower():
                                logger.error(f"<{_deploy_app.name}> {line.strip()}")
                            else:
                                logger.info(f"<{_deploy_app.name}> {line.strip()}")
                    exit_code = proc.wait()
                    if exit_code == -15:
                        logger.warning(
                            "Subprocess killed by SIGTERM — likely due to service restart. Did python-deployer just deploy itself?"
                        )
                    elif exit_code != 0:
                        raise Exception(f"Subprocess exited with code: {exit_code}!")

                elapsed = now().timestamp() - start.timestamp()
                message = f"Deployment for {_deploy_app.name} succeeded in {elapsed:.2f} seconds."
                return flask.jsonify({"success": True, "message": message}), 200

            except Exception as e:
                elapsed = now().timestamp() - start.timestamp()
                logger.error(f"Failed to deploy app: {_deploy_app.name}.", exc_info=e)
                message = f"Deployment failed after {elapsed:.2f} seconds."
                return flask.jsonify({"success": False, "message": message}), 500

        # give the function a unique name
        handler.__name__ = f"handler_{uuid4().hex}"
        app.route(_deploy_app.endpoint, methods=["POST"])(handler)

    make_route(deploy_app)
    logger.debug(f"Created API route for '{deploy_app.name} @ {deploy_app.endpoint} --> {deploy_app.run_args}'")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
