import json
from os.path import abspath
from pathlib import Path
from subprocess import Popen, TimeoutExpired
from tempfile import TemporaryFile
from typing import Any, Dict, List

from mythx_cli.fuzz.exceptions import BuildArtifactsError
from mythx_cli.fuzz.ide.generic import IDEArtifacts, JobBuilder
from mythx_cli.util import LOGGER, sol_files_by_directory


class TruffleArtifacts(IDEArtifacts):
    def __init__(self, project_dir: str, build_dir=None, targets=None):
        self._include: List[str] = []
        if targets:
            include = []
            for target in targets:
                # targets could be specified using relative path. But sourcePath in truffle artifacts
                # will use absolute paths, so we need to use absolute paths in targets as well
                include.extend(
                    [abspath(file_path) for file_path in sol_files_by_directory(target)]
                )
            self._include = include

        self._build_dir = build_dir or Path("./build/contracts")
        build_files_by_source_file = self._get_build_artifacts(self._build_dir)
        project_sources = self._get_project_sources(project_dir)

        self._contracts, self._sources = self.fetch_data(
            build_files_by_source_file, project_sources
        )

    def fetch_data(
        self, build_files_by_source_file, project_sources: Dict[str, List[str]]
    ):
        result_contracts = {}
        result_sources = {}
        for source_file, contracts in build_files_by_source_file.items():
            if source_file not in self._include:
                continue
            result_contracts[source_file] = []
            for contract in contracts:
                # We get the build items from truffle and rename them into the properties used by the FaaS
                try:
                    result_contracts[source_file] += [
                        {
                            "sourcePaths": {
                                i: k
                                for i, k in enumerate(
                                    project_sources[contract["contractName"]]
                                )
                            },
                            "deployedSourceMap": contract["deployedSourceMap"],
                            "deployedBytecode": contract["deployedBytecode"],
                            "sourceMap": contract["sourceMap"],
                            "bytecode": contract["bytecode"],
                            "contractName": contract["contractName"],
                            "mainSourceFile": contract["sourcePath"],
                        }
                    ]
                except KeyError as e:
                    raise BuildArtifactsError(
                        f"Build artifact did not contain expected key. Contract: {contract}: \n{e}"
                    )

                for file_index, source_file_dep in enumerate(
                    project_sources[contract["contractName"]]
                ):
                    if source_file_dep in result_sources.keys():
                        continue

                    if source_file_dep not in build_files_by_source_file:
                        LOGGER.debug(f"{source_file} not found.")
                        continue

                    # We can select any dict on the build_files_by_source_file[source_file] array
                    # because the .source and .ast values will be the same in all.
                    target_file = build_files_by_source_file[source_file_dep][0]
                    result_sources[source_file_dep] = {
                        "fileIndex": file_index,
                        "source": target_file["source"],
                        "ast": target_file["ast"],
                    }
        return result_contracts, result_sources

    @staticmethod
    def query_truffle_db(query: str, project_dir: str) -> Dict[str, Any]:
        try:
            # here we're using the tempfile to overcome the subprocess.PIPE's buffer size limit (65536 bytes).
            # This limit becomes a problem on a large sized output which will be truncated, resulting to an invalid json
            with TemporaryFile() as stdout_file, TemporaryFile() as stderr_file:
                with Popen(
                    ["truffle", "db", "query", f"{query}"],
                    stdout=stdout_file,
                    stderr=stderr_file,
                    cwd=project_dir,
                ) as p:
                    p.communicate(timeout=3 * 60)
                    if stdout_file.tell() == 0:
                        error = ""
                        if stderr_file.tell() > 0:
                            stderr_file.seek(0)
                            error = f"\nError: {str(stderr_file.read())}"
                        raise BuildArtifactsError(
                            f'Empty response from the Truffle DB.\nQuery: "{query}"{error}'
                        )
                    stdout_file.seek(0)
                    result = json.load(stdout_file)
        except BuildArtifactsError as e:
            raise e
        except TimeoutExpired:
            raise BuildArtifactsError(f'Truffle DB query timeout.\nQuery: "{query}"')
        except Exception as e:
            raise BuildArtifactsError(
                f'Truffle DB query error.\nQuery: "{query}"'
            ) from e
        if not result.get("data"):
            raise BuildArtifactsError(
                f'"data" field is not found in the query result.\n Result: "{json.dumps(result)}".\nQuery: "{query}"'
            )
        return result.get("data")

    @staticmethod
    def _get_project_sources(project_dir: str) -> Dict[str, List[str]]:
        result = TruffleArtifacts.query_truffle_db(
            f'query {{ projectId(input: {{ directory: "{project_dir}" }}) }}',
            project_dir,
        )
        project_id = result.get("projectId")

        if not project_id:
            raise BuildArtifactsError(
                f'No project artifacts found. Path: "{project_dir}"'
            )

        result = TruffleArtifacts.query_truffle_db(
            f"""
            {{
              project(id:"{project_id}") {{
                contracts {{
                  name
                  compilation {{
                    processedSources {{
                      source {{
                        sourcePath
                      }}
                    }}
                  }}
                }}
              }}
            }}
            """,
            project_dir,
        )

        contracts = {}

        if not result.get("project") or not result["project"]["contracts"]:
            raise BuildArtifactsError(
                f'No project artifacts found. Path: "{project_dir}". Project ID "{project_id}"'
            )

        for contract in result["project"]["contracts"]:
            contracts[contract["name"]] = list(
                map(
                    lambda x: x["source"]["sourcePath"],
                    contract["compilation"]["processedSources"],
                )
            )
        return contracts

    @property
    def contracts(self):
        return self._contracts

    @property
    def sources(self):
        return self._sources


class TruffleJob:
    def __init__(self, project_dir: str, target: List[str], build_dir: Path):
        artifacts = TruffleArtifacts(project_dir, build_dir, targets=target)
        self._jb = JobBuilder(artifacts)
        self.payload = None

    def generate_payload(self):
        self.payload = self._jb.payload()
