"""This module contains functions to generate payloads for Truffle projects."""

import json
import logging
import re
import sys
from collections import defaultdict
from glob import glob
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

import click

from .scribble import ScribbleMixin

LOGGER = logging.getLogger("mythx-cli")


class TruffleJob(ScribbleMixin):
    """A truffle job to be sent to the API.

    This object represents a collection of truffle artifacts that will
    be sent to the API. It aggregates artifacts and transforms them into
    API-conform payload dicts.
    """

    def __init__(self, target: Path):
        super().__init__()
        self.target = target
        self.payloads = []
        self.sol_artifact_map = {}
        self.artifact_files, self.source_list = self.find_truffle_artifacts()

        if not self.artifact_files:
            raise click.exceptions.UsageError(
                "Could not find any truffle artifacts. Did you run truffle compile?"
            )
        LOGGER.debug(
            f"Detected Truffle project with files:{', '.join(self.artifact_files)}"
        )

        self.dependency_map = self.build_dependency_map()

    def find_truffle_artifacts(
        self
    ) -> Union[Tuple[List[str], List[str]], Tuple[None, None]]:
        """Look for a Truffle build folder and return all relevant JSON
        artifacts.

        This function will skip the Migrations.json file and return all other files
        under :code:`<project-dir>/build/contracts/`. If no files were found,
        :code:`None` is returned.

        :return: Files under :code:`<project-dir>/build/contracts/` or :code:`None`
        """
        output_pattern = self.target / "build" / "contracts" / "*.json"
        artifact_files = list(glob(str(output_pattern.absolute())))
        if not artifact_files:
            LOGGER.debug(f"No truffle artifacts found in pattern {output_pattern}")
            return None, None

        sources: Set[Tuple[int, str]] = set()
        for file in artifact_files:
            with open(file) as af:
                artifact = json.load(af)
                try:
                    ast = artifact.get("ast") or artifact.get("legacyAST")
                    idx = ast.get("src", "").split(":")[2]
                    sources.add((int(idx), artifact.get("sourcePath")))
                except (KeyError, IndexError, AttributeError) as e:
                    LOGGER.warning(f"Could not reconstruct artifact source list: {e}")
                    click.echo(
                        (
                            "Unable to construct a valid payload from the Truffle build artifacts. "
                            "Do your payloads contain an 'ast' or 'legacyAST' field? "
                            "Alternatively, consider explicitly compiling your project using solc: "
                            "https://mythx-cli.readthedocs.io/en/latest/usage.html#submitting-analyses"
                        )
                    )
                    sys.exit(1)

        # infer source list from artifact collection
        source_list = [x[1] for x in sorted(list(sources), key=lambda x: x[0])]
        return artifact_files, source_list

    def generate_payloads(
        self,
        remappings: Tuple[str] = None,
        enable_scribble: bool = False,
        scribble_path: str = "scribble",
    ):
        """Generate a MythX analysis request payload based on a truffle build
        artifact.

        This will send the following artifact entries to MythX for analysis:

        * :code:`contractName`
        * :code:`bytecode`
        * :code:`deployedBytecode`
        * :code:`sourceMap`
        * :code:`deployedSourceMap`
        * :code:`sourcePath`
        * :code:`source`
        * :code:`ast`
        * :code:`legacyAST`
        * the compiler version

        :param remappings: Optional solc import remappings
        :param enable_scribble: Whether to instrument the payloads with scribble
        :param scribble_path: The path to the scribble executable
        :return: The payload dictionary to be sent to MythX
        """
        for file in self.artifact_files:
            with open(file) as af:
                artifact = json.load(af)
                LOGGER.debug(f"Loaded Truffle artifact with {len(artifact)} keys")

            self.payloads.append(
                {
                    "contract_name": artifact.get("contractName"),
                    "bytecode": self.patch_truffle_bytecode(artifact.get("bytecode"))
                    if artifact.get("bytecode") != "0x"
                    else None,
                    "deployed_bytecode": self.patch_truffle_bytecode(
                        artifact.get("deployedBytecode")
                    )
                    if artifact.get("deployedBytecode") != "0x"
                    else None,
                    "source_map": artifact.get("sourceMap")
                    if artifact.get("sourceMap")
                    else None,
                    "deployed_source_map": artifact.get("deployedSourceMap")
                    if artifact.get("deployedSourceMap")
                    else None,
                    "sources": {
                        artifact.get("sourcePath"): {
                            "source": artifact.get("source"),
                            "ast": artifact.get("ast"),
                        },
                        **self.get_artifact_context(file),
                    },
                    "source_list": self.source_list,
                    "main_source": artifact.get("sourcePath"),
                    "solc_version": artifact["compiler"]["version"],
                }
            )

        if enable_scribble:
            return self.instrument_truffle_artifacts(
                payloads=self.payloads,
                scribble_path=scribble_path,
                remappings=remappings,
            )
        else:
            return self.payloads

    @staticmethod
    def patch_truffle_bytecode(code: str) -> str:
        """Patch Truffle bytecode placeholders.

        This function patches placeholders in Truffle artifact files. These placeholders are meant
        to be replaced with deployed library/dependency addresses on deployment, but do not form
        valid EVM bytecode. To produce a valid payload, placeholders are replaced with the zero-address.

        :param code: The bytecode to patch
        :return: The patched bytecode with the zero-address filled in
        """
        return re.sub(re.compile(r"__\w{38}"), "0" * 40, code)

    def artifact_to_sol_file(self, artifact_path: str) -> str:
        """Resolve an artifact file to its corresponding Solidity file.

        This method will take the Truffle artifact's file name, and
        recursively search through the current directory and all
        subdirectories, looking for a Solidity file with the same name.

        For additional lookup performance in large Truffle projects with
        a large dependency graph, the mapping from Solidity file to
        artifact and vice versa is stored in the job object for future
        resolution to aboid filesystem interaction.

        NOTE: We do not loop up the entries in the mapping here, because
        we want to avoid accidentally resolving external dependencies
        defined by path remappings, e.g. @openzeppelin/SafeMath.sol as
        these don't turn up as absolute paths in Truffle artifacts but
        stay in the remapped format.

        :param artifact_path: The path to the Truffle artifact
        :return: The corresponding Solidity file path
        """
        basename = Path(artifact_path).name.replace(".json", ".sol")
        sol_file = str(next(Path().rglob(basename)).absolute())
        self.sol_artifact_map[sol_file] = artifact_path
        self.sol_artifact_map[artifact_path] = sol_file
        return sol_file

    def sol_file_to_artifact(
        self, sol_path: str, artifact_files: Tuple[List[str], List[str]]
    ) -> Optional[List[str]]:
        """Resolve a Solidity file to the corresponding artifact file.

        This method will take the path to a Solidity file and return
        its corresponding Truffle artifact JSON file.
        If this relation is already stored in the local artifact mapping,
        the result will be returned right away. Otherwise, the Solidity
        path's file name is retrieved, and looked up in the list of
        artifact files and add the relation to the job object's mapping.

        :param sol_path: The path of the Solidity file to retrieve the artifact for
        :param artifact_files: The list of artifact files in the Truffle build directory
        :return: The resolved Truffle artifact JSON path
        """
        if sol_path in self.sol_artifact_map:
            return self.sol_artifact_map[sol_path]
        basename = Path(sol_path).name.replace(".sol", ".json")
        artifact_path = next((x for x in artifact_files if basename in x), None)
        self.sol_artifact_map[sol_path] = artifact_path
        return artifact_path

    def build_dependency_map(self) -> Dict[Any, Iterable]:
        """Build the local dependency mapping.

        To speed up lookups when attaching related artifacts to analysis
        payloads, this method builds a dependency map where the current
        file is the key, and the value is a set containing all related
        artifact paths the key file path depends on.

        This method is called in the constructor to build the mapping right
        away and speed up all future lookups.
        """
        dependency_map = defaultdict(set)
        for artifact_file in self.artifact_files:
            with open(artifact_file) as af:
                artifact = json.load(af)

            for node in artifact.get("ast")["nodes"]:
                if node["nodeType"] != "ImportDirective":
                    continue
                related_artifact = self.sol_file_to_artifact(
                    sol_path=node["absolutePath"], artifact_files=self.artifact_files
                )
                if related_artifact is not None:
                    dependency_map[artifact_file].add(related_artifact)
        return dependency_map

    def get_artifact_context(self, artifact_file: str) -> Dict[str, Any]:
        """Get additional context for a given artifact file.

        This method will look up the artifacts related to the current one
        in the instace's dependency map, load their JSON, and attach source
        code and AST information to the context object.

        To do that, the related Solidity file path is resolved.

        :param artifact_file: The artifact file to generate context for
        :return: A dictionary containing source and AST information of all related files
        """
        context = {}
        for related_file in self.dependency_map[artifact_file]:
            with open(related_file) as af:
                artifact = json.load(af)
            context[self.artifact_to_sol_file(artifact_path=related_file)] = {
                "source": artifact.get("source"),
                "ast": artifact.get("ast"),
            }
        return context
