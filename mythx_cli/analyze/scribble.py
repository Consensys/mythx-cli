import json
import os
import subprocess
import sys
from collections import defaultdict
from typing import List

import click

from mythx_cli.util import sol_files_by_directory

SCRIBBLE_ARMING_META_FILE = ".scribble-arming.meta.json"


class ScribbleMixin:
    """A mixing for job objects to instrument code with Scribble."""

    @staticmethod
    def _handle_scribble_error(process: subprocess.CompletedProcess) -> None:
        """Handle scribble subprocess errors.

        This method will throw a CLI error in the case of scribble exiting
        with a non-zero exit code.

        :param process: The finished scribble process object
        """
        if process.returncode == 0:
            return

        click.echo(f"Scribble has encountered an error (code: {process.returncode})")
        click.echo("=====STDERR=====")
        click.echo(process.stderr.decode())
        click.echo("=====STDOUT=====")
        click.echo(process.stdout.decode())

        sys.exit(process.returncode)

    def instrument_truffle_artifacts(
        self, payloads: List[dict], scribble_path: str, remappings: List[str]
    ) -> dict:
        """Instrument a list of truffle artifacts with scribble.

        :param payloads: The list of truffle artifact objects
        :param scribble_path: The path to the scribble executable
        :param remappings: Optional solc import remappings
        :return: The deserialized scribble JSON output object
        """
        stdin = {"sources": {}, "contracts": defaultdict(defaultdict)}

        for payload in payloads:
            # reconstruct solc artifact from payload to pass it into scribble
            for filename, file_data in payload["sources"].items():
                stdin["sources"][filename] = {
                    "ast": file_data["ast"],
                    "source": file_data["source"],
                    "id": payload["source_list"].index(filename),
                }

                stdin["contracts"][filename][payload["contract_name"]] = {
                    "evm": {
                        "bytecode": {
                            "object": payload["bytecode"],
                            "sourceMap": payload["source_map"],
                        },
                        "deployedBytecode": {
                            "object": payload["deployed_bytecode"],
                            "sourceMap": payload["deployed_source_map"],
                        },
                    }
                }

        process = subprocess.run(
            [scribble_path, "--input-mode", "json", "--output-mode", "json"]
            + ([f"--path-remapping" "{';'.join(remappings)}"] if remappings else [])
            + ["--"],
            input=json.dumps(stdin).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._handle_scribble_error(process)

        return json.loads(process.stdout.decode())

    def instrument_solc_file(
        self, target: str, scribble_path: str, remappings: List[str]
    ) -> dict:
        """Instrument a single Solidity file with scribble.

        :param target: The target filename to pass to scribble
        :param scribble_path: The path to the scribble executable
        :param remappings: Optional solc import remappings
        :return: The deserialized scribble JSON output object
        """
        process = subprocess.run(
            [scribble_path, "--input-mode=source", "--output-mode=json"]
            + ([f"--path-remapping={';'.join(remappings)}"] if remappings else [])
            + [target],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._handle_scribble_error(process)

        return json.loads(process.stdout.decode())

    @staticmethod
    def instrument_solc_in_place(
        file_list: List[str],
        scribble_path: str,
        remappings: List[str] = None,
        solc_version: str = None,
    ) -> None:
        """Instrument a collection of Solidity files in place.

        :param file_list: List of paths to Solidity files to instrument
        :param scribble_path: The path to the scribble executable
        :param remappings: List of import remappings to pass to solc
        :param solc_version: The solc compiler version to use
        """
        command = [
            scribble_path,
            "--arm",
            "--output-mode=files",
            f"--instrumentation-metadata-file={SCRIBBLE_ARMING_META_FILE}",
        ]

        if remappings:
            command.append(f"--path-remapping={';'.join(remappings)}")

        if solc_version:
            command.append(f"--compiler-version={solc_version}")

        # Scribble doesnt currently support directories as inputs
        # so we create a list of all solidity files inside each of the targets
        # and submit that to Scribble.

        sol_files = []
        for file in file_list:
            target_files = sol_files_by_directory(file)
            sol_files = [*sol_files, *target_files]

        command.extend(sol_files)

        process = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        ScribbleMixin._handle_scribble_error(process)

    @staticmethod
    def disarm_solc_in_place(
        file_list: List[str],
        scribble_path: str,
        remappings: List[str] = None,
        solc_version: str = None,
    ) -> None:
        """Un-instrument a collection of Solidity files in place.

        :param file_list: List of paths to Solidity files to instrument
        :param scribble_path: The path to the scribble executable
        :param remappings: List of import remappings to pass to solc
        :param solc_version: The solc compiler version to use
        """
        command = [scribble_path, "--disarm"]

        if remappings:
            command.append(f"--path-remapping={';'.join(remappings)}")

        if solc_version:
            command.append(f"--compiler-version={solc_version}")

        # Scribble doesnt currently support directories as inputs
        # so we create a list of all solidity files inside each of the targets
        # and submit that to Scribble.

        sol_files = []
        for file in file_list:
            target_files = sol_files_by_directory(file)
            sol_files = [*sol_files, *target_files]

        command.extend(sol_files)

        if os.path.isfile(SCRIBBLE_ARMING_META_FILE):
            os.remove(SCRIBBLE_ARMING_META_FILE)

        process = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        ScribbleMixin._handle_scribble_error(process)

    @staticmethod
    def get_arming_instr_meta():
        if os.path.exists(SCRIBBLE_ARMING_META_FILE):
            with open(SCRIBBLE_ARMING_META_FILE, "r") as f:
                return json.load(f)

        return None
