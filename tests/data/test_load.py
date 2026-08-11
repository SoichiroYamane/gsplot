import numpy as np

from gsplot.data.load_file import LoadFile, LoadFileFast, load_file, load_file_fast


def test_load_file_class_reads_a_text_file(tmp_path) -> None:
    data_file = tmp_path / "data.txt"
    data_file.write_text("1 2 3\n4 5 6\n", encoding="utf-8")

    data = LoadFile(data_file, delimiter=" ", unpack=False).load_data()

    np.testing.assert_array_equal(data, np.array([[1, 2, 3], [4, 5, 6]]))


def test_load_file_wrapper_uses_current_public_api(tmp_path) -> None:
    data_file = tmp_path / "data.csv"
    data_file.write_text("1,2\n3,4\n", encoding="utf-8")

    data = load_file(data_file, delimiter=",", unpack=False)

    np.testing.assert_array_equal(data, np.array([[1, 2], [3, 4]]))


def test_load_file_fast_supports_class_and_wrapper(tmp_path) -> None:
    data_file = tmp_path / "data.csv"
    data_file.write_text("1,2\n3,4\n", encoding="utf-8")

    class_data = LoadFileFast(data_file, delimiter=",", unpack=False).load_data()
    wrapper_data = load_file_fast(data_file, delimiter=",", unpack=False)

    expected = np.array([[1, 2], [3, 4]])
    np.testing.assert_array_equal(class_data, expected)
    np.testing.assert_array_equal(wrapper_data, expected)
