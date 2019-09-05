from .simple_stdout import SimpleFormatter
from .json import JSONFormatter


FORMAT_RESOLVER = {"simple": SimpleFormatter, "json": JSONFormatter}
