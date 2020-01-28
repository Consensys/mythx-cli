"""Utility functions for handling API requests and responses."""

from typing import List, Union

import click
from mythx_models.response import DetectedIssuesResponse, Severity

SEVERITY_ORDER = (Severity.UNKNOWN, Severity.NONE, Severity.LOW, Severity.MEDIUM, Severity.HIGH)


def get_source_location_by_offset(source, offset):
    """Retrieve the Solidity source code location based on the source map offset.

    :param source: The Solidity source to analyze
    :param offset: The source map's offset
    :return: The line number
    """

    return source.encode("utf-8")[0:offset].count("\n".encode("utf-8")) + 1


def generate_dashboard_link(uuid: str, staging=False):
    return "https://dashboard.{}mythx.io/#/console/analyses/{}".format("staging." if staging else "", uuid)


def normalize_swc_list(swc_list: Union[str, List[str], None]) -> List[str]:
    if not swc_list:
        return []
    if type(swc_list) == str:
        swc_list = swc_list.split(",")
    swc_list = [str(x).strip().upper() for x in swc_list]
    swc_list = ["SWC-{}".format(x) if not x.startswith("SWC") else x for x in swc_list]

    return swc_list


def set_ci_failure():
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

    This will remove issues of a specific SWC ID or with a too low severity
    from the issue reports of the passed :code:`DetectedIssuesResponse` object.
    The SWC blacklist can be a list of strings in the format "SWC-000" or a
    comma-separated string. "SWC" is case-insensitive and normalized. The SWC
    whitelist works in a similar way, just including selected SWCs into the
    resulting response object.
    """

    min_severity = Severity(min_severity.title()) if min_severity else Severity.UNKNOWN
    swc_blacklist = normalize_swc_list(swc_blacklist)
    swc_whitelist = normalize_swc_list(swc_whitelist)

    new_issues = []
    for report in resp.issue_reports:
        for issue in report.issues:
            is_severe = SEVERITY_ORDER.index(issue.severity) >= SEVERITY_ORDER.index(min_severity)
            not_blacklisted = issue.swc_id not in swc_blacklist
            is_whitelisted = issue.swc_id in swc_whitelist if swc_whitelist else True

            if all((is_severe, is_whitelisted, not_blacklisted)):
                new_issues.append(issue)
                set_ci_failure()

        report.issues = new_issues

    return resp
