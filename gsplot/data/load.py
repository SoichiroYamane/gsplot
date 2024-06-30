import numpy as np
from typing import Any, Union
from os import PathLike
from typing import Iterable


class LoadFile:
    def __init__(self, f: Union[str, PathLike[str], Iterable[str], Iterable[bytes]]):
        self.f = f

    def load_txt(self, *args: Any, **kwargs: Any) -> np.ndarray:
        return np.genfromtxt(self.f, *args, **kwargs)
