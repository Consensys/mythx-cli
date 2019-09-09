from mythx_cli.formatter.base import BaseFormatter
from mythx_models.response import (
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    VersionResponse,
    AnalysisInputResponse
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
    def format_detected_issues(resp: DetectedIssuesResponse, inp: AnalysisInputResponse) -> str:
        return resp.to_json()

    @staticmethod
    def format_version(resp: VersionResponse) -> str:
        return resp.to_json()


class PrettyJSONFormatter(BaseFormatter):
    @staticmethod
    def _print_as_json(obj):
        return json.dumps(obj.to_dict(), indent=2, sort_keys=True)

    @staticmethod
    def format_analysis_list(
        obj: Union[AnalysisListResponse, List[AnalysisStatusResponse]]
    ) -> str:
        return PrettyJSONFormatter._print_as_json(obj)

    @staticmethod
    def format_detected_issues(obj: DetectedIssuesResponse, inp: AnalysisInputResponse):
        return PrettyJSONFormatter._print_as_json(obj)

    @staticmethod
    def format_version(obj: VersionResponse):
        return PrettyJSONFormatter._print_as_json(obj)
