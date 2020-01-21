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

E.g. :code:`mythx analyze --create-group dir1/ test.sol test2.sol` will initialize
an empty group, add all analyses coming from :code:`dir1/` and the two test Solidity
files into it, and close it once submission has been completed. The analyses will then
show up in their dedicated group inside the dashboard.


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
   helpful for when you need to "remember" long-running analysis IDs and cannot wait for them to
   finish, e.g. when running full-mode analyses on a CI server.


Filtering Reports
-----------------


Asynchronous Analysis
---------------------


CI Flags
--------


Fetching Multiple Reports
-------------------------


