"""The main runtime of the MythX CLI."""
import logging
import sys

import click
from pythx import Client, MythXAPIError
from pythx.middleware.toolname import ClientToolNameMiddleware

from mythx_cli import __version__
from mythx_cli.analysis.list import analysis_list
from mythx_cli.analysis.report import analysis_report
from mythx_cli.analysis.status import analysis_status
from mythx_cli.analyze.command import analyze
from mythx_cli.formatter import FORMAT_RESOLVER
from mythx_cli.group.close import group_close
from mythx_cli.group.list import group_list
from mythx_cli.group.open import group_open
from mythx_cli.group.status import group_status
from mythx_cli.render.command import render
from mythx_cli.version.command import version

LOGGER = logging.getLogger("mythx-cli")
logging.basicConfig(level=logging.WARNING)


class APIErrorCatcherGroup(click.Group):
    """A custom click group to catch API-related errors.

    This custom Group implementation catches :code:`MythXAPIError`
    exceptions, which get raised when the API returns a non-200
    status code. It is used to notify the user about the error that
    happened instead of triggering an uncaught exception traceback.

    It is given to the main CLI entrypoint and propagated to all
    subcommands.
    """

    def __call__(self, *args, **kwargs):
        try:
            return self.main(*args, **kwargs)
        except MythXAPIError as exc:
            click.echo("The API returned an error:\n{}".format(exc))
            sys.exit(1)


# noinspection PyIncorrectDocstring
@click.group(cls=APIErrorCatcherGroup)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    envvar="MYTHX_DEBUG",
    help="Provide additional debug output",
)
@click.option(
    "--api-key", envvar="MYTHX_API_KEY", help="Your MythX API key from the dashboard"
)
@click.option(
    "--username", envvar="MYTHX_USERNAME", help="Your MythX account's username"
)
@click.option(
    "--password", envvar="MYTHX_PASSWORD", help="Your MythX account's password"
)
@click.option(
    "--format",
    "fmt",
    default="table",
    type=click.Choice(FORMAT_RESOLVER.keys()),
    show_default=True,
    help="The format to display the results in",
)
@click.option(
    "--ci",
    is_flag=True,
    default=False,
    help="Return exit code 1 if high-severity issue is found",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    default=False,
    help="Do not prompt for any confirmations",
)
@click.option(
    "-o", "--output", default=None, help="Output file to write the results into"
)
@click.pass_context
def cli(ctx, **kwargs) -> None:
    """Your CLI for interacting with https://mythx.io/

    \f

    :param ctx: Click context holding group-level parameters
    :param debug: Boolean to enable the `logging` debug mode
    :param api_key: User JWT api token from the MythX dashboard
    :param username: The MythX account ETH address/username
    :param password: The account password from the MythX dashboard
    :param fmt: The formatter to use for the subcommand output
    :param ci: Boolean to return exit code 1 on medium/high-sev issues
    :param output: Output file to write the results into
    """

    ctx.obj = dict(kwargs)
    ctx.obj["retval"] = 0
    toolname_mw = ClientToolNameMiddleware(name="mythx-cli-{}".format(__version__))
    if kwargs["api_key"] is not None:
        ctx.obj["client"] = Client(api_key=kwargs["api_key"], middlewares=[toolname_mw])
    elif kwargs["username"] and kwargs["password"]:
        ctx.obj["client"] = Client(
            username=kwargs["username"],
            password=kwargs["password"],
            middlewares=[toolname_mw],
        )
    else:
        raise click.UsageError(
            (
                "The trial user has been deprecated. You can still use the MythX CLI for free "
                "by signing up for a free account at https://mythx.io/ and entering your access "
                "credentials."
            )
        )
    if kwargs["debug"]:
        for name in logging.root.manager.loggerDict:
            logging.getLogger(name).setLevel(logging.DEBUG)


cli.add_command(analyze)
cli.add_command(render)
cli.add_command(version)


@cli.group()
def group() -> None:
    """Create, modify, and view analysis groups.

    \f

    This subcommand holds all group-related actions, such as creating,
    listing, closing groups, as well as fetching the status of one
    or more group IDs.
    """
    pass


group.add_command(group_list)
group.add_command(group_status)
group.add_command(group_open)
group.add_command(group_close)


@cli.group()
def analysis() -> None:
    """Get information on running and finished analyses.

    \f

    This subcommand holds all analysis-related actions, such as submitting new
    analyses, listing existing ones, fetching their status, as well as fetching
    the reports of one or more finished analysis jobs.
    """
    pass


analysis.add_command(analysis_status)
analysis.add_command(analysis_list)
analysis.add_command(analysis_report)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
