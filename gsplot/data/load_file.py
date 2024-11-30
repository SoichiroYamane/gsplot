import numpy as np
from os import PathLike
from typing import Iterable, Any
from numpy.typing import NDArray

from ..base.base import bind_passed_params, ParamsGetter, CreateClassParams


class LoadFile:
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

        # np.genfromtxt does not have args parameter
        return np.genfromtxt(
            fname=self.f,
            delimiter=self.delimiter,
            skip_header=self.skip_header,
            skip_footer=self.skip_footer,
            unpack=self.unpack,
            **self.kwargs,
        )


# TODO: Modify docstring
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
    Load data from a file or an iterable and return it as a NumPy array.

    This function reads data from a specified file, path, or iterable. It supports
    custom delimiters, header/footer skipping, and unpacking of data into columns.

    Parameters
    ----------
    f : str, PathLike, Iterable[str], or Iterable[bytes]
        The file path, file-like object, or iterable containing the data to load.
        Strings or bytes are also accepted as iterable data sources.
    delimiter : str or None, optional
        The delimiter used to separate values in the data. If None, whitespace is used
        as the default delimiter. Default is ",".
    skip_header : int, optional
        Number of lines to skip at the beginning of the file. Default is 0.
    skip_footer : int, optional
        Number of lines to skip at the end of the file. Default is 0.
    unpack : bool, optional
        If True, unpack the columns into individual arrays. Default is True.
    **kwargs : Any
        Additional arguments passed to the file loader, such as encoding or specific
        parsing options.

    Returns
    -------
    NDArray[Any]
        A NumPy array containing the loaded data. If `unpack` is True, the data is
        returned as separate arrays (one per column).

    Notes
    -----
    - This function uses the `LoadFile` class for file parsing and data loading.
    - It automatically resolves parameters using the `ParamsGetter` and `CreateClassParams` classes.
    - The input `f` can be a file path, open file handle, or iterable containing
      lines of data.

    Examples
    --------
    Load data from a CSV file:

    >>> load_file("data.csv")
    array([...])  # Loaded data as a NumPy array.

    Use a custom delimiter:

    >>> load_file("data.tsv", delimiter="\t")
    array([...])  # Data loaded with tab-separated values.

    Skip headers and footers:

    >>> load_file("data.txt", skip_header=2, skip_footer=1)
    array([...])  # Data with headers/footers excluded.

    Load data from an iterable:

    >>> data = ["1,2,3", "4,5,6"]
    >>> load_file(data, delimiter=",")
    array([[1, 2, 3],
           [4, 5, 6]])
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
