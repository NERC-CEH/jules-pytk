from pathlib import Path

import pytest


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
def test_input_dir() -> Path:
    """Path to experiment directory."""
    return Path(__file__).parent / "data" / "test_inputs"

@pytest.fixture
def ascii_file(test_input_dir) -> Path:
    """An example ascii file."""
    return test_input_dir / "rows_with_comments.dat"


@pytest.fixture
def netcdf_file(test_input_dir) -> Path:
    return test_input_dir / "point_dataset.nc"

@pytest.fixture
def namelist_file(namelists_dir) -> Path:
    return namelists_dir / "ancillaries.nml"
