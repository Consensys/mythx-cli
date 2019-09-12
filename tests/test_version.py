import json
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli

from .testdata import VERSION_RESPONSE_OBJ, VERSION_RESPONSE_SIMPLE


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
