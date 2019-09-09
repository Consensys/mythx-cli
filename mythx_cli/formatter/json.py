from mythx_cli.formatter.base import BaseFormatter
from mythx_models.response import (
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    VersionResponse,
    AnalysisInputResponse
)
from typing import Union, List


class JSONFormatter(BaseFormatter):
    @staticmethod
    def format_analysis_list(
        resp: Union[AnalysisListResponse, List[AnalysisStatusResponse]]
    ) -> str:
        return resp.to_json()

    @staticmethod
    def format_detected_issues(resp: DetectedIssuesResponse, inp: AnalysisInputResponse) -> str:
        return resp.to_json()

    @staticmethod
    def format_version(resp: VersionResponse) -> str:
        return resp.to_json()
