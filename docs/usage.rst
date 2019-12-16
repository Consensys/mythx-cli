=====
Usage
=====

Format Options
--------------

A format option is passed to the :code:`--format` option of the :code:`mythx`
root command. E.g.::

    $ mythx --format json-pretty analysis report ab9092f7-54d0-480f-9b63-1bb1508280e2

This will print the report for the given analysis job UUID in pretty-printed
JSON format to stdout. Currently the following formatters are available:

* :code:`tabular` (default): Print the results in a pretty (extended) ASCII table.
* :code:`simple`: Print the results in simple plain text (easy to
  grep). This does not include all result data but a subset of it that seems
  relevant for most use-cases.
* :code:`json`: Print all of the result data as a single-line JSON string to
  stdout.
* :code:`json-pretty`: The same as :code:`json`, just pretty-printed, with an
  indentation of two spaces and alphabetically sorted object keys.


Authentication
--------------

By default the MythX CLI authenticates the user under the free trial account.
This means that no account needs to be created on first use. Simply run an
analysis, fetch the results and enjoy the free MythX service!

Of course, registering for a free MythX account and upgrading come with
`additional perks <https://mythx.io/plans/>`. If you have set up an account,
head over to the MythX `analysis dashboard <https://dashboard.mythx.io/>`.
Head to your *Profile* settings and enter your password in the *MythX API Key*
section. You will be able to copy a new API access token once it has been
generated. Set the environment variable :code:`MYTHX_ACCESS_TOKEN` with your
JWT token and start using the MythX CLI as authenticated user. You will be
able to see all your submitted analyses, their status, reports, and more on
the dashboard.

Note that you can also pass the JWT token directly to the CLI via the
:code:`--access-token` option. For security reasons it is however
recommended to always pass the token through a pre-defined environment
variable or a shell script you :code:`source` from.

Alternatively, username and password can be used for authentication. This
functionality is considered deprecated due to security concerns and will be
removed from the MythX API in the future. For compatibility reasons it has
been included, however. The username corresponds to the Ethereum address the
MythX account has been registered under, and the password is the one that the
user can set in the MythX dashboard. Both can be passed with the
:code:`--eth-address` and :code:`--password` option respectively, or by setting
the :code:`MYTHX_ETH_ADDRESS` and :code:`MYTHX_PASSWORD` environment variables.

Note that if an access token is passed in directly as well, it will take
precedence and no login with username and password is performed.


The Grouping Functionality
-----------------------------------

.. code-block:: console

    Usage: mythx group [OPTIONS] COMMAND [ARGS]...

      Create, modify, and view analysis groups.

    Options:
      --help  Show this message and exit.

    Commands:
      close   Close/seal an existing group.
      list    Get a list of analysis groups.
      open    Create a new group to assign future analyses to.
      status  Get the status of an analysis group.

An analysis group can be regarded as a container. It is supposed to capture groups of
analyses and display them in an easy-to-read overview in the MythX dashboard.

To open a new group, simply type:

.. code-block:: console

    $ mythx group open "super important"
    Opened group with ID 5df7c8932a73230011271d27 and name 'super important'

The name is optional and can be omitted if not needed. Now to analyze a sample, simply pass
the group ID (and optionally the name) as parameters to the :code:`mythx analyze` call:

.. code-block::

    $ mythx analyze --group-name "super important" --group-id 5df7c8932a73230011271d27 --async fallout.sol remythx-mbt385.sol token.sol functiontypes-swc127.sol

This will associate the individual analysis jobs to the same group in the MythX Dashboard:

.. image:: img/dashboard.png
    :alt: The MythX dashboard showing the analysis group
    :align: center

After all data has been submitted, the group must be closed again using

.. code-block:: console

    $ mythx group close 5df7c8932a73230011271d27
    Closed group with ID 5df7c8932a73230011271d27 and name 'super important'


The Analysis Functionality
--------------------------

