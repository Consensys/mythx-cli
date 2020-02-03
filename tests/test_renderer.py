from .common import mock_context, get_test_case
from click.testing import CliRunner
from mythx_cli.cli import cli
from mythx_models.response import AnalysisInputResponse, DetectedIssuesResponse


TEST_GROUP_ID = "5E36AE133FB6020011A6B13C"
INPUT_RESPONSE: AnalysisInputResponse = get_test_case("testdata/analysis-input-response.json", AnalysisInputResponse)
ISSUES_RESPONSE: DetectedIssuesResponse = get_test_case("testdata/detected-issues-response.json", DetectedIssuesResponse)


def assert_content(data):
    assert TEST_GROUP_ID in data
    for item in INPUT_RESPONSE.source_list:
        assert item in data
    assert INPUT_RESPONSE.bytecode in data
    for filename in INPUT_RESPONSE.sources.keys():
        assert filename in data
    for source in map(lambda x: x["source"], INPUT_RESPONSE.sources.values()):
        for line in source.split("\n"):
            assert line in data
    for issue in ISSUES_RESPONSE:
        assert issue.swc_id in data
        assert issue.swc_title in data


def test_renderer():
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        result = runner.invoke(cli, ["--output=test.html", "render", TEST_GROUP_ID])
        with open("test.html") as f:
            data = f.read()

        assert_content(data)
        assert result.exit_code == 0
