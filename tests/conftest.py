import os


def pytest_generate_tests(metafunc):
    os.environ["MYTHX_ACCESS_TOKEN"] = "test"
