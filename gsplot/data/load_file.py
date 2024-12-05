from os import PathLike
from typing import Any, Iterable

import numpy as np
from numpy.typing import NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params

__all__: list[str] = ["load_file"]


class LoadFile:
    """
    A utility class to load data from a file or iterable source using NumPy's `genfromtxt`.

    This class provides an interface for loading structured data from files or iterables
    with options for handling delimiters, skipping headers/footers, and unpacking the data.

    Parameters
    --------------------
    f : str, os.PathLike, Iterable[str], or Iterable[bytes]
        The file path, file-like object, or iterable source from which to load data.
    delimiter : str or None, optional
        The string used to separate values. If `None`, any whitespace is treated as a delimiter (default is ",").
    skip_header : int, optional
        The number of lines to skip at the beginning of the file (default is 0).
    skip_footer : int, optional
        The number of lines to skip at the end of the file (default is 0).
    unpack : bool, optional
        Whether to unpack columns into separate arrays (default is True).
    **kwargs : Any
        Additional keyword arguments to pass to NumPy's `genfromtxt`.

    Attributes
    --------------------
    f : str, os.PathLike, Iterable[str], or Iterable[bytes]
        The file path, file-like object, or iterable source from which to load data.
    delimiter : str or None
        The string used to separate values.
    skip_header : int
        The number of lines to skip at the beginning of the file.
    skip_footer : int
        The number of lines to skip at the end of the file.
    unpack : bool
        Whether to unpack columns into separate arrays.
    kwargs : Any
        Additional arguments passed to `genfromtxt`.

    Methods
    --------------------
    load_data()
        Loads the data using NumPy's `genfromtxt` with the specified parameters.

    Examples
    --------------------
    >>> loader = LoadFile("data.csv", delimiter=",", skip_header=1, unpack=False)
    >>> data = loader.load_data()
    >>> print(data)
    array([[1.0, 2.0, 3.0],
           [4.0, 5.0, 6.0],
           [7.0, 8.0, 9.0]])
    """

    def __init__(
        self,
        f: str | PathLike | Iterable[str] | Iterable[bytes],
        delimiter: str | None = ",",
        skip_header: int = 0,
        skip_footer: int = 0,
        unpack: bool = True,
        **kwargs: Any,
    ) -> None:

        self.f: str | PathLike | Iterable[str] | Iterable[bytes] = f
        self.delimiter: str | None = delimiter
        self.skip_header: int = skip_header
        self.skip_footer: int = skip_footer
        self.unpack: bool = unpack
        self.kwargs: Any = kwargs

    def load_data(self) -> NDArray[Any]:
        """
        Loads the data using NumPy's `genfromtxt` with the specified parameters.

        Returns
        --------------------
        numpy.ndarray
            The loaded data as a NumPy array.

        Raises
        --------------------
        ValueError
            If the file cannot be loaded or parsed correctly.

        Examples
        --------------------
        >>> loader = LoadFile("data.csv", delimiter=",", skip_header=1, unpack=False)
        >>> data = loader.load_data()
        >>> print(data)
        array([[1.0, 2.0, 3.0],
               [4.0, 5.0, 6.0],
               [7.0, 8.0, 9.0]])
        """

        # np.genfromtxt does not have args parameter
        return np.genfromtxt(
            fname=self.f,
            delimiter=self.delimiter,
            skip_header=self.skip_header,
            skip_footer=self.skip_footer,
            unpack=self.unpack,
            **self.kwargs,
        )


@bind_passed_params()
def load_file(
    f: str | PathLike | Iterable[str] | Iterable[bytes],
    delimiter: str | None = ",",
    skip_header: int = 0,
    skip_footer: int = 0,
    unpack: bool = True,
    **kwargs: Any,
) -> NDArray[Any]:
    """
    Loads structured data from a file or iterable source using the specified parameters.

    This function provides a flexible interface for loading data with NumPy's `genfromtxt`.
    It captures and processes the passed parameters, allowing for customized file loading
    options, such as handling delimiters, skipping headers/footers, and unpacking columns.

    Parameters
    --------------------
    f : str, os.PathLike, Iterable[str], or Iterable[bytes]
        The file path, file-like object, or iterable source from which to load data.
    delimiter : str or None, optional
        The string used to separate values. If `None`, any whitespace is treated as a delimiter (default is ",").
    skip_header : int, optional
        The number of lines to skip at the beginning of the file (default is 0).
    skip_footer : int, optional
        The number of lines to skip at the end of the file (default is 0).
    unpack : bool, optional
        Whether to unpack columns into separate arrays (default is True).
    **kwargs : Any
        Additional keyword arguments to pass to NumPy's `genfromtxt`.

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters and
    the `CreateClassParams` class to handle the merging of default, configuration,
    and passed parameters.

    Returns
    --------------------
    numpy.ndarray
        The loaded data as a NumPy array.

    Raises
    --------------------
    ValueError
        If the file cannot be loaded or parsed correctly.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> data = gs.load_file("data.csv", delimiter=",", skip_header=1, unpack=False)
    >>> print(data)
    array([[1.0, 2.0, 3.0],
           [4.0, 5.0, 6.0],
           [7.0, 8.0, 9.0]])

    >>> data = gs.load_file(["1,2,3", "4,5,6", "7,8,9"], delimiter=",", unpack=True)
    >>> print(data)
    [array([1.0, 4.0, 7.0]), array([2.0, 5.0, 8.0]), array([3.0, 6.0, 9.0])]
    """

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _load_file: LoadFile = LoadFile(
        class_params["f"],
        class_params["delimiter"],
        class_params["skip_header"],
        class_params["skip_footer"],
        class_params["unpack"],
        **class_params["kwargs"],
    )
    return _load_file.load_data()
