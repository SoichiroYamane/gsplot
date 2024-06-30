import os


class Path:
    def get_home(self) -> str:
        return os.path.expanduser("~")

    def get_pwd(self) -> str:
        return os.getcwd()

    def move_to_pwd(self) -> None:
        os.chdir(self.get_pwd())
