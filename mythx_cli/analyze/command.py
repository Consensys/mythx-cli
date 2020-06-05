import logging
import sys
import time
from enum import Enum
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from mythx_models.response import (
    AnalysisInputResponse,
    DetectedIssuesResponse,
    GroupCreationResponse,
)
from pythx.middleware.group_data import GroupDataMiddleware
from pythx.middleware.property_checking import PropertyCheckingMiddleware

from mythx_cli.analyze.bytecode import generate_bytecode_payload
from mythx_cli.analyze.solidity import generate_solidity_payload, walk_solidity_files
from mythx_cli.analyze.truffle import find_truffle_artifacts, generate_truffle_payload
from mythx_cli.analyze.util import is_valid_job, sanitize_paths
from mythx_cli.formatter import FORMAT_RESOLVER, util
from mythx_cli.formatter.base import BaseFormatter
from mythx_cli.util import write_or_print

LOGGER = logging.getLogger("mythx-cli")


class AnalyzeMode(Enum):
    SOLIDITY_FILE = 1
    SOLIDITY_DIR = 2
    TRUFFLE = 3


@click.command()
@click.argument("target", default=None, nargs=-1, required=False)
@click.option(
    "--async/--wait",  # TODO: make default on full
    "async_flag",
    default=None,
    help="Submit the job and print the UUID, or wait for execution to finish",
)
@click.option("--mode", type=click.Choice(["quick", "standard", "deep"]), default=None)
@click.option(
    "--create-group",
    is_flag=True,
    default=None,
    help="Create a new group for the analysis",
)
@click.option(
    "--group-id",
    type=click.STRING,
    help="The group ID to add the analysis to",
    default=None,
)
@click.option(
    "--group-name",
    type=click.STRING,
    help="The group name to attach to the analysis",
    default=None,
)
@click.option(
    "--min-severity",
    type=click.STRING,
    help="Ignore SWC IDs below the designated level",
    default=None,
)
@click.option(
    "--swc-blacklist",
    type=click.STRING,
    help="A comma-separated list of SWC IDs to ignore",
    default=None,
)
@click.option(
    "--swc-whitelist",
    type=click.STRING,
    help="A comma-separated list of SWC IDs to include",
    default=None,
)
@click.option(
    "--solc-version",
    type=click.STRING,
    help="The solc version to use for compilation",
    default=None,
)
@click.option(
    "--include",
    type=click.STRING,
    multiple=True,
    help="The contract name(s) to submit to MythX",
    default=None,
)
@click.option(
    "--remap-import",
    type=click.STRING,
    multiple=True,
    help="Add a solc compilation import remapping",
    default=None,
)
@click.option(
    "--check-properties",
    is_flag=True,
    default=None,
    help="Enable property verification mode",
)
@click.option(
    "--scribble",
    "enable_scribble",
    is_flag=True,
    default=None,
    help="Enable scribble instrumentation",
)
@click.option(
    "--scribble-path",
    type=click.Path(exists=True),
    default=None,
    help="Path to a custom scribble executable",
)
@click.pass_obj
def analyze(
    ctx,
    target: List[str],
    async_flag: bool,
    mode: str,
    create_group: bool,
    group_id: str,
    group_name: str,
    min_severity: str,
    swc_blacklist: str,
    swc_whitelist: str,
    solc_version: str,
    include: Tuple[str],
    remap_import: Tuple[str],
    check_properties: bool,
    enable_scribble: bool,
    scribble_path: str,
) -> None:
    """Analyze the given directory or arguments with MythX.

    \f

    :param ctx: Click context holding group-level parameters
    :param target: Arguments passed to the `analyze` subcommand
    :param async_flag: Whether to execute the analysis asynchronously
    :param mode: Full or quick analysis mode
    :param create_group: Create a new group for the analysis
    :param group_id: The group ID to add the analysis to
    :param group_name: The group name to attach to the analysis
    :param min_severity: Ignore SWC IDs below the designated level
    :param swc_blacklist: A comma-separated list of SWC IDs to ignore
    :param swc_whitelist: A comma-separated list of SWC IDs to include
    :param solc_version: The solc version to use for Solidity compilation
    :param include: List of contract names to send - exclude everything else
    :param remap_import: List of import remappings to pass on to solc
    :param check_properties: Enable property verification mode
    :param enable_scribble: Enable instrumentation with scribble
    :param scribble_path: Optional path to the scribble executable
    :return:
    """

    analyze_config = ctx.get("analyze")
    if async_flag is None:
        async_flag = analyze_config.get("async", False)
    if create_group is None:
        create_group = analyze_config.get("create-group", False)

    mode = mode or analyze_config.get("mode") or "quick"
    group_id = analyze_config.get("group-id") or group_id
    group_name = group_name or analyze_config.get("group-name") or ""
    min_severity = min_severity or analyze_config.get("min-severity") or None
    swc_blacklist = swc_blacklist or analyze_config.get("blacklist") or None
    swc_whitelist = swc_whitelist or analyze_config.get("whitelist") or None
    solc_version = solc_version or analyze_config.get("solc") or None
    include = include or analyze_config.get("contracts") or []
    remap_import = remap_import or analyze_config.get("remappings") or []
    check_properties = (
        check_properties or analyze_config.get("check-properties") or False
    )
    enable_scribble = enable_scribble or analyze_config.get("enable-scribble") or False
    scribble_path = scribble_path or analyze_config.get("scribble-path") or "scribble"
    target = target or analyze_config.get("targets") or None

    # enable property checking if explicitly requested or implicitly when
    # scribble instrumentation is requested
    ctx["client"].handler.middlewares.append(
        PropertyCheckingMiddleware(check_properties or enable_scribble)
    )

    if create_group:
        resp: GroupCreationResponse = ctx["client"].create_group(group_name=group_name)
        group_id = resp.group.identifier
        group_name = resp.group.name or ""

    if group_id:
        # associate all following analyses to the passed or newly created group
        group_mw = GroupDataMiddleware(group_id=group_id, group_name=group_name)
        ctx["client"].handler.middlewares.append(group_mw)

    jobs: List[Dict[str, Any]] = []
    include = list(include)
    mode_list = []

    if not target:
        if Path("truffle-config.js").exists() or Path("truffle.js").exists():
            LOGGER.debug(f"Identified directory as truffle project")
            mode_list.append((AnalyzeMode.TRUFFLE, Path.cwd()))  # TRUFFLE DIR
        elif list(glob("*.sol")):
            LOGGER.debug(f"Identified directory with Solidity files")
            mode_list.append((AnalyzeMode.SOLIDITY_DIR, Path.cwd()))  # SOLIDITY DIR
        else:
            raise click.exceptions.UsageError(
                "No argument given and unable to detect Truffle project or Solidity files"
            )
    else:
        for target_elem in target:
            element = target_elem.split(":")[0]
            if Path(element).is_file() and Path(element).suffix == ".sol":
                LOGGER.debug(f"Identified target {element} as solidity file")
                mode_list.append(
                    (AnalyzeMode.SOLIDITY_FILE, target_elem)
                )
            elif Path(target_elem).is_dir():
                LOGGER.debug(f"Identified target {target_elem} as directory")
                files, source_list = find_truffle_artifacts(Path(target_elem))
                if files:
                    LOGGER.debug(
                        f"Identified {target_elem} directory as truffle project"
                    )
                    mode_list.append((AnalyzeMode.TRUFFLE, Path(target_elem)))
                else:
                    LOGGER.debug(f"Identified {target_elem} as Solidity directory")
                    mode_list.append(
                        (AnalyzeMode.SOLIDITY_DIR, Path(target_elem))
                    )
            else:
                raise click.exceptions.UsageError(
                    f"Could not interpret argument {target_elem} as bytecode, Solidity file, or Truffle project"
                )

    for analyze_mode, element in mode_list:
        if analyze_mode == AnalyzeMode.TRUFFLE:
            files, source_list = find_truffle_artifacts(element)
            if not files:
                raise click.exceptions.UsageError(
                    "Could not find any truffle artifacts. Did you run truffle compile?"
                )
            LOGGER.debug(f"Detected Truffle project with files:{', '.join(files)}")
            for file in files:
                jobs.append(generate_truffle_payload(file, source_list))
        elif analyze_mode == AnalyzeMode.SOLIDITY_DIR:
            # recursively enumerate sol files if not a truffle project
            LOGGER.debug(f"Identified {element} as directory containing Solidity files")
            jobs.extend(
                walk_solidity_files(
                    ctx,
                    solc_version,
                    base_path=element,
                    remappings=remap_import,
                    enable_scribble=enable_scribble,
                    scribble_path=scribble_path,
                )
            )
        elif analyze_mode == AnalyzeMode.SOLIDITY_FILE:
            # TODO: There has to be a prettier way for this
            LOGGER.debug(f"Trying to interpret {element} as a solidity file")
            target_split = element.split(":")
            file_path, contract = target_split[0], target_split[1:]
            if contract:
                include += contract  # e.g. ["MyContract"]
                contract = contract[0]
            jobs.append(
                generate_solidity_payload(
                    file=file_path,
                    version=solc_version,
                    contract=contract,
                    remappings=remap_import,
                    enable_scribble=enable_scribble,
                    scribble_path=scribble_path,
                )
            )

    # sanitize local paths
    LOGGER.debug(f"Sanitizing {len(jobs)} jobs")
    jobs = [sanitize_paths(job) for job in jobs]
    # filter jobs where no bytecode was produced
    LOGGER.debug(f"Filtering {len(jobs)} jobs for empty bytecode")
    jobs = [job for job in jobs if is_valid_job(job)]

    # reduce to whitelisted contract names
    if include:
        LOGGER.debug(f"Filtering {len(jobs)} for contracts to be included")
        found_contracts = {job["contract_name"] for job in jobs}
        overlap = set(include).difference(found_contracts)
        if overlap:
            raise click.UsageError(
                f"The following contracts could not be found: {', '.join(overlap)}"
            )
        jobs = [job for job in jobs if job["contract_name"] in include]

    LOGGER.debug(f"Submitting {len(jobs)} analysis jobs to the MythX API")
    uuids = []
    with click.progressbar(jobs) as bar:
        for job in bar:
            # attach execution mode, submit, poll
            job.update({"analysis_mode": mode})
            resp = ctx["client"].analyze(**job)
            uuids.append(resp.uuid)

    if async_flag:
        LOGGER.debug(
            f"Asynchronous submission enabled - printing {len(uuids)} UUIDs and exiting"
        )
        write_or_print("\n".join(uuids))
        return

    issues_list: List[
        Tuple[DetectedIssuesResponse, Optional[AnalysisInputResponse]]
    ] = []
    formatter: BaseFormatter = FORMAT_RESOLVER[ctx["fmt"]]
    for uuid in uuids:
        while not ctx["client"].analysis_ready(uuid):
            # TODO: Add poll interval option
            LOGGER.debug(f"Analysis {uuid} not ready yet - waiting")
            time.sleep(3)
        LOGGER.debug(f"{uuid}: Fetching report")
        resp: DetectedIssuesResponse = ctx["client"].report(uuid)
        LOGGER.debug(f"{uuid}: Fetching input")
        inp: Optional[AnalysisInputResponse] = ctx["client"].request_by_uuid(
            uuid
        ) if formatter.report_requires_input else None

        LOGGER.debug(f"{uuid}: Applying SWC filters")
        util.filter_report(
            resp,
            min_severity=min_severity,
            swc_blacklist=swc_blacklist,
            swc_whitelist=swc_whitelist,
        )
        # extend response with job UUID to keep formatter logic isolated
        resp.uuid = uuid
        issues_list.append((resp, inp))

    LOGGER.debug(f"Printing report for {len(issues_list)} issue items")
    write_or_print(formatter.format_detected_issues(issues_list))
    sys.exit(ctx["retval"])
