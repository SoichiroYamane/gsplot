import os
from datetime import datetime
from typing import Any, cast

import yaml
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config.config import Config
from .path.path import PathToMain
from .version import __commit__, __version__


class Logger:
    HOME = os.path.expanduser("~")
    LOG_PATH = os.path.join(HOME, ".config", "gsplot")
    LOG_FILE_NAME = "gsplot_log.yml"
    LOG_FILE_PATH = os.path.join(LOG_PATH, LOG_FILE_NAME)

    def __init__(self):
        self.console = Console()
        self.log: dict[str, Any] = {}
        self.version_idx: int | None = None
        self.commit_idx: int | None = None

        self.is_error: bool = False

        self.create_file()
        self.log = self.read_file()

    def _create_empty_file(self):
        with open(self.LOG_FILE_PATH, "w") as file:
            file.write("{}")

    def create_file(self):
        if not os.path.exists(self.LOG_PATH):
            os.makedirs(self.LOG_PATH)

        # if YAML file does not exist, create it
        if not os.path.exists(self.LOG_FILE_PATH):
            self._create_empty_file()

    def _init_log(self):
        return {"versions": []}

    def read_file(self) -> dict[str, Any]:
        with open(self.LOG_FILE_PATH, "r") as file:
            log = yaml.safe_load(file)

        if not log or not log.get("versions"):
            log = self._init_log()

        return cast(dict[str, Any], log)

    def get_date(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _error_message(self, e: Exception) -> None:
        warning_message = f"[bold yellow]gsplot log file is corrupted. [bold green]See gsplot_log.yml file: {self.LOG_FILE_PATH}\n[bold red]Error: {e}"

        self.console.print(
            Panel(
                Text.from_markup(warning_message),
                title="[bold yellow]Warning",
                style="bold yellow",
            )
        )

    def _get_versions_from_log(self) -> list[dict[str, str]]:
        try:
            return cast(list[dict[str, str]], self.log.get("versions", []))
        except Exception as e:
            self.is_error = True
            self._error_message(e)
            return []

    def _get_commits_from_version(self, version: str) -> list[dict[str, str]]:
        try:
            return next(
                (
                    v.get("commits", [])
                    for v in self.log["versions"]
                    if v.get("version") == version
                ),
                [],
            )
        except Exception as e:
            self.is_error = True
            self._error_message(e)
            return []

    def _has_same_version(self, version: str) -> bool:
        # Retrieve the list of versions from the log
        versions: list[dict[str, str]] | None = self._get_versions_from_log()

        if not versions:
            return False

        # Find the index of the version that matches the input
        self.version_idx = next(
            (i for i, v in enumerate(versions) if v.get("version") == version), None
        )

        # Return True if a match is found, otherwise False
        return self.version_idx is not None

    def _has_same_commit(self, commit: str) -> bool:
        # Get commits from the version
        commits: list[dict[str, str]] = self._get_commits_from_version(__version__)

        if not commits:
            return False

        # Find the commit in the list of commits
        self.commit_idx = next(
            (i for i, c in enumerate(commits) if c.get("commit") == commit), None
        )

        # Return True if a match is found
        return self.commit_idx is not None

    def create_log(self):
        if not self._has_same_version(__version__):
            current = {
                "version": __version__,
                "commits": [{"commit": __commit__, "date": self.get_date()}],
            }

            self.log["versions"].append(current)
        else:
            if not self._has_same_commit(__commit__):
                self.log["versions"][self.version_idx]["commits"].append(
                    {"commit": __commit__, "date": self.get_date()}
                )

    def write_log(self, log: dict[str, Any]) -> None:
        with open(self.LOG_FILE_PATH, "w") as file:
            yaml.dump(log, file, default_flow_style=False, sort_keys=False, indent=2)

    def make_log(self) -> None:
        if self.is_error:
            return None

        try:
            self.create_log()
        except Exception as e:
            self.is_error = True
            self._error_message(e)

        self.write_log(self.log)


def logger():
    _logger = Logger()
    _logger.make_log()
