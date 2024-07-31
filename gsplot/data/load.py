import numpy as np
from os import PathLike
from typing import Iterable, Any, Union
from ..base.base import AttributeSetter


class LoadFile:
    def __init__(
        self,
        f: Union[str, PathLike, Iterable[str], Iterable[bytes]],
        delimiter: Union[None, str] = ",",
        skip_header: int = 0,
        skip_footer: int = 0,
        unpack: Union[None, bool] = True,
        **kwargs: Any,
    ) -> None:
        self.f: Union[str, PathLike, Iterable[str], Iterable[bytes]] = f
        self.delimiter: Union[None, str] = delimiter
        self.skip_header: int = skip_header
        self.skip_footer: int = skip_footer
        self.unpack: Union[None, bool] = unpack
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs = attributer.set_attributes(self, locals(), key="load")

    def load_text(self):
        return np.genfromtxt(
            fname=self.f,
            delimiter=self.delimiter,
            skip_header=self.skip_header,
            skip_footer=self.skip_footer,
            unpack=self.unpack,
            **self.kwargs,
        )


def load_file(
    f: Union[str, PathLike, Iterable[str], Iterable[bytes]],
    delimiter: Union[None, str] = ",",
    skip_header: int = 0,
    skip_footer: int = 0,
    unpack: Union[None, bool] = True,
    **kwargs: Any,
):
    load_text = LoadFile(
        f, delimiter, skip_header, skip_footer, unpack, **kwargs
    ).load_text()
    return load_text
