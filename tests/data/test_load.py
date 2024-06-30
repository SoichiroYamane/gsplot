import pytest
import numpy as np
from typing import Optional
from pathlib import Path
from gsplot.data.load import LoadFile


class TestLoadFile:
    loader: Optional[LoadFile] = None

    @classmethod
    def setup_class(cls):
        # Create a temporary file with some data
        with open("temp.txt", "w") as f:
            f.write("1 2 3\n4 5 6")

        cls.loader = LoadFile("temp.txt")

    @classmethod
    def teardown_class(cls):
        # Clean up the temporary file
        Path("temp.txt").unlink()

    def test_load_txt(self):
        assert self.loader is not None

        # Use LoadFile to load the data
        data = self.loader.load_txt()

        # Check that the data was loaded correctly
        assert np.array_equal(data, np.array([[1, 2, 3], [4, 5, 6]]))
