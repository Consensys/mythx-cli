from .json import JSONFormatter, PrettyJSONFormatter
from .simple_stdout import SimpleFormatter

FORMAT_RESOLVER = {
    "simple": SimpleFormatter(),
    "json": JSONFormatter(),
    "json-pretty": PrettyJSONFormatter(),
}
