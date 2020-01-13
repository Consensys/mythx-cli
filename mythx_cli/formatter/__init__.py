from .json import JSONFormatter, PrettyJSONFormatter
from .simple_stdout import SimpleFormatter
from .tabular import TabularFormatter
from .sonarqube import SonarQubeFormatter

FORMAT_RESOLVER = {
    "simple": SimpleFormatter(),
    "json": JSONFormatter(),
    "json-pretty": PrettyJSONFormatter(),
    "table": TabularFormatter(),
    "sonar": SonarQubeFormatter(),
}

__all__ = [JSONFormatter, PrettyJSONFormatter, SimpleFormatter, TabularFormatter, SonarQubeFormatter]
