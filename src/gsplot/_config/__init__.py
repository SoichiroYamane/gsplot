"""Private explicit configuration foundation for the canonical API."""

from .loader import (
    DEFAULT_CONFIG_NAME,
    load_config,
    resolve_config_value,
)
from .model import Config, FigureConfig, PlottingConfig

__all__ = [
    "DEFAULT_CONFIG_NAME",
    "load_config",
    "resolve_config_value",
    "Config",
    "FigureConfig",
    "PlottingConfig",
]
