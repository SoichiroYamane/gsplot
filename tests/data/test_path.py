import os
import pytest
from gsplot.data.path import Path


class TestPath:
    def setup_method(self):
        self.path = Path()

    def test_get_home(self):
        assert self.path.get_home() == os.path.expanduser("~")

    def test_get_pwd(self):
        assert self.path.get_pwd() == os.getcwd()

    def test_move_to_pwd(self):
        self.path.move_to_pwd()
        assert os.getcwd() == self.path.get_pwd()
