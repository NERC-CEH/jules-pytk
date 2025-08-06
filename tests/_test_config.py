import dataclasses
import logging
from pathlib import Path
import pytest
import random
import tempfile

from jules_pytk.config import JulesConfig

logger = logging.getLogger(__name__)


def test_config_load(experiment_dir, namelists_subdir):
    """Test that configurations can be read."""
    _ = JulesConfig.read(experiment_dir, namelists_subdir=namelists_subdir)


def test_config_write(jules_config):
    """Test that configurations can be written."""
    with tempfile.TemporaryDirectory() as temp_dir:
        jules_config.write(temp_dir)


def test_config_round_trip(jules_config):
    """Test that configurations round-trip correctly."""

    with tempfile.TemporaryDirectory() as temp_dir:
        jules_config.write(temp_dir)
        reloaded_jules_config = JulesConfig.read(temp_dir)

    assert reloaded_jules_config == jules_config


def _test_config_write_nodata(jules_config):
    """Test that writing with no data fails gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # TODO: Make this more specific to the particular ValueError
        with pytest.raises(ValueError):
            jules_config.write(temp_dir)
