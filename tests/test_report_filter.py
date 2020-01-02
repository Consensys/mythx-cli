from copy import deepcopy

import pytest

from mythx_cli.formatter.util import filter_report
from mythx_models.response import DetectedIssuesResponse

from .common import get_test_case

# contains SWC-110
RESPONSE = get_test_case("testdata/detected-issues-response.json", DetectedIssuesResponse)


@pytest.mark.parametrize(
    "blacklist,contained",
    (
        ("SWC-110", False),
        ("swc-110", False),
        ("swc-101,swc-110,swc-123", False),
        ("swc-123", True),
        ("SWC-123", True),
        ("SWC-123,swc-123", True),
        ("invalid", True),
        (["110"], False),
        (["110", "123"], False),
        (["123"], True),
    ),
)
def test_report_filter_blacklist(blacklist, contained):
    resp = deepcopy(RESPONSE)
    filter_report(resp, swc_blacklist=blacklist)

    if contained:
        assert "SWC-110" in resp
    else:
        assert "SWC-110" not in resp


@pytest.mark.parametrize(
    "min_sev,contained",
    (
        ("unknown", True),
        ("Unknown", True),
        ("UNKNOWN", True),
        ("none", True),
        ("None", True),
        ("NONE", True),
        ("low", True),
        ("Low", True),
        ("LOW", True),
        ("medium", False),
        ("Medium", False),
        ("MEDIUM", False),
        ("high", False),
        ("High", False),
        ("HIGH", False),
    ),
)
def test_report_filter_min_severity(min_sev, contained):
    resp = deepcopy(RESPONSE)
    filter_report(resp, min_severity=min_sev)

    if contained:
        assert "SWC-110" in resp
    else:
        assert "SWC-110" not in resp
