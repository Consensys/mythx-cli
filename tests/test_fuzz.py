import pytest
from click.testing import CliRunner

from mythx_cli.cli import cli


@pytest.mark.parametrize("keyword", ("run", "setup"))
def test_fuzz_subcommands_present(keyword):
    runner = CliRunner()

    result = runner.invoke(cli, ["fuzz", "--help"])

    assert keyword in result.output
