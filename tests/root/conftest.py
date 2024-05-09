import os

import pytest

# can't import it here, because
# conftest will be always run irrespective of ROOT availability
# from .test_write_root_tree import test_run

# to mark all files from this directory as 'ROOT', see this answer:
# https://stackoverflow.com/a/57046943/952234
# copy here:
"""
import pathlib
import pytest


def pytest_collection_modifyitems(config, items):
    # python 3.4/3.5 compat: rootdir = pathlib.Path(str(config.rootdir))
    rootdir = pathlib.Path(config.rootdir)
    for item in items:
        rel_path = pathlib.Path(item.fspath).relative_to(rootdir)
        mark_name = next((part for part in rel_path.parts if part.endswith('_tests')), '').rstrip('_tests')
        if mark_name:
            mark = getattr(pytest.mark, mark_name)
            item.add_marker(mark)
"""

# other ROOT tests depend on the existence of this file
@pytest.fixture(scope="session")
def rootfile():
    from .test_write_root_tree import test_run

    filename = "file.root"
    if not os.path.exists(filename):
        test_run()
    return filename
