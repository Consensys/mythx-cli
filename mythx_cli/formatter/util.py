"""Utility functions for handling API requests and responses."""

from collections import defaultdict
from typing import List, Optional, Tuple, Union

import click
from mythx_models.response import (
    AnalysisInputResponse,
    DetectedIssuesResponse,
    Severity,
)

SEVERITY_ORDER = (
    Severity.UNKNOWN,
    Severity.NONE,
    Severity.LOW,
    Severity.MEDIUM,
    Severity.HIGH,
)


def index_by_filename(
    issues_list: List[Tuple[DetectedIssuesResponse, Optional[AnalysisInputResponse]]]
):
    """Index the given report/input responses by filename.

    This will return a simplified, unified representation of the report/input payloads
    returned by the MythX API. It is a mapping from filename to an iterable of issue
    objects, which contain the report UUID, SWC ID, SWC title, short and long
    description, severity, as well as the issue's line location in the source code.

    This representation is meant to be passed on to the respective formatter, which
    them visualizes the data.

    :param issues_list: A list of two-tuples containing report and input responses
    :return: A simplified mapping indexing issues by their file path
    """
    file_to_issues = defaultdict(list)

    for resp, inp in issues_list:
        for report in resp.issue_reports:
            for issue in report.issues:
                issue_entry = {
                    "uuid": resp.uuid,
                    "swcID": issue.swc_id,
                    "swcTitle": issue.swc_title,
                    "description": {
                        "head": issue.description_short,
                        "tail": issue.description_long,
                    },
                    "severity": issue.severity,
                }

                if issue.swc_id == "" or issue.swc_title == "" or not issue.locations:
                    # skip issues with missing SWC or location data
                    continue

                source_formats = [loc.source_format for loc in issue.locations]
                for loc in issue.locations:
                    if loc.source_format != "text" and "text" in source_formats:
                        # skip non-text locations when we have one attached to the issue
                        continue

                    for c in loc.source_map.components:
                        source_list = loc.source_list or report.source_list
                        if not (source_list and 0 <= c.file_id < len(source_list)):
                            # skip issues whose srcmap file ID if out of range of the source list
                            continue
                        filename = source_list[c.file_id]

                        if not inp.sources or filename not in inp.sources:
                            # skip issues that can't be decoded to source location
                            continue

                        line = get_source_location_by_offset(
                            inp.sources[filename]["source"], c.offset
                        )
                        issue_entry["line"] = line
                        issue_entry["snippet"] = inp.sources[filename]["source"].split(
                            "\n"
                        )[line - 1]
                        file_to_issues[filename].append(issue_entry)

    return file_to_issues


def get_source_location_by_offset(source: str, offset: int) -> int:
    """Retrieve the Solidity source code location based on the source map
    offset.

    :param source: The Solidity source to analyze
    :param offset: The source map's offset
    :return: The offset's source line number equivalent
    """

    return source.encode("utf-8")[0:offset].count("\n".encode("utf-8")) + 1


def generate_dashboard_link(uuid: str) -> str:
    """Generate a MythX dashboard link for an analysis job.

    This method will generate a link to an analysis job on the official
    MythX dashboard production setup. Custom deployment locations are currently
    not supported by this function (but available at mythx.io).
    :param uuid: The analysis job's UUID
    :return: The analysis job's dashboard link
    """
    return "https://dashboard.mythx.io/#/console/analyses/{}".format(uuid)


def normalize_swc_list(swc_list: Union[str, List[str], None]) -> List[str]:
    """Normalize a list of SWC IDs.

    This method normalizes a list of SWC ID definitions, making SWC-101, swc-101,
    and 101 equivalent.
    :param swc_list: The list of SWC IDs as strings
    :return: The normalized SWC ID list as SWC-XXX
    """
    if not swc_list:
        return []
    if type(swc_list) == str:
        swc_list = swc_list.split(",")
    swc_list = [str(x).strip().upper() for x in swc_list]
    swc_list = ["SWC-{}".format(x) if not x.startswith("SWC") else x for x in swc_list]

    return swc_list


def set_ci_failure() -> None:
    """Based on the current context, set the return code to 1.

    This method sets the return code to 1. It is called by the respective
    subcommands (analyze and report) in case a severe issue has been found (as
    specified by the user) if the CI flag is passed. This will make the MythX
    CLI fail when running on a CI server. If no context is available, this
    function assumes that it is running outside a CLI scenario (e.g. a test
    setup) and will not do anything.
    """
    try:
        ctx = click.get_current_context()
        if ctx.obj["ci"]:
            ctx.obj["retval"] = 1
    except RuntimeError:
        # skip failure when there is no active click context
        # i.e. the method has been called outside the click
        # application.
        pass


def filter_report(
    resp: DetectedIssuesResponse,
    min_severity: Union[str, Severity] = None,
    swc_blacklist: Union[str, List[str]] = None,
    swc_whitelist: Union[str, List[str]] = None,
) -> DetectedIssuesResponse:
    """Filter issues based on an SWC blacklist and minimum severity.

    This will remove issues of a specific SWC ID or with a too low
    severity from the issue reports of the passed
    :code:`DetectedIssuesResponse` object. The SWC blacklist can be a
    list of strings in the format "SWC-000" or a comma-separated string.
    "SWC" is case-insensitive and normalized. The SWC whitelist works in
    a similar way, just including selected SWCs into the resulting
    response object.

    :param resp: The issue report of an analysis job
    :param min_severity: Ignore SWC IDs below the designated level
    :param swc_blacklist: A comma-separated list of SWC IDs to ignore
    :param swc_whitelist: A comma-separated list of SWC IDs to include
    :return: The filtered issue report
    """

    min_severity = Severity(min_severity.title()) if min_severity else Severity.UNKNOWN
    swc_blacklist = normalize_swc_list(swc_blacklist)
    swc_whitelist = normalize_swc_list(swc_whitelist)

    new_issues = []
    for report in resp.issue_reports:
        for issue in report.issues:
            is_severe = SEVERITY_ORDER.index(issue.severity) >= SEVERITY_ORDER.index(
                min_severity
            )
            not_blacklisted = issue.swc_id not in swc_blacklist
            is_whitelisted = issue.swc_id in swc_whitelist if swc_whitelist else True

            if all((is_severe, is_whitelisted, not_blacklisted)):
                new_issues.append(issue)
                set_ci_failure()

        report.issues = new_issues

    return resp
