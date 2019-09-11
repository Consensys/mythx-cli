import json
from unittest.mock import patch

from click.testing import CliRunner
from mythx_models.response import AnalysisListResponse

from mythx_cli.cli import cli

LIST_RESPONSE_OBJ = AnalysisListResponse.from_dict(
    {
        "analyses": [
            {
                "uuid": "ed6b2347-68b7-4ef3-b85c-4340ae404867",
                "apiVersion": "v1.4.33-37-g0fb1a8f",
                "mythrilVersion": "0.21.14",
                "harveyVersion": "0.0.34",
                "maruVersion": "0.5.4",
                "queueTime": 1400,
                "runTime": 4267,
                "status": "Finished",
                "submittedAt": "2019-09-10T17:15:11.267Z",
                "submittedBy": "5d6fca7fef1fc700129b6efa",
                "clientToolName": "pythx",
            },
            {
                "uuid": "e6566fc9-ebc1-4d04-ae5d-6f3b1873290a",
                "apiVersion": "v1.4.33-37-g0fb1a8f",
                "mythrilVersion": "0.21.14",
                "harveyVersion": "0.0.34",
                "maruVersion": "0.5.4",
                "queueTime": 2015,
                "runTime": 28427,
                "status": "Finished",
                "submittedAt": "2019-09-10T17:15:10.645Z",
                "submittedBy": "5d6fca7fef1fc700129b6efa",
                "clientToolName": "pythx",
            },
            {
                "uuid": "b87f0174-ef09-4fac-9d3c-97c3fdf01782",
                "apiVersion": "v1.4.33-37-g0fb1a8f",
                "mythrilVersion": "0.21.14",
                "harveyVersion": "0.0.34",
                "maruVersion": "0.5.4",
                "queueTime": 2816,
                "runTime": 52405,
                "status": "Finished",
                "submittedAt": "2019-09-10T17:15:09.836Z",
                "submittedBy": "5d6fca7fef1fc700129b6efa",
                "clientToolName": "pythx",
            },
            {
                "uuid": "2056caf6-25d7-4ce8-a633-d10a8746d5dd",
                "apiVersion": "v1.4.33-37-g0fb1a8f",
                "mythrilVersion": "0.21.14",
                "harveyVersion": "0.0.34",
                "maruVersion": "0.5.4",
                "queueTime": 80698393,
                "runTime": -80698393,
                "status": "Finished",
                "submittedAt": "2019-09-10T17:12:42.341Z",
                "submittedBy": "5d6fca7fef1fc700129b6efa",
                "clientToolName": "pythx",
            },
            {
                "uuid": "63eb5611-ba4b-46e8-9e40-f735a0b86fd9",
                "apiVersion": "v1.4.33-37-g0fb1a8f",
                "mythrilVersion": "0.21.14",
                "harveyVersion": "0.0.34",
                "maruVersion": "0.5.4",
                "queueTime": 1158,
                "runTime": 130267,
                "status": "Finished",
                "submittedAt": "2019-09-10T17:12:41.645Z",
                "submittedBy": "5d6fca7fef1fc700129b6efa",
                "clientToolName": "pythx",
            },
        ],
        "total": 5,
    }
)
LIST_RESPONSE_SIMPLE = """UUID: ed6b2347-68b7-4ef3-b85c-4340ae404867
Submitted at: 2019-09-10 17:15:11.267000+00:00
Status: Finished

UUID: e6566fc9-ebc1-4d04-ae5d-6f3b1873290a
Submitted at: 2019-09-10 17:15:10.645000+00:00
Status: Finished

UUID: b87f0174-ef09-4fac-9d3c-97c3fdf01782
Submitted at: 2019-09-10 17:15:09.836000+00:00
Status: Finished

UUID: 2056caf6-25d7-4ce8-a633-d10a8746d5dd
Submitted at: 2019-09-10 17:12:42.341000+00:00
Status: Finished

UUID: 63eb5611-ba4b-46e8-9e40-f735a0b86fd9
Submitted at: 2019-09-10 17:12:41.645000+00:00
Status: Finished

"""


def test_list_simple():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = LIST_RESPONSE_OBJ
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert result.output == LIST_RESPONSE_SIMPLE


def test_list_json():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = LIST_RESPONSE_OBJ
        result = runner.invoke(cli, ["--format", "json", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == LIST_RESPONSE_OBJ.to_dict()


def test_list_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = LIST_RESPONSE_OBJ
        result = runner.invoke(cli, ["--format", "json-pretty", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == LIST_RESPONSE_OBJ.to_dict()
