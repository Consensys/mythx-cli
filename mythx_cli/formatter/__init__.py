"""This module contains various formatters for printing report data."""

from .json import JSONFormatter, PrettyJSONFormatter
from .simple_stdout import SimpleFormatter
from .tabular import TabularFormatter

FORMAT_RESOLVER = {
    "simple": SimpleFormatter(),
    "json": JSONFormatter(),
    "json-pretty": PrettyJSONFormatter(),
    "table": TabularFormatter(),
}

__all__ = [JSONFormatter, PrettyJSONFormatter, SimpleFormatter, TabularFormatter]
