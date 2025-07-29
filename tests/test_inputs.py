from pathlib import Path
import tempfile

import numpy
import pytest

from jules_pytk.config import JulesInput, JulesInputAscii, JulesInputNetcdf


@pytest.mark.parametrize("suffix", JulesInputAscii.valid_extensions)
def test_read_ascii(suffix):
    file_contents = "\n".join(["# comment"] + ["1 2 3 4 5" for _ in range(10)])

    with tempfile.NamedTemporaryFile(suffix=suffix, delete_on_close=False) as tmp:
        with open(tmp.name, "w") as file:
            file.write(file_contents)

        input = JulesInputAscii.read(tmp.name)

    assert input.data is not None
    assert isinstance(input.data, numpy.ndarray)
    assert len(input.data) == 10
    assert input.comment.strip() == "comment"


def test_read_netcdf(netcdf_input):
    input = JulesInputNetcdf.read(netcdf_input)


def _test_load(jules_input, experiment_dir):
    assert jules_input.data is None
    jules_input.load(experiment_dir / jules_input.path)
    assert jules_input.data is not None


def _test_dump(jules_input_loaded):
    assert jules_input_loaded.data is not None

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        jules_input_loaded.dump(temp_dir / jules_input_loaded.path)

        assert (temp_dir / jules_input_loaded.path).exists()


def _test_round_trip(jules_input_loaded):
    assert jules_input_loaded.data is not None

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        jules_input_loaded.dump(temp_dir / jules_input_loaded.path)

        assert (temp_dir / jules_input_loaded.path).exists()

        jules_input_reloaded = JulesInput(jules_input_loaded.path)
        jules_input_reloaded.load(temp_dir / jules_input_loaded.path)

        assert jules_input_reloaded == jules_input_loaded
