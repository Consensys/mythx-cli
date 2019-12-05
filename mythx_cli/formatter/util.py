"""Utility functions for handling API requests and responses."""

from typing import List, Union

from mythx_models.response import DetectedIssuesResponse, Severity

SEVERITY_ORDER = (
    Severity.UNKNOWN,
    Severity.NONE,
    Severity.LOW,
    Severity.MEDIUM,
    Severity.HIGH,
)


def get_source_location_by_offset(source, offset):
    """Retrieve the Solidity source code location based on the source map offset.

    :param source: The Solidity source to analyze
    :param offset: The source map's offset
    :return: The line number
    """

    return source.encode("utf-8")[0:offset].count("\n".encode("utf-8")) + 1


def generate_dashboard_link(uuid: str, staging=False):
    return "https://dashboard.{}mythx.io/#/console/analyses/{}".format(
        "staging." if staging else "", uuid
    )


def filter_report(
    resp: DetectedIssuesResponse,
    min_severity: Union[str, Severity] = None,
    swc_blacklist: List[str] = None,
):
    """Filter issues based on an SWC blacklist and minimum severity.

    This will remove issues of a specific SWC ID or with a too low severity
    from the issue reports of the passed :code:`DetectedIssuesResponse` object.
    The SWC blacklist can be a list of strings in the format "SWC-000" or a
    comma-separated string. "SWC" is case-insensitive and normalized.
    """

    min_severity = Severity(min_severity.title()) if min_severity else Severity.UNKNOWN
    swc_blacklist = swc_blacklist or []

    if type(swc_blacklist) == str:
        swc_blacklist = swc_blacklist.split(",")
    swc_blacklist = [str(x).strip().upper() for x in swc_blacklist]
    swc_blacklist = [
        "SWC-{}".format(x) if not x.startswith("SWC") else x for x in swc_blacklist
    ]

    new_issues = []
    for report in resp.issue_reports:
        for issue in report.issues:
            is_severe = SEVERITY_ORDER.index(issue.severity) >= SEVERITY_ORDER.index(
                min_severity
            )
            if issue.swc_id not in swc_blacklist and is_severe:
                new_issues.append(issue)
        report.issues = new_issues

    return resp
