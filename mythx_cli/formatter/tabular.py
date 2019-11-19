"""This module contains a tabular data formatter class printing a subset of the response data."""

from collections import defaultdict
from os.path import basename

import click
from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    GroupListResponse,
    VersionResponse,
)
from tabulate import tabulate

from .base import BaseFormatter
from .util import generate_dashboard_link, get_source_location_by_offset


class TabularFormatter(BaseFormatter):
    @staticmethod
    def format_analysis_list(resp: AnalysisListResponse) -> str:
        """Format an analysis list response to a tabular representation."""

        data = [
            (a.uuid, a.status, a.client_tool_name, a.submitted_at)
            for a in resp.analyses
        ]
        return tabulate(data, tablefmt="fancy_grid")

    @staticmethod
    def format_group_list(resp: GroupListResponse):
        """Format an analysis group response to a tabular representation."""

        data = [
            (
                group.identifier,
                group.status,
                ",".join([basename(x) for x in group.main_source_files]),
                group.created_at.strftime("%Y-%m-%d %H:%M:%S%z"),
            )
            for group in resp.groups
        ]
        return tabulate(data, tablefmt="fancy_grid")

    @staticmethod
    def format_analysis_status(resp: AnalysisStatusResponse) -> str:
        """Format an analysis status response to a tabular representation."""

        data = ((k, v) for k, v in resp.analysis.to_dict().items())
        return tabulate(data, tablefmt="fancy_grid")

    @staticmethod
    def format_detected_issues(
        resp: DetectedIssuesResponse, inp: AnalysisInputResponse
    ) -> str:
        """Format an issue report to a tabular representation."""

        res = []
        file_to_issue = defaultdict(list)
        for report in resp.issue_reports:
            for issue in report.issues:
                # handle fake issues for trial users
                if issue.swc_id == "" and issue.swc_title == "" and not issue.locations:
                    res.extend((issue.description_long, ""))
                for loc in issue.locations:
                    for c in loc.source_map.components:
                        # This is so nested, a barn swallow might be hidden somewhere.
                        source_list = loc.source_list or report.source_list
                        if not (source_list and 0 >= c.file_id < len(source_list)):
                            continue
                        filename = report.source_list[c.file_id]
                        if not inp.sources or filename not in inp.sources:
                            line = "bytecode offset {}".format(c.offset)
                        else:
                            line = get_source_location_by_offset(
                                inp.sources[filename]["source"], c.offset
                            )
                        file_to_issue[filename].append(
                            (
                                line,
                                issue.swc_title,
                                issue.severity,
                                issue.description_short,
                            )
                        )

        ctx = click.get_current_context()
        for filename, data in file_to_issue.items():
            res.append("Report for {}".format(filename))
            res.extend(
                (
                    generate_dashboard_link(ctx.obj["uuid"]),
                    tabulate(
                        data,
                        tablefmt="fancy_grid",
                        headers=("Line", "SWC Title", "Severity", "Short Description"),
                    ),
                )
            )

        return "\n".join(res)

    @staticmethod
    def format_version(resp: VersionResponse) -> str:
        """Format a version response to a tabular representation."""

        data = ((k.title(), v) for k, v in resp.to_dict().items())
        return tabulate(data, tablefmt="fancy_grid")
