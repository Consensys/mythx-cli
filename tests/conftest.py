import logging
import os


def pytest_generate_tests(metafunc):
    os.environ["MYTHX_API_KEY"] = "test"
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.DEBUG)
