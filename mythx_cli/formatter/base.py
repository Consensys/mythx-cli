import abc
from mythx_models.response import (
    AnalysisListResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
    VersionResponse,
    AnalysisInputResponse
)
from typing import Union, List


class BaseFormatter(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def format_analysis_list(
        obj: Union[AnalysisListResponse, List[AnalysisStatusResponse]]
    ):
        pass

    @classmethod
    def format_analysis_status(cls, resp: AnalysisStatusResponse) -> str:
        return cls.format_analysis_list([resp])

    @staticmethod
    @abc.abstractmethod
    def format_detected_issues(obj: DetectedIssuesResponse, inp: AnalysisInputResponse):
        pass

    @staticmethod
    @abc.abstractmethod
    def format_version(obj: VersionResponse):
        pass
