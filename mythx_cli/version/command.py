import logging

import click

from mythx_cli.formatter import FORMAT_RESOLVER
from mythx_cli.util import write_or_print

LOGGER = logging.getLogger("mythx-cli")


@click.command()
@click.pass_obj
def version(ctx) -> None:
    """Display API version information.

    \f

    :param ctx: Click context holding group-level parameters
    :return:
    """

    LOGGER.debug("Fetching version information")
    resp = ctx["client"].version()
    write_or_print(FORMAT_RESOLVER[ctx["fmt"]].format_version(resp))
