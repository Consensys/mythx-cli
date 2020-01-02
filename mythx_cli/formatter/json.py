"""This module contains the compressed and pretty-printing JSON formatters."""

import json

from mythx_cli.formatter.base import BaseFormatter
from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    GroupListResponse,
    GroupStatusResponse,
    VersionResponse,
)


class JSONFormatter(BaseFormatter):
    @staticmethod
    def format_group_status(resp: GroupStatusResponse):
        """Format a group status response as compressed JSON."""

        return resp.to_json()

    @staticmethod
    def format_group_list(resp: GroupListResponse):
        """Format a group list response as compressed JSON."""

        return resp.to_json()

    @staticmethod
    def format_analysis_list(resp: AnalysisListResponse) -> str:
        """Format an analysis list response as compressed JSON."""

        return resp.to_json()

    @staticmethod
    def format_analysis_status(resp: AnalysisStatusResponse) -> str:
        """Format an analysis status response as compressed JSON."""

        return resp.to_json()

    @staticmethod
    def format_detected_issues(resp: DetectedIssuesResponse, inp: AnalysisInputResponse) -> str:
        """Format an issue report response as compressed JSON."""

        return resp.to_json()

    @staticmethod
    def format_version(resp: VersionResponse) -> str:
        """Format a version response as compressed JSON."""

        return resp.to_json()


class PrettyJSONFormatter(BaseFormatter):
    @staticmethod
    def _print_as_json(obj):
        """Pretty-print the given object's JSON representation."""

        json_args = {"indent": 2, "sort_keys": True}
        if type(obj) == DetectedIssuesResponse:
            return json.dumps(obj.to_dict(as_list=True), **json_args)
        return json.dumps(obj.to_dict(), **json_args)

    @staticmethod
    def format_group_status(resp: GroupStatusResponse):
        """Format a group status response as pretty-printed JSON."""

        return PrettyJSONFormatter._print_as_json(resp)

    @staticmethod
    def format_group_list(resp: GroupListResponse):
        """Format a group list response as pretty-printed JSON."""

        return PrettyJSONFormatter._print_as_json(resp)

    @staticmethod
    def format_analysis_list(obj: AnalysisListResponse) -> str:
        """Format an analysis list response as pretty-printed JSON."""

        return PrettyJSONFormatter._print_as_json(obj)

    @staticmethod
    def format_analysis_status(obj: AnalysisStatusResponse) -> str:
        """Format an analysis status response as pretty-printed JSON."""

        return PrettyJSONFormatter._print_as_json(obj)

    @staticmethod
    def format_detected_issues(obj: DetectedIssuesResponse, inp: AnalysisInputResponse):
        """Format an issue report response as pretty-printed JSON."""

        return PrettyJSONFormatter._print_as_json(obj)

    @staticmethod
    def format_version(obj: VersionResponse):
        """Format a version response as pretty-printed JSON."""

        return PrettyJSONFormatter._print_as_json(obj)
