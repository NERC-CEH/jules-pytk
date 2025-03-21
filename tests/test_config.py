import dataclasses
from pathlib import Path
import tempfile

from jules_pytk.config import JulesConfig



def test_read_config(config_dir):
    """Test that configurations can be read."""
    _ = JulesConfig.load(config_dir)

def test_write_config(config):
    """Test that configurations can be written."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        config.write(temp_dir)

        assert all(
            [
                (temp_dir / field.name).with_suffix(".nml").exists()
                for field in dataclasses.fields(config)
            ]
        )

def test_round_trip(config):
    """Test that configurations round-trip correctly."""

    with tempfile.TemporaryDirectory() as temp_dir:
        config.write(temp_dir)

        reloaded_config = JulesConfig.load(temp_dir)

    assert config == reloaded_config


