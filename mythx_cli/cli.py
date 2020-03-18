"""The main runtime of the MythX CLI."""
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import click
import htmlmin
import jinja2
from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisStatusResponse,
    DetectedIssuesResponse,
)
from pythx import Client, MythXAPIError
from pythx.middleware.toolname import ClientToolNameMiddleware

from mythx_cli import __version__
from mythx_cli.analysis.list import analysis_list
from mythx_cli.analysis.report import analysis_report
from mythx_cli.analysis.status import analysis_status
from mythx_cli.analyze.command import analyze
from mythx_cli.formatter import FORMAT_RESOLVER, util
from mythx_cli.group.close import group_close
from mythx_cli.group.list import group_list
from mythx_cli.group.open import group_open
from mythx_cli.group.status import group_status
from mythx_cli.util import write_or_print

DEFAULT_HTML_TEMPLATE = Path(__file__).parent / "templates/default.html"
DEFAULT_MD_TEMPLATE = Path(__file__).parent / "templates/default.md"

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


@cli.group()
def group() -> None:
    """Create, modify, and view analysis groups.

    \f

    This subcommand holds all group-related actions, such as creating,
    listing, closing groups, as well as fetching the status of one
    or more group IDs.
    """
    pass


@cli.group()
def analysis() -> None:
    """Get information on running and finished analyses.

    \f

    This subcommand holds all analysis-related actions, such as submitting new
    analyses, listing existing ones, fetching their status, as well as fetching
    the reports of one or more finished analysis jobs.
    """
    pass


cli.add_command(analyze)

group.add_command(group_list)
group.add_command(group_status)
group.add_command(group_open)
group.add_command(group_close)

analysis.add_command(analysis_status)
analysis.add_command(analysis_list)
analysis.add_command(analysis_report)


def get_analysis_info(
    client,
    uuid: str,
    min_severity: Optional[str],
    swc_blacklist: Optional[List[str]],
    swc_whitelist: Optional[List[str]],
) -> Tuple[AnalysisStatusResponse, DetectedIssuesResponse, AnalysisInputResponse]:
    """Fetch information related to the specified analysis job UUID.

    Given a UUID, this function will query the MythX API for the
    analysis status, the analysis' input data, and the issue report.
    Furthermore, filtering parameters can be passed to remove certain
    SWCs or severities from the returned report.
    """

    resp: DetectedIssuesResponse = client.report(uuid)
    inp: Optional[AnalysisInputResponse] = client.request_by_uuid(uuid)
    status: AnalysisStatusResponse = client.status(uuid)
    util.filter_report(
        resp,
        min_severity=min_severity,
        swc_blacklist=swc_blacklist,
        swc_whitelist=swc_whitelist,
    )
    # extend response with job UUID to keep formatter logic isolated
    resp.uuid = uuid

    return status, resp, inp


@cli.command()
@click.argument("target")
@click.option(
    "--template",
    "-t",
    "user_template",
    type=click.Path(exists=True),
    help="A custom report template",
    default=None,
)
@click.option("--aesthetic", is_flag=True, default=False, hidden=True)
@click.option(
    "--markdown", is_flag=True, default=False, help="Render the report as Markdown"
)
@click.option(
    "--min-severity",
    type=click.STRING,
    help="Ignore SWC IDs below the designated level",
    default=None,
)
@click.option(
    "--swc-blacklist",
    type=click.STRING,
    help="A comma-separated list of SWC IDs to ignore",
    default=None,
)
@click.option(
    "--swc-whitelist",
    type=click.STRING,
    help="A comma-separated list of SWC IDs to include",
    default=None,
)
@click.pass_obj
def render(
    ctx,
    target: str,
    user_template: str,
    aesthetic: bool,
    markdown: bool,
    min_severity: Optional[str],
    swc_blacklist: Optional[List[str]],
    swc_whitelist: Optional[List[str]],
) -> None:
    """Render an analysis job or group report as HTML.

    \f
    :param ctx: Click context holding group-level parameters
    :param target: Group or analysis ID to fetch the data for
    :param user_template: User-defined template string
    :param aesthetic: DO NOT TOUCH IF YOU'RE BORING
    :param markdown: Flag to render a markdown report
    :param min_severity: Ignore SWC IDs below the designated level
    :param swc_blacklist: A comma-separated list of SWC IDs to ignore
    :param swc_whitelist: A comma-separated list of SWC IDs to include
    """

    client: Client = ctx["client"]

    default_template = DEFAULT_MD_TEMPLATE if markdown else DEFAULT_HTML_TEMPLATE
    # enables user to include library templates in their own
    template_dirs = [default_template.parent]

    if user_template:
        user_template = Path(user_template)
        template_name = user_template.name
        template_dirs.append(user_template.parent)
    else:
        template_name = default_template.name

    env_kwargs = {
        "trim_blocks": True,
        "lstrip_blocks": True,
        "keep_trailing_newline": True,
    }
    if not markdown:
        env_kwargs = {
            "trim_blocks": True,
            "lstrip_blocks": True,
            "keep_trailing_newline": True,
        }
        if aesthetic:
            template_name = "aesthetic.html"

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dirs), **env_kwargs
    )
    template = env.get_template(template_name)

    issues_list: List[
        Tuple[
            AnalysisStatusResponse,
            DetectedIssuesResponse,
            Optional[AnalysisInputResponse],
        ]
    ] = []
    if len(target) == 24:
        # identified group
        list_resp = client.analysis_list(group_id=target)
        offset = 0
        while len(list_resp.analyses) < list_resp.total:
            offset += len(list_resp.analyses)
            list_resp.analyses.extend(
                client.analysis_list(group_id=target, offset=offset)
            )

        for analysis_ in list_resp.analyses:
            click.echo("Fetching report for analysis {}".format(analysis_.uuid))
            status, resp, inp = get_analysis_info(
                client=client,
                uuid=analysis_.uuid,
                min_severity=min_severity,
                swc_blacklist=swc_blacklist,
                swc_whitelist=swc_whitelist,
            )
            issues_list.append((status, resp, inp))
    elif len(target) == 36:
        # identified analysis UUID
        click.echo("Fetching report for analysis {}".format(target))
        status, resp, inp = get_analysis_info(
            client=client,
            uuid=target,
            min_severity=min_severity,
            swc_blacklist=swc_blacklist,
            swc_whitelist=swc_whitelist,
        )
        issues_list.append((status, resp, inp))
    else:
        raise click.UsageError(
            "Invalid target. Please provide a valid group or analysis job ID."
        )

    rendered = template.render(issues_list=issues_list, target=target)
    if not markdown:
        rendered = htmlmin.minify(rendered, remove_comments=True)

    write_or_print(rendered, mode="w+")


@cli.command()
@click.pass_obj
def version(ctx) -> None:
    """Display API version information.

    \f

    :param ctx: Click context holding group-level parameters
    :return:
    """

    resp = ctx["client"].version()
    write_or_print(FORMAT_RESOLVER[ctx["fmt"]].format_version(resp))


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
