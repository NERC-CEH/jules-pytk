from pathlib import Path
import tempfile

import numpy
import pytest

from jules_pytk.inputs import JulesInput, JulesInputAscii, JulesInputNetcdf


@pytest.mark.parametrize("suffix", JulesInputAscii.valid_extensions)
def test_read_ascii(jules_input_ascii, suffix):
    assert jules_input_ascii.data is None

    file_contents = "\n".join(
            ["# comment"] + ["1 2 3 4 5" for _ in range(10)]
    )

    with tempfile.TemporaryFile(suffix=suffix) as fp:
        fp.write(file_contents)
        jules_input_ascii.read_(fp.name)

    data = jules_input_ascii.data
    assert data is not None
    print(data)
    #assert isinstance(data, numpy.ndarray)
    #assert len(data) == 10
    #assert jules_input_ascii.comment == "# comment"

def test_load(jules_input, experiment_dir):
    assert jules_input.data is None
    jules_input.load(experiment_dir / jules_input.path)
    assert jules_input.data is not None


def test_dump(jules_input_loaded):
    assert jules_input_loaded.data is not None

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        jules_input_loaded.dump(temp_dir / jules_input_loaded.path)

        assert (temp_dir / jules_input_loaded.path).exists()


def test_round_trip(jules_input_loaded):
    assert jules_input_loaded.data is not None

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        jules_input_loaded.dump(temp_dir / jules_input_loaded.path)

        assert (temp_dir / jules_input_loaded.path).exists()

        jules_input_reloaded = JulesInput(jules_input_loaded.path)
        jules_input_reloaded.load(temp_dir / jules_input_loaded.path)

        assert jules_input_reloaded == jules_input_loaded
