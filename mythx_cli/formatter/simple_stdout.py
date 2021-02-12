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
    ProjectListResponse,
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
        for analysis in resp.analyses:
            res.append("UUID: {}".format(analysis.uuid))
            res.append("Submitted at: {}".format(analysis.submitted_at))
            res.append("Status: {}".format(analysis.status))
            res.append("")

        return "\n".join(res)

    @staticmethod
    def format_group_status(resp: GroupStatusResponse) -> str:
        """Format a group status response to a simple text representation."""

        res = [
            "ID: {}".format(resp.identifier),
            "Name: {}".format(resp.name or "<unnamed>"),
            "Created on: {}".format(resp.created_at),
            "Status: {}".format(resp.status),
            "",
        ]
        return "\n".join(res)

    @staticmethod
    def format_group_list(resp: GroupListResponse) -> str:
        """Format an analysis group response to a simple text
        representation."""

        res = []
        for group in resp.groups:
            res.append("ID: {}".format(group.identifier))
            res.append("Name: {}".format(group.name or "<unnamed>"))
            res.append("Created on: {}".format(group.created_at))
            res.append("Status: {}".format(group.status))
            res.append("")

        return "\n".join(res)

    @staticmethod
    def format_project_list(resp: ProjectListResponse) -> str:
        """Format an analysis group response to a simple text
        representation."""

        res = []
        for project in resp.projects:
            res.append("ID: {}".format(project.id))
            res.append("Name: {}".format(project.name or "<unnamed>"))
            res.append("Created on: {}".format(project.created))
            res.append("Modified: {}".format(project.modified))
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
            Tuple[str, DetectedIssuesResponse, Optional[AnalysisInputResponse]]
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
                "API: {}".format(resp.api),
                "Harvey: {}".format(resp.harvey),
                "Maru: {}".format(resp.maru),
                "Mythril: {}".format(resp.mythril),
                "Hashed: {}".format(resp.hash),
            ]
        )
