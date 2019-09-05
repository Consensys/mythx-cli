from mythx_cli.formatter.base import BaseFormatter
from mythx_models.response import (
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    VersionResponse,
)
from typing import Union, List
import json


class JSONFormatter(BaseFormatter):
    @staticmethod
    def format_analysis_list(
        resp: Union[AnalysisListResponse, List[AnalysisStatusResponse]]
    ) -> str:
        return resp.to_json()

    @staticmethod
    def format_detected_issues(resp: DetectedIssuesResponse) -> str:
        return resp.to_json()

    @staticmethod
    def format_version(resp: VersionResponse) -> str:
        return resp.to_json()
