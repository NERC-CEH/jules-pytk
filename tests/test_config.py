import dataclasses
import logging
from pathlib import Path
import random
import tempfile

from jules_pytk.config.config import JulesConfig

logger = logging.getLogger(__name__)


def test_config_load(config_dir):
    """Test that configurations can be read."""
    _ = JulesConfig.load(config_dir, nml_subdir="namelists")

def test_config_dump(jules_config):
    """Test that configurations can be written."""
    with tempfile.TemporaryDirectory() as temp_dir:
        jules_config.dump(temp_dir, nml_subdir="namelists")

def test_config_round_trip(jules_config):
    """Test that configurations round-trip correctly."""

    with tempfile.TemporaryDirectory() as temp_dir:
        jules_config.dump(temp_dir, nml_subdir="namelists")
        reloaded_jules_config = JulesConfig.load(temp_dir, nml_subdir="namelists")

    assert reloaded_jules_config == jules_config
