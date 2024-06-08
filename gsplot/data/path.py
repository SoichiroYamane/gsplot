import os


class Path:
    def __init__(
        self,
    ):
        pass

    def get_home(self) -> str:
        home = os.path.expanduser("~")
        return home

    def get_pwd(self) -> str:
        pwd = os.path.dirname(os.path.abspath("__file__"))
        return pwd

    def move_to_pwd(self):
        pwd = self.get_pwd()
        os.chdir(pwd)
