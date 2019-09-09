from .simple_stdout import SimpleFormatter
from .json import JSONFormatter, PrettyJSONFormatter


FORMAT_RESOLVER = {"simple": SimpleFormatter(), "json": JSONFormatter(), "json-pretty": PrettyJSONFormatter()}
