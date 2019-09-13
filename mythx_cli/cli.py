# -*- coding: utf-8 -*-

"""Console script for mythx_cli."""
import logging
import sys
import time
from glob import glob
from pathlib import Path

import click
from mythx_models.response import AnalysisListResponse
from pythx import Client, MythXAPIError

from mythx_cli.formatter import FORMAT_RESOLVER
from mythx_cli.payload import (
    generate_bytecode_payload,
    generate_solidity_payload,
    generate_truffle_payload,
)

LOGGER = logging.getLogger("mythx-cli")
logging.basicConfig(level=logging.WARNING)


@click.group()
@click.option(
    "--debug/--no-debug",
    default=False,
    envvar="MYTHX_DEBUG",
    help="Provide additional debug output",
)
@click.option(
    "--access-token",
    envvar="MYTHX_ACCESS_TOKEN",
    help="Your access token generated from the MythX dashboard",
)
@click.option(
    "--staging/--production",
    default=False,
    hidden=True,
    envvar="MYTHX_STAGING",
    help="Use the MythX staging environment",
)
@click.option(
    "--format",
    "fmt",
    default="simple",
    type=click.Choice(FORMAT_RESOLVER.keys()),
    help="The format to display the results in",
)
@click.pass_context
def cli(ctx, **kwargs):
    """Console script for mythx_cli."""

    ctx.obj = dict(kwargs)
    if kwargs["access_token"] is not None:
        ctx.obj["client"] = Client(
            access_token=kwargs["access_token"], staging=kwargs["staging"]
        )
    else:
        # default to trial user client
        ctx.obj["client"] = Client(
            eth_address="0x0000000000000000000000000000000000000000",
            password="trial",
            staging=kwargs["staging"],
        )
    if kwargs["debug"]:
        for name in logging.root.manager.loggerDict:
            logging.getLogger(name).setLevel(logging.DEBUG)

    return 0


def find_truffle_artifacts(project_dir):
    """Look for a Truffle build folder and return all relevant JSON artifacts.
    This function will skip the Migrations.json file and return all other paths
    under <project-dir>/build/contracts/.
    """

    output_pattern = Path(project_dir) / "build" / "contracts" / "*.json"
    artifact_files = list(glob(str(output_pattern.absolute())))
    if not artifact_files:
        return None

    return [f for f in artifact_files if not f.endswith("Migrations.json")]


def find_solidity_files(project_dir):
    output_pattern = Path(project_dir) / "*.sol"
    artifact_files = list(glob(str(output_pattern.absolute())))
    if not artifact_files:
        return None

    return artifact_files


@cli.command()
@click.argument(
    "target", default=None, nargs=-1, required=False  # allow multiple targets
)
@click.option(
    "--async/--wait",  # TODO: make default on full
    "async_flag",
    help="Submit the job and print the UUID, or wait for execution to finish",
)
@click.option("--mode", type=click.Choice(["quick", "full"]), default="quick")
@click.pass_obj
def analyze(ctx, target, async_flag, mode):
    jobs = []

    if not target:
        if Path("truffle-config.js").exists() or Path("truffle.js").exists():
            files = find_truffle_artifacts(Path.cwd())
            if not files:
                raise click.exceptions.UsageError(
                    "Could not find any truffle artifacts. Are you in the project root? Did you run truffle compile?"
                )
            LOGGER.debug(
                "Detected Truffle project with files:\n{}".format("\n".join(files))
            )
            for file in files:
                jobs.append(generate_truffle_payload(file))

        elif list(glob("*.sol")):
            files = find_solidity_files(Path.cwd())
            click.confirm(
                "Do you really want to submit {} Solidity files?".format(len(files))
            )
            LOGGER.debug("Found Solidity files to submit:\n{}".format("\n".join(files)))
            for file in files:
                jobs.append(generate_solidity_payload(file))
        else:
            raise click.exceptions.UsageError(
                "No argument given and unable to detect Truffle project or Solidity files"
            )
    else:
        for target_elem in target:
            if target_elem.startswith("0x"):
                LOGGER.debug("Identified target {} as bytecode".format(target_elem))
                jobs.append(generate_bytecode_payload(target_elem))
                continue
            elif Path(target_elem).is_file() and Path(target_elem).suffix == ".sol":
                LOGGER.debug(
                    "Trying to interpret {} as a solidity file".format(target_elem)
                )
                jobs.append(generate_solidity_payload(target_elem))
                continue
            else:
                raise click.exceptions.UsageError(
                    "Could not interpret argument {} as bytecode or Solidity file".format(
                        target_elem
                    )
                )

    uuids = []
    with click.progressbar(jobs) as bar:
        for job in bar:
            # attach execution mode, submit, poll
            job.update({"analysis_mode": mode})
            resp = ctx["client"].analyze(**job)
            uuids.append(resp.uuid)

    if async_flag:
        click.echo("\n".join(uuids))
        return

    for uuid in uuids:
        while not ctx["client"].analysis_ready(uuid):
            # TODO: Add poll interval option
            time.sleep(3)
        resp = ctx["client"].report(uuid)
        inp = ctx["client"].request_by_uuid(uuid)
        ctx["uuid"] = uuid
        click.echo(FORMAT_RESOLVER[ctx["fmt"]].format_detected_issues(resp, inp))


@cli.command()
@click.argument("uuids", default=None, nargs=-1)
@click.pass_obj
def status(ctx, uuids):
    for uuid in uuids:
        resp = ctx["client"].status(uuid)
        click.echo(FORMAT_RESOLVER[ctx["fmt"]].format_analysis_status(resp))


@cli.command(name="list")
@click.option(
    "--number",
    default=5,
    type=click.IntRange(min=1, max=100),  # ~ 5 requests à 20 entries
    help="The number of most recent analysis jobs to display",
)
@click.pass_obj
def list_(ctx, number):
    result = AnalysisListResponse(analyses=[], total=0)
    try:
        offset = 0
        while True:
            resp = ctx["client"].analysis_list(offset=offset)
            offset += len(resp.analyses)
            result.analyses.extend(resp.analyses)
            if len(result.analyses) >= number:
                break

        # trim result to desired result number
        LOGGER.debug(resp.total)
        result = AnalysisListResponse(analyses=result[:number], total=resp.total)
    except MythXAPIError:
        raise click.UsageError(
            (
                "This functionality is only available to registered users. "
                "Head over to https://mythx.io/ and register a free account to "
                "list your past analyses. Alternatively, you can look up the "
                "status of a specific job by calling 'mythx status <uuid>'."
            )
        )
    click.echo(FORMAT_RESOLVER[ctx["fmt"]].format_analysis_list(result))


@cli.command()
@click.argument("uuids", default=None, nargs=-1)
@click.pass_obj
def report(ctx, uuids):
    for uuid in uuids:
        resp = ctx["client"].report(uuid)
        inp = ctx["client"].request_by_uuid(uuid)
        ctx["uuid"] = uuid
        click.echo(FORMAT_RESOLVER[ctx["fmt"]].format_detected_issues(resp, inp))


@cli.command()
@click.pass_obj
def version(ctx):
    resp = ctx["client"].version()
    click.echo(FORMAT_RESOLVER[ctx["fmt"]].format_version(resp))


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
