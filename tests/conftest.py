from pathlib import Path

import pytest

from jules_pytk.config import JulesConfig

@pytest.fixture
def config_dir() -> Path:
    """Path to directory containing the test config, i.e. namelist files."""
    return Path(__file__).parent / "data" / "config"

@pytest.fixture
def config(config_dir) -> JulesConfig:
    """An instance of JulesConfig with the test config loaded."""
    return JulesConfig.load(config_dir)
