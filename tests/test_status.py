import json
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli

from .testdata import STATUS_RESPONSE_OBJ, STATUS_RESPONSE_SIMPLE


def test_status_simple():
    runner = CliRunner()
    with patch("pythx.Client.status") as status_patch:
        status_patch.return_value = STATUS_RESPONSE_OBJ
        result = runner.invoke(cli, ["status", "381eff48-04db-4f81-a417-8394b6614472"])
        assert result.exit_code == 0
        assert result.output == STATUS_RESPONSE_SIMPLE


def test_status_json():
    runner = CliRunner()
    with patch("pythx.Client.status") as status_patch:
        status_patch.return_value = STATUS_RESPONSE_OBJ
        result = runner.invoke(
            cli, ["--format", "json", "status", "381eff48-04db-4f81-a417-8394b6614472"]
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == STATUS_RESPONSE_OBJ.to_dict()


def test_status_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.status") as status_patch:
        status_patch.return_value = STATUS_RESPONSE_OBJ
        result = runner.invoke(
            cli,
            [
                "--format",
                "json-pretty",
                "status",
                "381eff48-04db-4f81-a417-8394b6614472",
            ],
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == STATUS_RESPONSE_OBJ.to_dict()
