import warnings

__all__ = ["hello_world"]


def hello_world() -> None:
    """
    Warn that the old display helper is documentation-only.
    """

    warnings.warn(
        "gsplot.hello_world is documentation-only and no longer displays output; "
        "use gsplot.build_info() for version information",
        DeprecationWarning,
        stacklevel=2,
    )
