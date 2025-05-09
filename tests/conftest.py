"""
Pytest configuration and shared fixtures.
"""

import os
import shutil
import pytest


# Copy hdem to hdem.py before any tests run
# This needs to be at the module level, not inside a fixture
# to ensure it happens before any imports in test files
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
hdem_path = os.path.join(project_root, "hdem")
hdem_py_path = os.path.join(project_root, "hdem.py")

if not os.path.exists(hdem_py_path) and os.path.exists(hdem_path):
    shutil.copy2(hdem_path, hdem_py_path)


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    """Clean up the copied hdem.py file after all tests."""
    yield

    # Clean up the temporary file
    if os.path.exists(hdem_py_path):
        os.remove(hdem_py_path)
