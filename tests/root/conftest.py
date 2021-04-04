import pytest

from .test_write_root_tree import test_run


@pytest.fixture(scope="session")
def rootfile():
    # other ROOT tests depend on the existence of this file
    # test_run will be run twice: once here, and also when tested.
    filename = test_run()
    return filename  # "file.root"