.. code-block:: console

    $ mythx analyze --help
    Usage: mythx analyze [OPTIONS] [TARGET]...

      Analyze the given directory or arguments with MythX.

    Options:
      --async / --wait      Submit the job and print the UUID, or wait for
                            execution to finish
      --mode [quick|full]   [default: quick]
      --group-id TEXT       The group ID to add the analysis to
      --group-name TEXT     The group name to attach to the analysis
      --min-severity TEXT   Ignore SWC IDs below the designated level
      --swc-blacklist TEXT  A comma-separated list of SWC IDs to ignore
      --solc-version TEXT   The solc version to use for Solidity compilation
      --help                Show this message and exit.


Submit a new analysis to MythX. This command works in different scenarios,
simply by calling :code:`mythx analyze`:

1. Either :code:`truffle-config.js` or :code:`truffle.js` are found in the
   directory. In this case, the MythX CLI checks the
   :code:`<project_dir>/build/contracts` path for artifact JSON files
   generated by the :code:`truffle compile` command. For each artifact found
   a new job is submitted to the MythX API.
2. If no Truffle project can be detected, the MythX CLI will automatically
   enumerate all Solidity files (having the :code:`.sol` extension) in the
   current directory. A confirmation prompt will be displayed asking the user
   to confirm the submission of the number of smart contracts found. This is
   done to make sure a user does not accidentally submit a huge repository of
   Solidity files (unless they actually want it). For automation purposes
   the prompt can automatically be confirmed by piping :code:`yes` into the
   command, i.e. :code:`yes | mythx analyze`.
3. To analyze specific Solidity files or bytecode, data can also explicitly
   be passed to the :code:`analyze` subcommand. The two supported argument
   types are creation bytecode strings (beginning with :code:`0x`) and
   Solidity files (valid files ending with with :code:`.sol`). The arguments
   can have arbitrary order and for each a new analysis request will be
   submitted.

If a Solidity file is analyzed in any of the given scenarios, the MythX CLI
will attempt to automatically compile the file and obtain data such as the
creation bytecode and the Solidity AST to enrich the request data submitted to
the MythX API. This will increase the number of detected issues (as e.g.
symbolic execution tools in the MythX backend can pick up on the bytecode), as
well as reduce the number of false positive issues. The MythX CLI will try to
estimate the :code:`solc` version based on the pragma set in the source code.


Asynchronous Analysis
~~~~~~~~~~~~~~~~~~~~~

In any of the above scenarios the :code:`analyze` subcommand will poll the
MythX API for job completion and print the analysis report in the
user-specified format. In some situations it might not be desired to wait for
the results. The MythX CLI offers an option to only submit the analysis, print
the job's UUID, and exit. In any scenario, simply pass the :code:`--async`
flag. E.g. in the scenario of a Continuous Integration (CI) server the
submitted UUIDs can be stored in the first step::

    $ mythx analyze --async > uuids.txt

This file can be stored as a CI job artifact. Later, when the (potentially
very exhaustive and long) analysis run has finished, the reports can be
retrieved. This is done by simply providing the stored job IDs as an
argument list to the :code:`mythx report` command::

    $ cat uuids.txt | xargs mythx analysis report

Optionally, the format can be changed here as well, e.g. to JSON, to allow
for easier automated processing further on.


Listing Past Analyses
---------------------

.. code-block:: console

    Usage: mythx analysis list [OPTIONS]

    Options:
    --number INTEGER RANGE  The number of most recent analysis jobs to display
    --help                  Show this message and exit.

This subcommand lists the past analyses associated to the current user. Note
that this functionality is not available for the default trial account to
ensure the confidentiality of analyses submitted by its users.

By default this subcommand will list the past five analyses associated to the
authenticated user account. The number of returned analyses can be updated by
passing the :code:`--number` option. It is worth noting that in its current
version (:code:`v1.4.34.4`) the API returns only objects of 20 analyses per
call. If a number greater than this is passed to :code:`mythx analysis list`, the MythX
CLI will automatically query the next page until the desired number is
reached.

