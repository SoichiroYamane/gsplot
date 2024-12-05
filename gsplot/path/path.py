import os
import sys

__all__: list[str] = ["home", "pwd", "pwd_move", "pwd_main"]


class Path:
    """
    A utility class for handling common file system operations.

    This class provides methods for retrieving the home directory, current working
    directory, and moving to the current working directory.

    Methods
    --------------------
    get_home()
        Returns the path to the user's home directory.
    get_pwd()
        Returns the current working directory.
    move_to_pwd()
        Changes the current working directory to the current value of `get_pwd()`.

    Examples
    --------------------
    >>> path_util = Path()
    >>> home_dir = path_util.get_home()
    >>> print(home_dir)
    "/home/user"  # Example output

    >>> pwd = path_util.get_pwd()
    >>> print(pwd)
    "/home/user/project"  # Example output

    >>> path_util.move_to_pwd()  # Moves to the current working directory
    """

    def get_home(self) -> str:
        """
        Returns the path to the user's home directory.

        Returns
        --------------------
        str
            The absolute path to the home directory.

        Examples
        --------------------
        >>> path_util = Path()
        >>> home_dir = path_util.get_home()
        >>> print(home_dir)
        "/home/user"  # Example output
        """
        return os.path.expanduser("~")

    def get_pwd(self) -> str:
        """
        Returns the current working directory.

        Returns
        --------------------
        str
            The absolute path of the current working directory.

        Examples
        --------------------
        >>> path_util = Path()
        >>> pwd = path_util.get_pwd()
        >>> print(pwd)
        "/home/user/project"  # Example output
        """
        return os.getcwd()

    def move_to_pwd(self) -> None:
        """
        Changes the current working directory to the current value of `get_pwd()`.

        This is typically redundant, as the current working directory is already the result of `get_pwd()`.

        Examples
        --------------------
        >>> path_util = Path()
        >>> path_util.move_to_pwd()  # Changes directory to the current working directory
        """
        os.chdir(self.get_pwd())


def home() -> str:
    """
    Returns the path to the user's home directory.

    This is a convenience function wrapping `Path.get_home`.

    Returns
    --------------------
    str
        The absolute path to the home directory.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> home_dir = gs.home()
    >>> print(home_dir)
    "/home/user"  # Example output
    """
    return Path().get_home()


def pwd() -> str:
    """
    Returns the current working directory.

    This is a convenience function wrapping `Path.get_pwd`.

    Returns
    --------------------
    str
        The absolute path of the current working directory.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> current_dir = gs.pwd()
    >>> print(current_dir)
    "/home/user/project"  # Example output
    """
    return Path().get_pwd()


def pwd_move() -> None:
    """
    Changes the current working directory to the value of `pwd()`.

    This is a convenience function wrapping `Path.move_to_pwd`.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.pwd_move()  # Changes directory to the current working directory
    """
    Path().move_to_pwd()


class PathToMain:
    """
    A utility class to retrieve the directory of the executed main file.

    This class determines the directory of the script or module being executed as the main
    program. If executed in an environment where `__file__` is not available (e.g., REPL or
    interactive environments), it falls back to the current working directory.

    Attributes
    --------------------
    EXECUTED_FILE_DIR : str or None
        The directory of the executed main file. Initialized as `None`.

    Methods
    --------------------
    get_executed_file_dir()
        Retrieves the directory of the executed main file or the current working directory.

    Examples
    --------------------
    >>> path_util = PathToMain()
    >>> executed_dir = path_util.get_executed_file_dir()
    >>> print(executed_dir)
    "/home/user/project"  # Example output for an executed script
    """

    EXECUTED_FILE_DIR: str | None = None

    def get_executed_file_dir(self) -> str:
        """
        Retrieves the directory of the executed main file or the current working directory.

        This method checks the `__file__` attribute of the `__main__` module to determine
        the directory of the executed script. If unavailable (e.g., in REPL), it defaults to
        the current working directory.

        Returns
        --------------------
        str
            The directory of the executed main file or the current working directory.

        Raises
        --------------------
        ValueError
            If the executed file directory cannot be determined.

        Examples
        --------------------
        >>> path_util = PathToMain()
        >>> executed_dir = path_util.get_executed_file_dir()
        >>> print(executed_dir)
        "/home/user/project"  # Example output for an executed script
        """
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
    Retrieves the directory of the executed main file or the current working directory.

    This function is a convenience wrapper around `PathToMain.get_executed_file_dir`.

    Returns
    --------------------
    str
        The directory of the executed main file or the current working directory.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> executed_dir = gs.pwd_main()
    >>> print(executed_dir)
    "/home/user/project"  # Example output for an executed script
    """
    return PathToMain().get_executed_file_dir()
