import logging
import subprocess

import click

LOGGER = logging.getLogger("mythx-cli")


# TODO: Help texts and docs
@click.command()
@click.argument("target", type=click.Path(exists=True))
@click.option("--scribble-path", type=click.Path(exists=True), default="scribble")
@click.pass_obj
def check(ctx, target, scribble_path) -> None:
    """Use Scribble instrumentation.

    \f

    :param ctx: Click context holding group-level parameters
    :param target: The target file to instrument
    :param scribble_path: Custom path to the scribble executable
    :return:
    """

    process = subprocess.run(
        [scribble_path, target], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if process.returncode != 0:
        click.echo(f"Scribble has encountered an error (code: {process.returncode})")
        click.echo("=====STDERR=====")
        click.echo(process.stderr.decode())
        click.echo("=====STDOUT=====")
        process.stdout.decode()
        return

    click.echo(process.stdout.decode())
