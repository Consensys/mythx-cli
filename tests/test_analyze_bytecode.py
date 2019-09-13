import json
import os
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli

from .testdata import (
    ARTIFACT_DATA,
    INPUT_RESPONSE_OBJ,
    ISSUES_RESPONSE_OBJ,
    SUBMISSION_RESPONSE_OBJ,
    ISSUES_RESPONSE_SIMPLE
)


FORMAT_ERROR = "Could not interpret argument lolwut as bytecode or Solidity file"


def test_bytecode_analyze():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE_OBJ
        ready_patch.return_value = True
        report_patch.return_value = ISSUES_RESPONSE_OBJ
        input_patch.return_value = INPUT_RESPONSE_OBJ

        result = runner.invoke(cli, ["analyze", "0xfe"])
        assert result.exit_code == 0
        assert SUBMISSION_RESPONSE_OBJ.analysis.uuid in result.output


def test_bytecode_analyze_invalid():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE_OBJ
        ready_patch.return_value = True
        report_patch.return_value = ISSUES_RESPONSE_OBJ
        input_patch.return_value = INPUT_RESPONSE_OBJ

        result = runner.invoke(cli, ["analyze", "lolwut"])
        assert result.exit_code == 2
        assert FORMAT_ERROR in result.output
