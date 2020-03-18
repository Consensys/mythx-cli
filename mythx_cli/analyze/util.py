import logging
import sys
from glob import glob
from os.path import abspath, commonpath
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import click

from mythx_cli.payload import generate_solidity_payload

RGLOB_BLACKLIST = ["node_modules"]
LOGGER = logging.getLogger("mythx-cli")


def sanitize_paths(job: Dict) -> Dict:
    """Remove the common prefix from paths.

    This method takes a job payload, iterates through all paths, and
    removes all their common prefixes. This is an effort to only submit
    information on a need-to-know basis to MythX. Unless it's to distinguish
    between files, the API does not need to know the absolute path of a file.
    This may even leak user information and should be removed.

    If a common prefix cannot be found (e.g. if there is just one element in
    the source list), the relative path from the current working directory
    will be returned.

    This concerns the following fields:
    - sources
    - AST absolute path
    - legacy AST absolute path
    - source list
    - main source

    :param job: The payload to sanitize
    :return: The sanitized job
    """

    source_list = job.get("source_list")
    if not source_list:
        # triggers on None and empty list
        # if no source list is given, we are analyzing bytecode only
        return job
    source_list = [abspath(s) for s in source_list]
    if len(source_list) > 1:
        # get common path prefix and remove it
        prefix = commonpath(source_list) + "/"
    else:
        # fallback: replace with CWD and get common prefix
        prefix = commonpath(source_list + [str(Path.cwd())]) + "/"

    job["source_list"] = [s.replace(prefix, "") for s in source_list]
    if job.get("main_source") is not None:
        job["main_source"] = job["main_source"].replace(prefix, "")
    for name in list(job.get("sources", {})):
        data = job["sources"].pop(name)
        # sanitize AST data in compiler output
        for ast_key in ("ast", "legacyAST"):
            if not (data.get(ast_key) and data[ast_key].get("absolutePath")):
                continue
            sanitized_absolute = data[ast_key]["absolutePath"].replace(prefix, "")
            data[ast_key]["absolutePath"] = sanitized_absolute

        # replace source key names
        job["sources"][name.replace(prefix, "")] = data

    return job


def is_valid_job(job) -> bool:
    """Detect interface contracts.

    This utility function is used to detect interface contracts in solc and Truffle
    artifacts. This is done by checking whether any bytecode or source maps are to be
    found in the speficied job. This check is performed after the payload has been
    assembled to cover Truffle and Solidity analysis jobs.

    :param job: The payload to perform the check on
    :return: True if the submitted job is for an interface, False otherwise
    """

    filter_values = ("", "0x", None)
    if all(
        (
            job.get("bytecode") in filter_values,
            job.get("source_map") in filter_values,
            job.get("deployed_source_map") in filter_values,
            job.get("deployed_bytecode") in filter_values,
        )
    ):
        click.echo(
            "Skipping submission for contract {} because no bytecode was produced.".format(
                job["contract_name"]
            )
        )
        return True
    return False


def find_truffle_artifacts(project_dir: Union[str, Path]) -> Optional[List[str]]:
    """Look for a Truffle build folder and return all relevant JSON artifacts.

    This function will skip the Migrations.json file and return all other files
    under :code:`<project-dir>/build/contracts/`. If no files were found,
    :code:`None` is returned.

    :param project_dir: The base directory of the Truffle project
    :return: Files under :code:`<project-dir>/build/contracts/` or :code:`None`
    """

    output_pattern = Path(project_dir) / "build" / "contracts" / "*.json"
    artifact_files = list(glob(str(output_pattern.absolute())))
    if not artifact_files:
        return None

    return [f for f in artifact_files if not f.endswith("Migrations.json")]


def find_solidity_files(project_dir: str) -> Optional[List[str]]:
    """Return all Solidity files in the given directory.

    This will match all files with the `.sol` extension.

    :param project_dir: The directory to search in
    :return: Solidity files in `project_dir` or `None`
    """

    output_pattern = Path(project_dir)
    artifact_files = [str(x) for x in output_pattern.rglob("*.sol")]
    if not artifact_files:
        return None

    return [af for af in artifact_files if all((b not in af for b in RGLOB_BLACKLIST))]


def walk_solidity_files(
    ctx,
    solc_version: str,
    base_path: Optional[str] = None,
    remappings: Tuple[str] = None,
) -> List[Dict]:
    """Aggregate all Solidity files in the given base path.

    Given a base path, this function will recursively walk through the filesystem
    and aggregate all Solidity files it comes across. The resulting job list will
    contain all the Solidity payloads (optionally compiled), ready for submission.

    :param ctx: :param ctx: Click context holding group-level parameters
    :param solc_version: The solc version to use for Solidity compilation
    :param base_path: The base path to walk through from
    :param remappings: Import remappings to pass to solcx
    :return:
    """

    jobs = []
    remappings = remappings or []
    walk_path = Path(base_path) if base_path else Path.cwd()
    files = find_solidity_files(walk_path)
    consent = ctx["yes"] or click.confirm(
        "Do you really want to submit {} Solidity files?".format(len(files))
    )
    if not consent:
        sys.exit(0)
    LOGGER.debug("Found Solidity files to submit:\n{}".format("\n".join(files)))
    for file in files:
        jobs.append(generate_solidity_payload(file, solc_version, remappings))
    return jobs
