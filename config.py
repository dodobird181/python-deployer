import json
import subprocess
from dataclasses import dataclass
from typing import List


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

    apps: List[App]
    logdir: str
    max_email_payload_bytes: int
    api_secret: str

    def __str__(self) -> str:
        return "<Config: apps={}, logdir={}, max_email_payload_bytes={}, api_secret={}>".format(
            self.apps, self.logdir, self.max_email_payload_bytes, "*****"
        )


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
        )
    except (KeyError, ValueError) as e:
        raise Config.InvalidConfig from e
