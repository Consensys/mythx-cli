from copy import deepcopy
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli
from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisSubmissionResponse,
    DetectedIssuesResponse,
    Severity,
)

from .common import get_test_case

SOLIDITY_CODE = """pragma solidity 0.4.13;

contract OutdatedCompilerVersion {
    uint public x = 1;
}
"""
SOLC_ERROR = "No pragma found - please specify a solc version with --solc-version"
INPUT_RESPONSE = get_test_case(
    "testdata/analysis-input-response.json", AnalysisInputResponse
)
ISSUES_RESPONSE = get_test_case(
    "testdata/detected-issues-response.json", DetectedIssuesResponse
)
SUBMISSION_RESPONSE = get_test_case(
    "testdata/analysis-submission-response.json", AnalysisSubmissionResponse
)
ISSUES_TABLE = get_test_case("testdata/detected-issues-table.txt", raw=True)


def test_solidity_analyze_async():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["analyze", "--async"], input="y\n")
            assert result.exit_code == 0
            assert SUBMISSION_RESPONSE.analysis.uuid in result.output


def test_solidity_analyze_blocking():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["analyze"], input="y\n")
            assert result.exit_code == 0
            assert ISSUES_TABLE in result.output


def test_solidity_analyze_blocking_ci():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        # set up high-severity issue
        issues_resp = deepcopy(ISSUES_RESPONSE)
        issues_resp.issue_reports[0].issues[0].severity = Severity.HIGH

        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = issues_resp
        input_patch.return_value = INPUT_RESPONSE

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["--ci", "analyze"], input="y\n")
            assert result.exit_code == 1
            assert "Assert Violation" in result.output
            assert INPUT_RESPONSE.source_list[0] in result.output


def test_solidity_analyze_blocking_blacklist():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(
                cli, ["analyze", "--swc-blacklist", "SWC-110"], input="y\n"
            )
            assert result.exit_code == 0
            assert "Assert Violation" not in result.output
            assert (
                "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol"
                not in result.output
            )


def test_solidity_analyze_blocking_filter():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(
                cli, ["analyze", "--min-severity", "high"], input="y\n"
            )
            assert result.exit_code == 0
            assert "Assert Violation" not in result.output
            assert (
                "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol"
                not in result.output
            )


def test_solidity_analyze_as_arg():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["analyze", "outdated.sol"])
            assert result.exit_code == 0
            assert result.output == ISSUES_TABLE


def test_solidity_analyze_multiple():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            with open("outdated2.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["analyze", "outdated.sol", "outdated2.sol"])
            assert result.exit_code == 0
            assert result.output == ISSUES_TABLE + ISSUES_TABLE


def test_solidity_analyze_missing_version():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file without pragma line
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE[1:])

            result = runner.invoke(cli, ["analyze", "outdated.sol"])
            assert result.exit_code == 2
            assert SOLC_ERROR in result.output
