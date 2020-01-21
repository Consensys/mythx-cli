==============
Advanced Usage
==============

The purpose of this document is to give an introduction to advanced usage patterns
of the MythX CLI as well as functionality the user might not have been aware of.


Automatic Group Creation
------------------------

The basic workflow for attaching analyses to groups can be divided into the following
steps:

1. Open a new group with :code:`mythx group open`
2. Submit analyses in reference to the new group :code:`mythx analyze --group-id <ID>`
3. Close the group when done :code:`mythx group close <ID>`

This can become very annoying and hinder automation tasks leveraging the MythX CLI.
Because of that, the :code:`--create-group` flag has been introduced. Passing this
flag to :code:`mythx analyze` will automatically open a group before submitting new
analysis jobs, and close it after the submission process has been completed. This
functionality encapsulates all targets passed to the :code:`analyze` subcommand.

A short example:

.. code::

    mythx analyze --create-group dir1/ test.sol test2.sol

This command will initialize an empty group, add all analyses coming from :code:`dir1/`
and the two test Solidity files into it, and close it once submission has been completed.
The analyses will then show up in their dedicated group inside the dashboard.


File Output
-----------

Especially in scenarios of automation the need often arises to persist data and store it
as files. Since version :code:`0.4.0` the base :code:`mythx` command carries the
:code:`--output` option. This allows you to take the :code:`stdout` from any subcommand
and store it as a file. This can be very helpful for storing analysis job and group IDs
for long-running asynchronous jobs - which we will also outline in this document.

The :code:`--format` option is fully supported with :code:`--output` and allows the user
to define what is written to the file. Furthermore, it can be combined with every
subcommand :code:`mythx` supports.

Examples:

1. :code:`mythx --output=status.json --format=json-pretty status <id>`: Output the status of
   an analysis job in pretty-printed JSON format to :code:`status.json`.
2. :code:`mythx --output=report.json --format=json report report <id>`: This is equivalent as
   above with the difference being that now the analysis job's report is fetched and directly
   written to the file. This is especially useful for testing new formatters and other
   integrations with static input.
3. :code:`mythx --output=analyses.txt analyze --async <targets>`: This performs a quick analysis
   on the defined targets (e.g. truffle projects, Solidity files) and instead of waiting for the
   results, simply writes the analysis job IDs to the :code:`analyses.txt` files. This can be
   helpful for when you need to persist long-running analysis IDs and cannot wait for them to
   finish, e.g. when running full-mode analyses on a CI server.


Filtering Reports
-----------------

The MythX CLI offers a variety of flags to filter report output. These are available in the
:code:`analyze` and :code:`report` subcommands respectively and identical in their behaviour.
Report filtering can be used to hide unwanted issues detected by MythX, e.g. a floating Solidity
compiler pragma (`SWC-103 <https://swcregistry.io/docs/SWC-103>`_). There are three flags with
report filtering capabilities available:

1. :code:`--swc-blacklist`: Ignore specific SWC IDs, e.g. :code:`--swc-blacklist SWC-104` will
   display all found issues except for unchecked call return values.
2. :code:`--swc-whitelist`: Ignore all SWC IDs that do not match the given ones, e.g.
   :code:`--swc-whitelist 110,123` will only display requirement and assert violations.
3. :code:`--min-severity`: Ignore issues below the given severity, e.g. :code:`--min-severity medium`
   ignores all low severity issues.

The SWC black- and whitelist parameters support a variety of formats. Besides individual SWC IDs, the
user can also pass in a comma-separated list of multiple IDs to submit a list. Furthermore, the inputs
can be expressed in different manners, i.e. :code:`swc-110`, :code:`SWC-110`, and :code:`110` all target
the same SWC ID. List submission works in the same way, so :code:`--swc-blacklist=SWC-101,102,swc-103` is
a valid way to exclude IDs 101-103 from the report, even though it is definitely recommended to stick with
a consistent notation for readability purposes.


Asynchronous Analysis
---------------------

As mentioned before, the :code:`analyze` subcommand offers the :code:`--async` flag. This will prevent
the CLI from blocking after the submission of one or multiple analysis jobs and waiting for them to finish.
Instead, for each analysis job the job's UUID will be printed to :code:`stdout`, or to a file, if the
:code:`--output` option is passed as well. This feature is often used in CI scenarios, where the server
job is not expected to run for very long. It is strongly recommended that this flag is used in combination
with MythX plans that offer higher analysis times. These scans are more exhaustive, deliver more precise
results, but as a trade-off take longer to process. In the CI server scenario, a developer might choose to
submit analyses asynchronously and check on the job later in the MythX dashboard. Alternatively, the job
IDs could also be stored in a file as a CI artifact and later retrieved by another part of the pipeline,
e.g. to kickstart a security or QA pipeline.

An example is the submission of a large truffle project:
.. code::

    mythx analyze --async my-project/

This flag is also best friends with the :code:`--create-group` flag for the :code:`analyze` subcommand. Together
they help keeping the MythX dashboard overview tidy.


The CI Flag
-----------

MythX is designed to support developers throughout the process of building their product by providing
continuous security checks. It is self-understood that CI use cases present their own set of challenges,
and the MythX CLI aims to support this process by providing the `--ci` flag in the base command. This
flag sets the application's return code to 1 if any issues were found in the analysis.

The true power of this flag becomes apparent when taking into consideration that it is fully integrated
with the options available for report filtering. This means that the return code can be set depending on
the input provided to the :code:`swc-blacklist`, :code:`swc-whitelist`, and :code:`min-severity` options.
A use case is to make CI jobs only fail on high-severity issues, but excluding a subset of them because
they are already in the process of being fixed, or insignificant relating to the business logic.

The filtering options can be freely combined with the :code:`--ci` flag to achieve the desiged behaviour.
A simple example is excluding the (fairly common) floating pragma issue type, and assert and requirement
violations for testing purposes:

.. code::

    mythx --ci analyze --swc-blacklist 110,123,103 my-project/

