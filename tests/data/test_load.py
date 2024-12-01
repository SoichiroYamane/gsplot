from pathlib import Path
from typing import Optional

import numpy as np
import pytest

from gsplot.data.load import LoadFile


class TestLoadFile:
    loader: Optional[LoadFile] = None

    @classmethod
    def setup_class(cls):
        # Create a temporary file with some data
        with open("temp.txt", "w") as f:
            f.write("1 2 3\n4 5 6")

        cls.loader = LoadFile("temp.txt", delimiter=" ")

    @classmethod
    def teardown_class(cls):
        # Clean up the temporary file
        Path("temp.txt").unlink()

    def test_load_text(self):
        assert self.loader is not None

        # Use LoadFile to load the data
        data = self.loader.load_text()

        # Check that the data was loaded correctly
        assert np.array_equal(data, np.array([[1, 2, 3], [4, 5, 6]]))
