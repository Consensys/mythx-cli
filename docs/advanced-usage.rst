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


Filtering Reports
-----------------


Asynchronous Analysis
---------------------


CI Flags
--------


Fetching Multiple Reports
-------------------------


