import logging
from subprocess import check_output

import click

LOGGER = logging.getLogger("mythx-cli")


@click.command()
@click.pass_obj
def check(ctx) -> None:
    """Use Scribble instrumentation.

    \f

    :param ctx: Click context holding group-level parameters
    :return:
    """

    print(check_output(["echo", "Hello Scribble!"]).decode())
