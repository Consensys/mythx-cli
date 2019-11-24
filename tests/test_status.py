import json
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli

from .testdata import (
    GROUP_STATUS_RESPONSE_OBJ,
    GROUP_STATUS_RESPONSE_SIMPLE,
    GROUP_STATUS_RESPONSE_TABLE,
    STATUS_RESPONSE_OBJ,
    STATUS_RESPONSE_SIMPLE,
    STATUS_RESPONSE_TABLE,
)


def test_status_tabular():
    runner = CliRunner()
    with patch("pythx.Client.status") as status_patch:
        status_patch.return_value = STATUS_RESPONSE_OBJ
        result = runner.invoke(cli, ["status", "381eff48-04db-4f81-a417-8394b6614472"])
        assert result.exit_code == 0
        assert result.output == STATUS_RESPONSE_TABLE


def test_group_status_tabular():
    runner = CliRunner()
    with patch("pythx.Client.group_status") as status_patch:
        status_patch.return_value = GROUP_STATUS_RESPONSE_OBJ
        result = runner.invoke(cli, ["group", "status", "5dd40ca50d861d001101e888"])
        assert result.output == GROUP_STATUS_RESPONSE_TABLE
        assert result.exit_code == 0


def test_status_json():
    runner = CliRunner()
    with patch("pythx.Client.status") as status_patch:
        status_patch.return_value = STATUS_RESPONSE_OBJ
        result = runner.invoke(
            cli, ["--format", "json", "status", "381eff48-04db-4f81-a417-8394b6614472"]
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == STATUS_RESPONSE_OBJ.to_dict()


def test_group_status_json():
    runner = CliRunner()
    with patch("pythx.Client.group_status") as status_patch:
        status_patch.return_value = GROUP_STATUS_RESPONSE_OBJ
        result = runner.invoke(
            cli, ["--format", "json", "group", "status", "5dd40ca50d861d001101e888"]
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == GROUP_STATUS_RESPONSE_OBJ.to_dict()


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


def test_group_status_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.group_status") as status_patch:
        status_patch.return_value = GROUP_STATUS_RESPONSE_OBJ
        result = runner.invoke(
            cli,
            ["--format", "json-pretty", "group", "status", "5dd40ca50d861d001101e888"],
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == GROUP_STATUS_RESPONSE_OBJ.to_dict()


def test_status_simple():
    runner = CliRunner()
    with patch("pythx.Client.status") as status_patch:
        status_patch.return_value = STATUS_RESPONSE_OBJ
        result = runner.invoke(
            cli,
            ["--format", "simple", "status", "381eff48-04db-4f81-a417-8394b6614472"],
        )
        assert result.exit_code == 0
        assert result.output == STATUS_RESPONSE_SIMPLE


def test_group_status_simple():
    runner = CliRunner()
    with patch("pythx.Client.group_status") as status_patch:
        status_patch.return_value = GROUP_STATUS_RESPONSE_OBJ
        result = runner.invoke(
            cli, ["--format", "simple", "group", "status", "5dd40ca50d861d001101e888"]
        )
        assert result.exit_code == 0
        assert result.output == GROUP_STATUS_RESPONSE_SIMPLE
