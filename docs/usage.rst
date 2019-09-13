=====
Usage
=====

Format Options
--------------

TODO


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

..code-block:: console

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
