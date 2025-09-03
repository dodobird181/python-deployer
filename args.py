import argparse
from collections import namedtuple

Arguments = namedtuple(
    "ArgNamespace",
    ["log_level"],
)


def get_arguments() -> Arguments:
    """Parse script arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str,
        help="The console log level. One of: [DEBUG, INFO, WARNING, ERROR]. ",
    )
    args = parser.parse_args()
    return args  # type: ignore
