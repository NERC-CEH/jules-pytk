from pathlib import Path
import tempfile

from jules_pytk.config import JulesInput

def test_load(jules_input, config_dir):
    assert jules_input.data is None
    jules_input.load(config_dir / jules_input.path)
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
