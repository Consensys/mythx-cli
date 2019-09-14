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
