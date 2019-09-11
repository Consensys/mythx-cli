from click.testing import CliRunner
from mythx_cli.cli import cli
from unittest.mock import patch
from mythx_models.response import AnalysisStatusResponse
import json


STATUS_RESPONSE_OBJ = AnalysisStatusResponse.from_dict({"uuid": "381eff48-04db-4f81-a417-8394b6614472", "apiVersion": "v1.4.33-1-g1a235db", "mythrilVersion": "0.21.14", "harveyVersion": "0.0.34", "maruVersion": "0.5.4", "queueTime": 507, "runTime": 30307, "status": "Finished", "submittedAt": "2019-09-05T20:34:27.606Z", "submittedBy": "5d6fca7fef1fc700129b6efa", "clientToolName": "pythx"})
STATUS_RESPONSE_SIMPLE = """UUID: 381eff48-04db-4f81-a417-8394b6614472
Submitted at: 2019-09-05 20:34:27.606000+00:00
Status: Finished

"""


def test_status_simple():
    runner = CliRunner()
    with patch("pythx.Client.status") as status_patch:
        status_patch.return_value = STATUS_RESPONSE_OBJ
        result = runner.invoke(cli, ["status", "381eff48-04db-4f81-a417-8394b6614472"])
        assert result.exit_code == 0
        assert result.output == STATUS_RESPONSE_SIMPLE


def test_status_json():
    runner = CliRunner()
    with patch("pythx.Client.status") as status_patch:
        status_patch.return_value = STATUS_RESPONSE_OBJ
        result = runner.invoke(cli, ["--format", "json", "status", "381eff48-04db-4f81-a417-8394b6614472"])
        assert result.exit_code == 0
        assert json.loads(result.output) == STATUS_RESPONSE_OBJ.to_dict()


def test_status_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.status") as status_patch:
        status_patch.return_value = STATUS_RESPONSE_OBJ
        result = runner.invoke(cli, ["--format", "json-pretty", "status", "381eff48-04db-4f81-a417-8394b6614472"])
        assert result.exit_code == 0
        assert json.loads(result.output) == STATUS_RESPONSE_OBJ.to_dict()
