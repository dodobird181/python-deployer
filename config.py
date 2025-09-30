import json
import subprocess
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class Config:
    """
    Python representation of the config file.
    """

    class InvalidConfig(Exception):
        """The config contains some invalid formatting or data."""

        ...

    @dataclass
    class App:
        """
        An app to be deployed.
        """

        name: str
        endpoint: str
        run_args: List[str]

    @dataclass
    class Gunicorn:
        """
        Gunicorn options.
        """

        app_name: str
        options: Dict[str, Any]

    apps: List[App]
    logdir: str
    max_email_payload_bytes: int
    api_secret: str
    gunicorn: Gunicorn

    def __str__(self) -> str:
        return "<Config: apps={}, logdir={}, max_email_payload_bytes={}, api_secret={}>".format(
            self.apps, self.logdir, self.max_email_payload_bytes, "*****"
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["api_secret"] = "*****"
        return d


def load_config(config_path="config.yaml") -> Config:
    try:
        result = subprocess.run(["yq", "-e", "-o=json", ".", config_path], capture_output=True)
        data = json.loads(result.stdout)["config"]
        return Config(
            logdir=data["logs"]["dir"],
            max_email_payload_bytes=data["security"]["max_payload_bytes"],
            api_secret=data["security"]["api_secret"],
            apps=[
                Config.App(
                    name=app["name"],
                    endpoint=app["endpoint"],
                    run_args=app["run_args"],
                )
                for app in data["apps"]
            ],
            gunicorn=Config.Gunicorn(
                app_name=data["gunicorn"]["app_name"],
                options=data["gunicorn"]["run_args"],
            ),
        )
    except (KeyError, ValueError) as e:
        raise Config.InvalidConfig from e
