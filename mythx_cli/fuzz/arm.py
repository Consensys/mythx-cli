import logging

import click

LOGGER = logging.getLogger("mythx-cli")


@click.command("arm")
def fuzz_arm():
    click.echo("Hello, arm!")
