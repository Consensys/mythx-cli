import json
from typing import List, Union

from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    VersionResponse,
)

from mythx_cli.formatter.base import BaseFormatter


class JSONFormatter(BaseFormatter):
    @staticmethod
    def format_analysis_list(resp: AnalysisListResponse) -> str:
        return resp.to_json()

    @staticmethod
    def format_analysis_status(resp: AnalysisStatusResponse) -> str:
        return resp.to_json()

    @staticmethod
    def format_detected_issues(
        resp: DetectedIssuesResponse, inp: AnalysisInputResponse
    ) -> str:
        return resp.to_json()

    @staticmethod
    def format_version(resp: VersionResponse) -> str:
        return resp.to_json()


class PrettyJSONFormatter(BaseFormatter):
    @staticmethod
    def _print_as_json(obj):
        json_args = {"indent": 2, "sort_keys": True}
        if type(obj) == DetectedIssuesResponse:
            return json.dumps(obj.to_dict(as_list=True), **json_args)
        return json.dumps(obj.to_dict(), **json_args)

    @staticmethod
    def format_analysis_list(obj: AnalysisListResponse) -> str:
        return PrettyJSONFormatter._print_as_json(obj)

    @staticmethod
    def format_analysis_status(obj: AnalysisStatusResponse) -> str:
        return PrettyJSONFormatter._print_as_json(obj)

    @staticmethod
    def format_detected_issues(obj: DetectedIssuesResponse, inp: AnalysisInputResponse):
        return PrettyJSONFormatter._print_as_json(obj)

    @staticmethod
    def format_version(obj: VersionResponse):
        return PrettyJSONFormatter._print_as_json(obj)
