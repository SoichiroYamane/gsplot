import os
import sys

__all__: list[str] = ["home", "pwd", "pwd_move", "pwd_main"]


class Path:
    """
    A utility class for handling basic file path operations, such as retrieving the home directory
    and current working directory, and changing the current working directory.

    Methods
    -------
    get_home() -> str
        Returns the path to the user's home directory.
    get_pwd() -> str
        Returns the path to the current working directory.
    move_to_pwd() -> None
        Changes the current working directory to the directory returned by get_pwd().
    """

    def get_home(self) -> str:
        """
        Returns the path to the user's home directory.

        Returns
        -------
        str
            The path to the home directory.
        """
        return os.path.expanduser("~")

    def get_pwd(self) -> str:
        """
        Returns the path to the current working directory.

        Returns
        -------
        str
            The path to the current working directory.
        """
        return os.getcwd()

    def move_to_pwd(self) -> None:
        """
        Changes the current working directory to the directory returned by `get_pwd()`.

        Returns
        -------
        None
        """
        os.chdir(self.get_pwd())


def home() -> str:
    """
    Returns the path to the user's home directory.

    Returns
    -------
    str
        The path to the home directory.
    """

    return Path().get_home()


def pwd() -> str:
    """
    Returns the path to the current working directory.

    Returns
    -------
    str
        The path to the current working directory.
    """
    return Path().get_pwd()


def pwd_move() -> None:
    """
    Changes the current working directory to the directory returned by `get_pwd()`.

    Returns
    -------
    None
    """
    Path().move_to_pwd()


class PathToMain:
    EXECUTED_FILE_DIR: str | None = None

    def get_executed_file_dir(self) -> str:
        if hasattr(sys.modules["__main__"], "__file__"):
            file_path = sys.modules["__main__"].__file__
            if file_path:
                self.EXECUTED_FILE_DIR = os.path.dirname(os.path.abspath(file_path))
        else:
            # case when __file__ does not exist in REPL or environment
            self.EXECUTED_FILE_DIR = os.getcwd()  # current working directory

        if self.EXECUTED_FILE_DIR is None:
            raise ValueError("Cannot find the executed file directory.")
        return self.EXECUTED_FILE_DIR


def pwd_main() -> str:
    """
    Returns the path to the directory of the executed file.

    Returns
    -------
    str
        The path to the directory of the executed file.
    """
    return PathToMain().get_executed_file_dir()
