import os


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


def get_home() -> str:
    """
    Returns the path to the user's home directory.

    Returns
    -------
    str
        The path to the home directory.
    """
    return Path().get_home()


def get_pwd() -> str:
    """
    Returns the path to the current working directory.

    Returns
    -------
    str
        The path to the current working directory.
    """
    return Path().get_pwd()


def move_to_pwd() -> None:
    """
    Changes the current working directory to the directory returned by `get_pwd()`.

    Returns
    -------
    None
    """
    Path().move_to_pwd()
