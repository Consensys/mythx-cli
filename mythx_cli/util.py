import logging

import click

LOGGER = logging.getLogger("mythx-cli")


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