To prevent too many network requests, the maximum number of analyses that can
be fetched it capped at 100.::

    $ mythx analysis list
    ╒══════════════════════════════════════╤══════════╤═════════════════╤══════════════════════════════════╕
    │ ac5af0dd-bd78-4cfb-b4ed-32f21216aaf6 │ Finished │ mythx-cli-0.2.1 │ 2019-10-30 09:41:36.165000+00:00 │
    ├──────────────────────────────────────┼──────────┼─────────────────┼──────────────────────────────────┤
    │ 391db48f-9e89-424f-8063-7626fdd2051e │ Finished │ mythx-cli-0.2.1 │ 2019-10-30 09:40:59.868000+00:00 │
    ├──────────────────────────────────────┼──────────┼─────────────────┼──────────────────────────────────┤
    │ 5a1fc208-7a7f-425a-bbc5-8512e5c37b50 │ Finished │ mythx-cli-0.2.1 │ 2019-10-30 09:40:06.092000+00:00 │
    ├──────────────────────────────────────┼──────────┼─────────────────┼──────────────────────────────────┤
    │ 1667a99d-6335-4a71-aa78-0d729e25b8e1 │ Finished │ mythx-cli-0.2.1 │ 2019-10-30 09:39:47.736000+00:00 │
    ├──────────────────────────────────────┼──────────┼─────────────────┼──────────────────────────────────┤
    │ fa88b710-e423-4535-a7b1-0c8c71833724 │ Finished │ mythx-cli-0.2.1 │ 2019-10-30 09:38:23.064000+00:00 │
    ╘══════════════════════════════════════╧══════════╧═════════════════╧══════════════════════════════════╛

Fetching Analysis Reports
-------------------------

.. code-block:: console

    Usage: mythx analysis report [OPTIONS] [UUIDS]...

    Options:
    --help  Show this message and exit.


This subcommand prints the report of one or more finished analyses in the
user-specified format. By default, it will print a simple text representation
of the report to stdout. This will alos resolve the report's source map
locations to the corresponding line and column numbers in the Solidity source
file. This is only possible if the user has specified the source map in their
request and is passing the Solidity source code as text.::

    $ mythx --format=simple analysis report ab9092f7-54d0-480f-9b63-1bb1508280e2
    UUID: ab9092f7-54d0-480f-9b63-1bb1508280e2
    Title: Assert Violation (Low)
    Description: It is possible to trigger an exception (opcode 0xfe). Exceptions can be caused by type errors, division by zero, out-of-bounds array access, or assert violations. Note that explicit `assert()` should only be used to check invariants. Use `require()` for regular input checking.


    /home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol:24
      mapping(uint256 => uint256[]) public estateLandIds;




Fetching Analysis Status
------------------------

.. code-block:: console

    Usage: mythx analysis status [OPTIONS] [UUIDS]...

    Options:
    --help  Show this message and exit.

This subcommand prints the status of an already submitted analysis.::

    $ mythx --format=simple analysis status 381eff48-04db-4f81-a417-8394b6614472
    UUID: 381eff48-04db-4f81-a417-8394b6614472
    Submitted at: 2019-09-05 20:34:27.606000+00:00
    Status: Finished

By default a simple text representation is printed to stdout, more data on the
MythX API's status response can be obtained by specifying an alternative output
format such as :code:`json-pretty`.


Fetching API Version Information
--------------------------------

.. code-block:: console

    Usage: mythx version [OPTIONS]

    Options:
    --help  Show this message and exit.

This subcommand hits the MythX API's :code:`/version` endpoint and obtains
version information on the API. This can be especially useful for continuous
scans as the backend tool capabilities of MythX are constantly being improved.
This means that it's a good idea to rerun old scans with newer versions of
MythX as potentially more vulnerabilities can be found, false positives are
removed, and additional helpful data can be returned.

The MythX team has included a hash of all versions so changes are easily
noticed simply by comparing the hash an analysis has run under with the one
returned by the API.::

    $ mythx version
    API: v1.4.34.4
    Harvey: 0.0.33
    Maru: 0.5.3
    Mythril: 0.21.14
    Hashed: 00c17c8b0ae13bebc9a7f678d8ee55db

This output can be adapted using the :code:`--format` parameter as well to
fetch e.g. JSON output for easier parsing.
