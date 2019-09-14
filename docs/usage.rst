=====
Usage
=====

Format Options
--------------

A format option is passed to the :code:`--format` option of the :code:`mythx`
root command. E.g.::

    $ mythx --format json-pretty report ab9092f7-54d0-480f-9b63-1bb1508280e2

This will print the report for the given analysis job UUID in pretty-printed
JSON format to stdout. Currently the following formatters are avialable:

* :code:`simple` (default): Print the results in simple plain text (easy to
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


The Analysis Functionality
--------------------------

TODO

.. code-block:: console

  Usage: mythx analyze [OPTIONS] [TARGET]...

  Options:
    --async / --wait     Submit the job and print the UUID, or wait for
                         execution to finish
    --mode [quick|full]
    --help               Show this message and exit.


Listing Past Analyses
---------------------

TODO

.. code-block:: console

  Usage: mythx list [OPTIONS]

  Options:
  --number INTEGER RANGE  The number of most recent analysis jobs to display
  --help                  Show this message and exit.


Fetching Analysis Reports
-------------------------

TODO

.. code-block:: console

  Usage: mythx report [OPTIONS] [UUIDS]...

  Options:
    --help  Show this message and exit.


Fetching Analysis Status
------------------------

TODO

.. code-block:: console

  Usage: mythx status [OPTIONS] [UUIDS]...

  Options:
  --help  Show this message and exit.


Fetching API Version Information
--------------------------------

.. code-block:: console

  Usage: mythx version [OPTIONS]

  Options:
  --help  Show this message and exit.
