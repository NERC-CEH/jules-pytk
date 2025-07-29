from pathlib import Path

import pytest


from jules_pytk.config import (
    JulesConfig,
    JulesNamelists,
    JulesInputAscii,
    JulesInputNetcdf,
)
from jules_pytk.experiment import JulesExperiment


@pytest.fixture
def experiment_dir() -> Path:
    """Path to experiment directory."""
    return Path(__file__).parent / "data" / "experiment"


@pytest.fixture
def namelists_subdir() -> str:
    """Subdirectory of `experiment_dir` containing the namelist files."""
    return "namelists"


@pytest.fixture
def namelists_dir(experiment_dir, namelists_subdir) -> Path:
    return experiment_dir / namelists_subdir


@pytest.fixture
def jules_namelists(namelists_dir) -> JulesNamelists:
    """An instance of JulesNamelists."""
    return JulesNamelists.read(namelists_dir)


@pytest.fixture
def jules_input_ascii(experiment_dir) -> JulesInputAscii:
    """An instance of JulesInputAscii."""
    return JulesInputAscii(experiment_dir / "inputs" / "Loobos1997.dat")


@pytest.fixture
def jules_input_netcdf() -> JulesInputNetcdf:
    """An instance of JulesInputNetcdf."""
    raise NotImplementedError


@pytest.fixture
def jules_config(experiment_dir, namelists_subdir) -> JulesConfig:
    """An instance of JulesConfig."""
    return JulesConfig.read(experiment_dir, namelists_subdir=namelists_subdir)

@pytest.fixture
def test_input_dir() -> Path:
    """Path to experiment directory."""
    return Path(__file__).parent / "data" / "test_inputs"


@pytest.fixture
def netcdf_input(test_input_dir) -> Path:
    return test_input_dir / "point_dataset.nc"


'''
@pytest.fixture
def jules_experiment(experiment_dir, namelists_subdir) -> JulesExperiment:
    """An instance of JulesExperiment."""
    return JulesExperiment(experiment_dir, namelists_subdir)


'''
