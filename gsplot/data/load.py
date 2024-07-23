import numpy as np
from typing import Any, Union
from os import PathLike
from typing import Iterable, Dict, List, Tuple, Any, Union
from ..base.base import AttributeSetter
from ..params.params import Params, LoadParams


# TODO: add json default value support
class LoadFile:
    def __init__(
        self,
        f: Union[str, PathLike[str], Iterable[str], Iterable[bytes]],
        delimiter: str = ",",
        skip_header: int = 0,
        skip_footer: int = 0,
        unpack: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> None:

        self.f: Union[str, PathLike[str], Iterable[str], Iterable[bytes]] = f
        self.delimiter: str = delimiter
        self.skip_header: int = skip_header
        self.skip_footer: int = skip_footer
        self.unpack: bool = unpack
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs = attributer.set_attributes(self, locals(), key="load")

    def load_text(self) -> np.ndarray:
        return np.genfromtxt(self.f, *self.args, **self.kwargs)


def load_file(
    f: Union[str, PathLike[str], Iterable[str], Iterable[bytes]],
    delimiter: str = ",",
    skip_header: int = 0,
    skip_footer: int = 0,
    unpack: bool = True,
    *args: Any,
    **kwargs: Any,
) -> np.ndarray:
    load_text = LoadFile(
        f, delimiter, skip_header, skip_footer, unpack, *args, **kwargs
    ).load_text()
    return load_text
