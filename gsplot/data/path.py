import os


class Path:
    def get_home(self) -> str:
        return os.path.expanduser("~")

    def get_pwd(self) -> str:
        return os.getcwd()

    def move_to_pwd(self) -> None:
        os.chdir(self.get_pwd())


def get_home() -> str:
    return Path().get_home()


def get_pwd() -> str:
    return Path().get_pwd()


def move_to_pwd() -> None:
    Path().move_to_pwd()
