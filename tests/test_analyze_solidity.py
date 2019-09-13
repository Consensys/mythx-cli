import json
import os
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli

from .testdata import (
    ARTIFACT_DATA,
    INPUT_RESPONSE_OBJ,
    ISSUES_RESPONSE_OBJ,
    ISSUES_RESPONSE_SIMPLE,
    SUBMISSION_RESPONSE_OBJ,
)

SOLIDITY_CODE = """pragma solidity 0.4.13;

contract OutdatedCompilerVersion {
    uint public x = 1;
}
"""
SOLC_ERROR = "No pragma found - please specify a solc version with --solc-version"


def test_solidity_analyze_async():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE_OBJ
        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["analyze", "--async"], input="y\n")
            assert result.exit_code == 0
            assert SUBMISSION_RESPONSE_OBJ.analysis.uuid in result.output


def test_solidity_analyze_blocking():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["analyze"], input="y\n")
            assert result.exit_code == 0
            assert ISSUES_RESPONSE_SIMPLE in result.output


def test_solidity_analyze_as_arg():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["analyze", "outdated.sol"])
            assert result.exit_code == 0
            assert result.output == ISSUES_RESPONSE_SIMPLE


def test_solidity_analyze_multiple():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            with open("outdated2.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["analyze", "outdated.sol", "outdated2.sol"])
            assert result.exit_code == 0
            assert result.output == ISSUES_RESPONSE_SIMPLE + ISSUES_RESPONSE_SIMPLE


def test_solidity_analyze_missing_version():
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

        with runner.isolated_filesystem():
            # initialize sample solidity file without pragma line
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE[1:])

            result = runner.invoke(cli, ["analyze", "outdated.sol"])
            assert result.exit_code == 2
            assert SOLC_ERROR in result.output
