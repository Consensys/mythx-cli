from mythx_cli.formatter.json import JSONFormatter
from mythx_models.response import DetectedIssuesResponse, AnalysisInputResponse
from mythx_models.response.issue import Severity, SourceType
import json


class SonarQubeFormatter(JSONFormatter):
    @staticmethod
    def format_detected_issues(resp: DetectedIssuesResponse, inp: AnalysisInputResponse) -> str:
        new_reports = []
        for report in resp.issue_reports:
            for issue in report:
                new_issue = {}
                for loc in issue.decoded_locations:
                    for raw_loc in issue.locations:
                        if raw_loc.source_type != SourceType.SOLIDITY_FILE:
                            continue
                        new_issue["onInputFile"] = raw_loc.source_list[raw_loc.source_map.components[0].file_id]
                        new_issue["atLineNr"] = loc.start_line

                new_issue.update({
                    "linterName": "mythx",
                    "forRule": issue.swc_id,
                    "ruleType": issue.severity.name,
                    "remediationEffortMinutes": 0,
                    "severity": "vulnerability" if issue.severity == Severity.HIGH else issue.severity.name,
                    "message": issue.description_long,
                })
                new_reports.append(new_issue)

        return json.dumps(new_reports)
