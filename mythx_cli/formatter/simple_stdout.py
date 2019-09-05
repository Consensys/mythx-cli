from mythx_cli.formatter.base import BaseFormatter
from mythx_models.response import (
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    VersionResponse,
)
from typing import Union, List


class SimpleFormatter(BaseFormatter):
    @staticmethod
    def format_analysis_list(
        resp: Union[AnalysisListResponse, List[AnalysisStatusResponse]]
    ) -> str:
        res = []
        for analysis in resp:
            res.append("UUID: {}".format(analysis.uuid))
            res.append("Submitted at: {}".format(analysis.submitted_at))
            res.append("Status: {}".format(analysis.status))
            res.append("")

        return "\n".join(res)

    @staticmethod
    def format_detected_issues(resp: DetectedIssuesResponse) -> str:
        res = []
        for issue in resp:
            res.append("Title: {}".format(issue.swc_title or "-"))
            res.append("Description: {}".format(issue.description_long))
            # TODO: Add location stuff from PythX CLI PoC and moar data
            res.append("")
        return "\n".join(res)

    @staticmethod
    def format_version(resp: VersionResponse) -> str:
        return "\n".join(
            [
                "API: {}".format(resp.api_version),
                "Harvey: {}".format(resp.harvey_version),
                "Maru: {}".format(resp.maru_version),
                "Mythril: {}".format(resp.mythril_version),
                "Hashed: {}".format(resp.hashed_version),
            ]
        )
