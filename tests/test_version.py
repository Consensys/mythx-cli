import json
from unittest.mock import patch

from click.testing import CliRunner
from mythx_models.response import VersionResponse

from mythx_cli.cli import cli

VERSION_RESPONSE_OBJ = VersionResponse.from_dict(
    {
        "api": "v1.4.34.4",
        "maru": "0.5.3",
        "mythril": "0.21.14",
        "harvey": "0.0.33",
        "hash": "6e0035da873e809e90eab4665e3d19d6",
    }
)

VERSION_RESPONSE_SIMPLE = """API: v1.4.34.4
Harvey: 0.0.33
Maru: 0.5.3
Mythril: 0.21.14
Hashed: 6e0035da873e809e90eab4665e3d19d6
"""


def test_version_simple():
    runner = CliRunner()
    with patch("pythx.Client.version") as version_patch:
        version_patch.return_value = VERSION_RESPONSE_OBJ
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert result.output == VERSION_RESPONSE_SIMPLE


def test_version_json():
    runner = CliRunner()
    with patch("pythx.Client.version") as version_patch:
        version_patch.return_value = VERSION_RESPONSE_OBJ
        result = runner.invoke(cli, ["--format", "json", "version"])
        assert result.exit_code == 0
        assert json.loads(result.output) == VERSION_RESPONSE_OBJ.to_dict()


def test_version_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.version") as version_patch:
        version_patch.return_value = VERSION_RESPONSE_OBJ
        result = runner.invoke(cli, ["--format", "json-pretty", "version"])
        assert result.exit_code == 0
        assert json.loads(result.output) == VERSION_RESPONSE_OBJ.to_dict()
