import logging
from collections import defaultdict
from typing import Any, List, Optional, Tuple

import click
from mythx_models.response import AnalysisInputResponse, DetectedIssuesResponse

from mythx_cli.formatter.util import get_source_location_by_offset

LOGGER = logging.getLogger("mythx-cli")


def index_by_filename(
    issues_list: List[Tuple[DetectedIssuesResponse, Optional[AnalysisInputResponse]]]
):
    """Index the given report/input responses by filename.

    This will return a simplified, unified representation of the report/input payloads
    returned by the MythX API. It is a mapping from filename to an iterable of issue
    objects, which contain the report UUID, SWC ID, SWC title, short and long
    description, severity, as well as the issue's line location in the source code.

    This representation is meant to be passed on to the respective formatter, which
    them visualizes the data.

    :param issues_list: A list of two-tuples containing report and input responses
    :return: A simplified mapping indexing issues by their file path
    """

    report_context = defaultdict(list)
    for resp, inp in issues_list:
        # initialize context with source line objects
        for filename, file_data in inp.sources.items():
            source = file_data.get("source")
            if source is None:
                # skip files where no source is given
                continue
            report_context[filename].extend(
                [
                    {"line": line + 1, "content": content, "issues": []}
                    for line, content in enumerate(source.split("\n"))
                ]
            )

        for report in resp.issue_reports:
            for issue in report.issues:
                issue_entry = {
                    "uuid": resp.uuid,
                    "swcID": issue.swc_id,
                    "swcTitle": issue.swc_title,
                    "description": {
                        "head": issue.description_short,
                        "tail": issue.description_long,
                    },
                    "severity": issue.severity,
                    "testCases": issue.extra_data.get("testCases", []),
                }

                if issue.swc_id == "" or issue.swc_title == "" or not issue.locations:
                    # skip issues with missing SWC or location data
                    continue

                source_formats = [loc.source_format for loc in issue.locations]
                for loc in issue.locations:
                    if loc.source_format != "text" and "text" in source_formats:
                        # skip non-text locations when we have one attached to the issue
                        continue

                    for c in loc.source_map.components:
                        source_list = loc.source_list or report.source_list
                        if not (source_list and 0 <= c.file_id < len(source_list)):
                            # skip issues whose srcmap file ID if out of range of the source list
                            continue
                        filename = source_list[c.file_id]

                        if not inp.sources or filename not in inp.sources:
                            # skip issues that can't be decoded to source location
                            continue

                        line = get_source_location_by_offset(
                            inp.sources[filename]["source"], c.offset
                        )
                        report_context[filename][line - 1]["issues"].append(issue_entry)
                        break

    return report_context


def update_context(
    context: dict, context_key: str, config: dict, config_key: str, default: Any = None
):
    """Update the click context based on a configuration dict.

    If the specified key is set in the configuration dict, it will
    be added/overwrite the respective other key in the click context.

    :param context: The click context dict to set/overwrite
    :param context_key: The key in the click context to overwrite
    :param config: The config to read additional data from
    :param config_key: The config key to overwrite with
    :param default: The default value to use if all lookups fail
    """

    context[context_key] = context.get(context_key) or config.get(config_key) or default


@click.pass_obj
def write_or_print(ctx, data: str, mode="a+") -> None:
    """Depending on the context, write the given content to stdout or a given
    file.

    :param ctx: Click context holding group-level parameters
    :param data: The data to print or write to a file
    :param mode: The mode to open the file in (if file output enabled)
    :return:
    """

    if not ctx["output"]:
        LOGGER.debug("Writing data to stdout")
        click.echo(data)
        return
    with open(ctx["output"], mode) as outfile:
        LOGGER.debug(f"Writing data to {ctx['output']}")
        outfile.write(data + "\n")
