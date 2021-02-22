import logging

import click

LOGGER = logging.getLogger("mythx-cli")


@click.command("run")
def fuzz_run():
    click.echo("Hello, run!")
