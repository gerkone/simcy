import pytest

import simcy
import simpy


@pytest.fixture
def log():
    return []


@pytest.fixture
def env_py():
    return simpy.Environment()

@pytest.fixture
def env():
    return simcy.Environment()
