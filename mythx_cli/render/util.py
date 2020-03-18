from typing import List, Optional, Tuple

from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
)

from mythx_cli.formatter import util


def get_analysis_info(
    client,
    uuid: str,
    min_severity: Optional[str],
    swc_blacklist: Optional[List[str]],
    swc_whitelist: Optional[List[str]],
) -> Tuple[AnalysisStatusResponse, DetectedIssuesResponse, AnalysisInputResponse]:
    """Fetch information related to the specified analysis job UUID.

    Given a UUID, this function will query the MythX API for the
    analysis status, the analysis' input data, and the issue report.
    Furthermore, filtering parameters can be passed to remove certain
    SWCs or severities from the returned report.
    """

    resp: DetectedIssuesResponse = client.report(uuid)
    inp: Optional[AnalysisInputResponse] = client.request_by_uuid(uuid)
    status: AnalysisStatusResponse = client.status(uuid)
    util.filter_report(
        resp,
        min_severity=min_severity,
        swc_blacklist=swc_blacklist,
        swc_whitelist=swc_whitelist,
    )
    # extend response with job UUID to keep formatter logic isolated
    resp.uuid = uuid

    return status, resp, inp
