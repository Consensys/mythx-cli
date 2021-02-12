# https://api.mythx.io/v1/openapi#operation/listProjects

import logging

import click
from mythx_models.response import ProjectListResponse
from pythx import Client

from mythx_cli.formatter import FORMAT_RESOLVER
from mythx_cli.util import write_or_print

LOGGER = logging.getLogger("mythx-cli")


@click.command("list")
@click.option(
    "--number",
    default=5,
    type=click.IntRange(min=1, max=100),  # ~ 5 requests à 20 entries
    show_default=True,
    help="The number of most recent projects to display",
)
@click.pass_obj
def project_list(ctx, number: int) -> None:
    """Get a list of analysis projects.

    \f

    :param ctx: Click context holding group-level parameters
    :param number: The number of analysis projects to display
    :return:
    """

    client: Client = ctx["client"]
    result = ProjectListResponse(projects=[], total=0)
    offset = 0
    while True:
        LOGGER.debug(f"Fetching projects with offset {offset}")
        resp = client.project_list(offset=offset)
        if not resp.projects:
            LOGGER.debug("Received empty project list response")
            break
        offset += len(resp.projects)
        result.projects.extend(resp.projects)
        if len(result.projects) >= number:
            LOGGER.debug(f"Received {len(result.projects)} projects")
            break

    # trim result to desired result number
    LOGGER.debug(f"Got {len(result.projects)} analyses, trimming to {number}")
    result = ProjectListResponse(projects=result.projects[:number], total=resp.total)
    write_or_print(FORMAT_RESOLVER[ctx["fmt"]].format_project_list(result))
