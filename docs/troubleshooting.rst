===============
Troubleshooting
===============


Solidity Compilation Issues under macOS
---------------------------------------

Under OSX/macOS, Solidity targets passed to the :code:`mythx analyze` command can fail.
This can look as follows:

.. code-block:: shell

    $ mythx analyze --mode quick contracts/**/*.sol
    Unsupported macOS version.
    We only support Mavericks, Yosemite, El Capitan, Sierra, High Sierra and Mojave.
    Usage: mythx analyze [OPTIONS] [TARGET]...

    Error: Error installing solc version v0.5.10: Command '['sh', '/var/folders/vk/01zl87497jx6bq66fhhhd9zm0000gn/T/py-solc-x-tmp/solidity_0.5.10/scripts/install_deps.sh']' returned non-zero exit status 1.

This error is raised by the :code:`py-solc-x` dependency, which is responsible for the automatic
setup of solc and correct compilation. Please consult `this wiki article <https://github.com/iamdefinitelyahuman/py-solc-x/wiki/Installing-Solidity-on-OSX>`_
for instructions to correctly set up your Solidity compiler. If the issue still persists, feel free
to `open an issue <https://github.com/iamdefinitelyahuman/py-solc-x/issues>`_ in the :code:`py-solc-x`
repository.


Overriding a YAML-defined Output File
-------------------------------------

Depending on your setup, you might find yourself in the situation where you have defined a :code:`.mythx.yml`
file, with an output key such as :code:`output: foo.json`. Now, whenever you run the CLI in this directory, the
YAML file is picked up on, and output of all MythX CLI commands is written to that file. Before the MythX CLI
version :code:`v0.6.18` the only workaround was to override the YAML configuration altogether by passing in
an explicit, empty configuration file parameter, such as :code:`mythx --config=/dev/null analysis list`.
This has been fixed in the following versions by introducing the :code`--stdout` flag. Now, to override the
output file definition, simply run:

.. code-block:: console

    mythx --stdout analysis list

This will preserve all your YAML configuration options, just overriding the output file definition.
