"""This module contains a tabular data formatter class printing a subset of the
response data."""

from itertools import zip_longest
from os.path import basename
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
from tabulate import tabulate

from mythx_cli.formatter.base import BaseFormatter
from mythx_cli.formatter.util import generate_dashboard_link
from mythx_cli.util import index_by_filename


class TabularFormatter(BaseFormatter):
    """The tabular formatter.

    This formatter displays an ASCII table. It is enabled by default and
    requires the analysis input data to display each issue's line number
    in the source file. It might break on very large field sizes as
    cell-internal line breaks are not supported by the tabulate library
    yet.
    """

    report_requires_input = True

    @staticmethod
    def format_analysis_list(resp: AnalysisListResponse) -> str:
        """Format an analysis list response to a tabular representation."""

        data = [
            (a.uuid, a.status, a.client_tool_name, a.submitted_at)
            for a in resp.analyses
        ]
        return tabulate(data, tablefmt="fancy_grid")

    @staticmethod
    def format_group_list(resp: GroupListResponse) -> str:
        """Format an analysis group response to a tabular representation."""

        data = [
            (
                group.identifier,
                group.status,
                ",".join([basename(x) for x in group.main_source_files]),
                group.created_at,
            )
            for group in resp.groups
        ]
        return tabulate(data, tablefmt="fancy_grid")

    @staticmethod
    def format_group_status(resp: GroupStatusResponse) -> str:
        """Format a group status response to a tabular representation."""

        data = (
            (
                ("ID", resp.identifier),
                ("Name", resp.name or "<unnamed>"),
                (
                    "Creation Date",
                    resp.created_at,
                ),
                ("Created By", resp.created_by),
                ("Progress", "{}/100".format(resp.progress)),
            )
            + tuple(
                zip_longest(("Main Sources",), resp.main_source_files, fillvalue="")
            )
            + (
                ("Status", resp.status.title()),
                ("Queued Analyses", resp.analysis_statistics.queued or 0),
                ("Running Analyses", resp.analysis_statistics.running or 0),
                ("Failed Analyses", resp.analysis_statistics.failed or 0),
                ("Finished Analyses", resp.analysis_statistics.finished or 0),
                ("Total Analyses", resp.analysis_statistics.total or 0),
                (
                    "High Severity Vulnerabilities",
                    resp.vulnerability_statistics.high or 0,
                ),
                (
                    "Medium Severity Vulnerabilities",
                    resp.vulnerability_statistics.medium or 0,
                ),
                (
                    "Low Severity Vulnerabilities",
                    resp.vulnerability_statistics.low or 0,
                ),
                (
                    "Unknown Severity Vulnerabilities",
                    resp.vulnerability_statistics.none or 0,
                ),
            )
        )
        return tabulate(data, tablefmt="fancy_grid")

    @staticmethod
    def format_analysis_status(resp: AnalysisStatusResponse) -> str:
        """Format an analysis status response to a tabular representation."""

        data = (
            ("UUID", resp.uuid),
            ("API Version", resp.api_version),
            ("Harvey Version", resp.harvey_version),
            ("Maru Version", resp.maru_version),
            ("Mythril Version", resp.mythril_version),
            ("Queue Time", resp.queue_time),
            ("Run Time", resp.run_time),
            ("Status", resp.status),
            ("Submitted At", resp.submitted_at),
            ("Submitted By", resp.submitted_by),
            ("Tool Name", resp.client_tool_name),
            ("Group ID", resp.group_id),
            ("Group Name", resp.group_name),
            ("Analysis Mode", resp.analysis_mode),
        )
        return tabulate(data, tablefmt="fancy_grid")

    @staticmethod
    def format_detected_issues(
        issues_list: List[
            Tuple[DetectedIssuesResponse, Optional[AnalysisInputResponse]]
        ],
        **kwargs,
    ) -> str:
        """Format an issue report to a tabular representation."""

        result = []
        file_to_issues = index_by_filename(issues_list)
        table_sort_key = kwargs.pop("table_sort_key", "line")

        for filename, data in file_to_issues.items():
            data = [o for o in data if o["issues"]]
            if not data:
                continue
            result.append(f"Report for {filename}")
            links, lines = set(), set()
            for line in data:
                for issue in line["issues"]:
                    links.add(generate_dashboard_link(issue["uuid"]))
                    lines.add(
                        (
                            line["line"],
                            f"({issue['swcID']}) {issue['swcTitle']}",
                            issue["severity"],
                            issue["description"]["head"],
                        )
                    )

            # sort by line number
            sort_idx = {"line": 0, "title": 1, "severity": 2, "description": 3}[
                table_sort_key
            ]
            lines = sorted(lines, key=lambda x: x[sort_idx])

            result.extend(links)
            result.extend(
                (
                    tabulate(
                        lines,
                        tablefmt="fancy_grid",
                        headers=("Line", "SWC Title", "Severity", "Short Description"),
                    ),
                    "",  # new line after table
                )
            )

        return "\n".join(result)

    @staticmethod
    def format_version(resp: VersionResponse) -> str:
        """Format a version response to a tabular representation."""

        data = ((k.title(), v) for k, v in resp.dict().items())
        return tabulate(data, tablefmt="fancy_grid")
