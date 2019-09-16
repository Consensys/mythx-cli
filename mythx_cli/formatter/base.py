"""This module contains the base formatter interface."""

import abc

from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    VersionResponse,
)


class BaseFormatter(abc.ABC):
    """The base formatter interface for printing various response types."""

    @staticmethod
    @abc.abstractmethod
    def format_analysis_list(obj: AnalysisListResponse):
        """Format an analysis list response."""

        pass  # pragma: no cover

    @staticmethod
    def format_analysis_status(resp: AnalysisStatusResponse) -> str:
        """Format an analysis status response."""

        pass  # pragma: no cover

    @staticmethod
    @abc.abstractmethod
    def format_detected_issues(obj: DetectedIssuesResponse, inp: AnalysisInputResponse):
        """Format an issue report response."""

        pass  # pragma: no cover

    @staticmethod
    @abc.abstractmethod
    def format_version(obj: VersionResponse):
        """Format a version response."""

        pass  # pragma: no cover
