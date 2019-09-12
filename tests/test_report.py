import json
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli

from .testdata import INPUT_RESPONSE_OBJ, ISSUES_RESPONSE_OBJ, ISSUES_RESPONSE_SIMPLE


def test_report_simple():
    runner = CliRunner()
    with patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        report_patch.return_value = ISSUES_RESPONSE_OBJ
        input_patch.return_value = INPUT_RESPONSE_OBJ
        result = runner.invoke(cli, ["report", "ab9092f7-54d0-480f-9b63-1bb1508280e2"])
        assert result.exit_code == 0
        assert result.output == ISSUES_RESPONSE_SIMPLE


def test_report_json():
    runner = CliRunner()
    with patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        report_patch.return_value = ISSUES_RESPONSE_OBJ
        input_patch.return_value = INPUT_RESPONSE_OBJ
        result = runner.invoke(
            cli, ["--format", "json", "report", "ab9092f7-54d0-480f-9b63-1bb1508280e2"]
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == json.loads(ISSUES_RESPONSE_OBJ.to_json())


def test_report_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        report_patch.return_value = ISSUES_RESPONSE_OBJ
        input_patch.return_value = INPUT_RESPONSE_OBJ
        result = runner.invoke(
            cli,
            [
                "--format",
                "json-pretty",
                "report",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == json.loads(ISSUES_RESPONSE_OBJ.to_json())
