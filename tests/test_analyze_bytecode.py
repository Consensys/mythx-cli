from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli
from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisSubmissionResponse,
    DetectedIssuesResponse,
)
from copy import deepcopy
from .common import get_test_case

FORMAT_ERROR = "Could not interpret argument lolwut as bytecode or Solidity file"
SUBMISSION_RESPONSE = get_test_case(
    "testdata/analysis-submission-response.json", AnalysisSubmissionResponse
)
ISSUES_RESPONSE = get_test_case(
    "testdata/detected-issues-response.json", DetectedIssuesResponse
)
INPUT_RESPONSE = get_test_case(
    "testdata/analysis-input-response.json", AnalysisInputResponse
)


def test_bytecode_analyze():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = deepcopy(ISSUES_RESPONSE)
        input_patch.return_value = INPUT_RESPONSE

        result = runner.invoke(cli, ["analyze", "0xfe"])
        assert result.exit_code == 0
        assert INPUT_RESPONSE.source_list[0] in result.output


def test_bytecode_analyze_blacklist():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = deepcopy(ISSUES_RESPONSE)
        input_patch.return_value = INPUT_RESPONSE

        result = runner.invoke(cli, ["analyze", "--swc-blacklist", "SWC-110", "0xfe"])
        assert result.exit_code == 0
        assert "Assert Violation" not in result.output
        assert "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol" not in result.output


def test_bytecode_analyze_filter():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = deepcopy(ISSUES_RESPONSE)
        input_patch.return_value = INPUT_RESPONSE

        result = runner.invoke(cli, ["analyze", "--min-severity", "high", "0xfe"])
        assert result.exit_code == 0
        assert "Assert Violation" not in result.output
        assert "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol" not in result.output


def test_bytecode_analyze_invalid():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = deepcopy(ISSUES_RESPONSE)
        input_patch.return_value = INPUT_RESPONSE

        result = runner.invoke(cli, ["analyze", "lolwut"])
        assert result.exit_code == 2
        assert FORMAT_ERROR in result.output
