"""This module contains a simple text formatter class printing a subset of the
response data."""

from typing import List, Optional, Tuple

from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    GroupListResponse,
    GroupStatusResponse,
    VersionResponse,
)

from mythx_cli.formatter.base import BaseFormatter
from mythx_cli.util import index_by_filename


class SimpleFormatter(BaseFormatter):
    """The simple text formatter.

    This formatter generates simplified text output. It also displays
    the source locations of issues by line in the Solidity source code
    if given. Therefore, this formatter requires the analysis input to
    be given.
    """

    report_requires_input = True

    @staticmethod
    def format_analysis_list(resp: AnalysisListResponse) -> str:
        """Format an analysis list response to a simple text representation."""

        res = []
        for analysis in resp:
            res.append("UUID: {}".format(analysis.uuid))
            res.append("Submitted at: {}".format(analysis.submitted_at))
            res.append("Status: {}".format(analysis.status))
            res.append("")

        return "\n".join(res)

    @staticmethod
    def format_group_status(resp: GroupStatusResponse) -> str:
        """Format a group status response to a simple text representation."""

        res = [
            "ID: {}".format(resp.group.identifier),
            "Name: {}".format(resp.group.name or "<unnamed>"),
            "Created on: {}".format(resp.group.created_at),
            "Status: {}".format(resp.group.status),
            "",
        ]
        return "\n".join(res)

    @staticmethod
    def format_group_list(resp: GroupListResponse) -> str:
        """Format an analysis group response to a simple text
        representation."""

        res = []
        for group in resp:
            res.append("ID: {}".format(group.identifier))
            res.append("Name: {}".format(group.name or "<unnamed>"))
            res.append("Created on: {}".format(group.created_at))
            res.append("Status: {}".format(group.status))
            res.append("")

        return "\n".join(res)

    @staticmethod
    def format_analysis_status(resp: AnalysisStatusResponse) -> str:
        """Format an analysis status response to a simple text
        representation."""

        res = [
            "UUID: {}".format(resp.uuid),
            "Submitted at: {}".format(resp.submitted_at),
            "Status: {}".format(resp.status),
            "",
        ]
        return "\n".join(res)

    @staticmethod
    def format_detected_issues(
        issues_list: List[
            Tuple[DetectedIssuesResponse, Optional[AnalysisInputResponse]]
        ],
        **kwargs,
    ) -> str:
        """Format an issue report to a simple text representation."""

        file_to_issues = index_by_filename(issues_list)
        result = []

        for filename, data in file_to_issues.items():
            result.append(f"Report for {filename}")
            # sort by line number
            data = sorted([o for o in data if o["issues"]], key=lambda x: x["line"])
            for line in data:
                for issue in line["issues"]:
                    result.append(f"Title: {issue['swcTitle']} ({issue['severity']})")
                    result.append(f"Description: {issue['description']['head']}")
                    result.append(f"Line: {line['line']}")
                    result.append("\t" + line["content"].strip() + "\n")

        return "\n".join(result)

    @staticmethod
    def format_version(resp: VersionResponse) -> str:
        """Format a version response to a simple text representation."""

        return "\n".join(
            [
                "API: {}".format(resp.api_version),
                "Harvey: {}".format(resp.harvey_version),
                "Maru: {}".format(resp.maru_version),
                "Mythril: {}".format(resp.mythril_version),
                "Hashed: {}".format(resp.hashed_version),
            ]
        )
