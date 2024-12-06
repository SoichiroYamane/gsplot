from rich import print

from ..version import __commit__, __version__

__all__ = ["hello_world"]


def hello_world() -> None:
    """
    Print the version, commit hash, and an ASCII art of the logo.
    """
    ascii_art = r"""
 ██████╗ ███████╗██████╗ ██╗      ██████╗ ████████╗
██╔════╝ ██╔════╝██╔══██╗██║     ██╔═══██╗╚══██╔══╝
██║  ███╗███████╗██████╔╝██║     ██║   ██║   ██║   
██║   ██║╚════██║██╔═══╝ ██║     ██║   ██║   ██║   
╚██████╔╝███████║██║     ███████╗╚██████╔╝   ██║   
 ╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝   
        """

    print(f"Version: {__version__}")
    print(f"Commit : {__commit__}")
    print(ascii_art)
