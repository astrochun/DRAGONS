"""
Configuration for tests that will propagate inside DRAGONS.
"""

import os
import pytest

# noinspection PyUnresolvedReferences
from astrodata.testing import (astrofaker, base_temp, change_working_dir,
                               path_to_inputs, path_to_outputs, path_to_refs)


def pytest_addoption(parser):
    try:
        parser.addoption(
            "--dragons-remote-data",
            action="store_true",
            default=False,
            help="Enable tests that use the download_from_archive function."
        )
        parser.addoption(
            "--do-plots",
            action="store_true",
            default=False,
            help="Plot results of each test after running them."
        )
        parser.addoption(
            "--keep-data",
            action="store_true",
            default=False,
            help="Keep intermediate data (e.g. pre-stack data)."
        )
    # This file is imported several times and might bring conflict
    except ValueError:
        pass


def pytest_configure(config):
    config.addinivalue_line("markers", "dragons_remote_data: tests with this "
                                       "mark will download a large volume of "
                                       "data and run")
    config.addinivalue_line("markers", "preprocessed_data: tests with this "
                                       "download anr preprocess the data if it "
                                       "does not exist in the cache folder.")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--dragons-remote-data"):
        marker = pytest.mark.skip(reason="need --dragons-remote-data to run")
        for item in items:
            if "dragons_remote_data" in item.keywords:
                item.add_marker(marker)


def pytest_report_header(config):
    return f"DRAGONS_TEST directory: {os.getenv('DRAGONS_TEST')}"
