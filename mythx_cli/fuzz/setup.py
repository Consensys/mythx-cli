import logging

import click

LOGGER = logging.getLogger("mythx-cli")


@click.command("setup")
def fuzz_setup():
    click.echo("Hello, setup!")
