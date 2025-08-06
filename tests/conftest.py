from pathlib import Path

import pytest


@pytest.fixture
def jules_dir() -> Path:
    """Path to jules directory."""
    return Path(__file__).parent / "data" / "experiment"


@pytest.fixture
def namelists_subdir() -> str:
    """Subdirectory of `jules_dir` containing the namelist files."""
    return "namelists"


@pytest.fixture
def inputs_subdir() -> str:
    return "inputs"


@pytest.fixture
def namelists_dir(jules_dir, namelists_subdir) -> Path:
    return jules_dir / namelists_subdir


@pytest.fixture
def inputs_dir(jules_dir, inputs_subdir) -> Path:
    return jules_dir / inputs_subdir


@pytest.fixture
def test_inputs_dir() -> Path:
    """Path to experiment directory."""
    return Path(__file__).parent / "data" / "test_inputs"


@pytest.fixture
def ascii_file(test_inputs_dir) -> Path:
    """An example ascii file."""
    return test_inputs_dir / "rows_with_comments.dat"


@pytest.fixture
def netcdf_file(test_inputs_dir) -> Path:
    return test_inputs_dir / "point_dataset.nc"


@pytest.fixture
def namelist_file(namelists_dir) -> Path:
    return namelists_dir / "ancillaries.nml"
