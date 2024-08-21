import numpy as np
from os import PathLike
from typing import Iterable, Any, Union
from ..base.base import AttributeSetter


class LoadFile:
    """
    A class to load data from a file with customizable options such as delimiter,
    header/footer skipping, and unpacking.

    Parameters
    ----------
    f : Union[str, PathLike, Iterable[str], Iterable[bytes]]
        The file path or an iterable of strings/bytes representing the data to be loaded.
    delimiter : Union[None, str], optional
        The string used to separate values in the file (default is ',').
    skip_header : int, optional
        The number of lines to skip at the beginning of the file (default is 0).
    skip_footer : int, optional
        The number of lines to skip at the end of the file (default is 0).
    unpack : Union[None, bool], optional
        If True, the columns are returned as separate arrays (default is True).
    **kwargs : Any
        Additional keyword arguments to pass to `np.genfromtxt`.

    Attributes
    ----------
    f : Union[str, PathLike, Iterable[str], Iterable[bytes]]
        The file path or an iterable of strings/bytes representing the data to be loaded.
    delimiter : Union[None, str]
        The string used to separate values in the file.
    skip_header : int
        The number of lines to skip at the beginning of the file.
    skip_footer : int
        The number of lines to skip at the end of the file.
    unpack : Union[None, bool]
        If True, the columns are returned as separate arrays.
    kwargs : Any
        Additional keyword arguments to pass to `np.genfromtxt`.

    Methods
    -------
    load_text() -> np.ndarray
        Loads the data from the file and returns it as a NumPy array.
    """

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
        """
        Loads the data from the file and returns it as a NumPy array.

        Returns
        -------
        np.ndarray
            The data loaded from the file as a NumPy array.
        """

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
    """
    Loads data from a file with customizable options and returns it as a NumPy array.

    Parameters
    ----------
    f : Union[str, PathLike, Iterable[str], Iterable[bytes]]
        The file path or an iterable of strings/bytes representing the data to be loaded.
    delimiter : Union[None, str], optional
        The string used to separate values in the file (default is ',').
    skip_header : int, optional
        The number of lines to skip at the beginning of the file (default is 0).
    skip_footer : int, optional
        The number of lines to skip at the end of the file (default is 0).
    unpack : Union[None, bool], optional
        If True, the columns are returned as separate arrays (default is True).
    **kwargs : Any
        Additional keyword arguments to pass to `np.genfromtxt`.

    Returns
    -------
    np.ndarray
        The data loaded from the file as a NumPy array.
    """

    load_text = LoadFile(
        f, delimiter, skip_header, skip_footer, unpack, **kwargs
    ).load_text()
    return load_text
