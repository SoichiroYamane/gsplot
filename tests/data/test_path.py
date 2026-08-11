import os
import sys

from gsplot.path.path import Path, PathToMain, home, pwd, pwd_main, pwd_move


def test_path_class_matches_the_process_environment(monkeypatch, tmp_path) -> None:
    path = Path()
    monkeypatch.chdir(tmp_path)

    assert path.get_home() == os.path.expanduser("~")
    assert path.get_pwd() == str(tmp_path)

    path.move_to_pwd()
    assert os.getcwd() == str(tmp_path)


def test_path_module_helpers(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    assert home() == os.path.expanduser("~")
    assert pwd() == str(tmp_path)
    pwd_move()
    expected_main_dir = os.path.dirname(
        os.path.abspath(sys.modules["__main__"].__file__)
    )
    assert pwd_main() == expected_main_dir
    assert PathToMain().get_executed_file_dir() == expected_main_dir
