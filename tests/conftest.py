from pathlib import Path

import pytest

from jules_pytk.config import JulesConfig, JulesConfigMeta, JulesNamelists

@pytest.fixture
def config_dir() -> Path:
    """Path to directory containing the test config, i.e. namelist files."""
    return Path(__file__).parent / "data" / "test_config"

@pytest.fixture
def namelists_dir(config_dir) -> Path:
    """Path to directory containing the test config, i.e. namelist files."""
    return config_dir / "namelists"

@pytest.fixture
def jules_config_meta(config_dir) -> JulesConfigMeta:
    """An instance of JulesConfigMeta from the test config."""
    return JulesConfigMeta.load(config_dir)

@pytest.fixture
def jules_namelists(namelists_dir) -> JulesNamelists:
    """An instance of JulesNamelists from the test config."""
    return JulesNamelists.load(namelists_dir)

@pytest.fixture
def jules_config(config_dir) -> JulesConfig:
    """An instance of JulesConfig with the test config loaded."""
    return JulesConfig.load(config_dir)
