import dataclasses
import logging
from pathlib import Path
import random
import tempfile

from jules_pytk.config import JulesConfig, JulesConfigMeta, JulesNamelists

logger = logging.getLogger(__name__)


def test_meta_load(config_dir):
    """Test that meta json can be read."""
    _ = JulesConfigMeta.load(config_dir)

def test_meta_dump(jules_config_meta):
    """Test that JulesConfigMeta dumps meta json."""
    with tempfile.TemporaryDirectory() as temp_dir:
        jules_config_meta.dump(temp_dir)
        assert (Path(temp_dir) / jules_config_meta.meta_file).exists()

def test_meta_round_trip(jules_config_meta):
    """Test that JulesConfigMeta round-trips."""
    with tempfile.TemporaryDirectory() as temp_dir:
        jules_config_meta.dump(temp_dir)
    
        reloaded_jules_config_meta = JulesConfigMeta.load(temp_dir)

    assert reloaded_jules_config_meta == jules_config_meta

def test_namelists_load(namelists_dir):
    """Test that namelists can be loaded."""
    _ = JulesNamelists.load(namelists_dir)

def test_namelists_dump(jules_namelists):
    """Test that JulesNamelists dumps all namelists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        jules_namelists.dump(temp_dir)

        names = [field.name for field in dataclasses.fields(jules_namelists)]

        assert all(
            [
                (temp_dir / name).with_suffix(".nml").exists()
                for name in names
            ]
        )

def test_namelists_round_trip(jules_namelists):
    """Test that JulesNamelists round-trips correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        jules_namelists.dump(temp_dir)

        reloaded_jules_namelists = JulesNamelists.load(temp_dir)

    assert reloaded_jules_namelists == jules_namelists


def test_config_load(config_dir):
    """Test that configurations can be read."""
    _ = JulesConfig.load(config_dir)

def test_config_dump(jules_config):
    """Test that configurations can be written."""
    with tempfile.TemporaryDirectory() as temp_dir:
        jules_config.dump(temp_dir)

def test_config_round_trip(jules_config):
    """Test that configurations round-trip correctly."""

    with tempfile.TemporaryDirectory() as temp_dir:
        jules_config.dump(temp_dir)
        reloaded_jules_config = JulesConfig.load(temp_dir)

    assert reloaded_jules_config == jules_config


def test_namelist_getitem(jules_namelists):
    a = random.choice([field.name for field in dataclasses.fields(jules_namelists)])

    namelist = jules_namelists[a]

    b = random.choice(list(namelist.keys()))

    group = jules_namelists[(a, b)]

    try:
        c = random.choice(list(group.keys()))
    except IndexError:
        logger.info("Empty namelist: skipping test of (a, b, c) access")
    else:
        param = jules_namelists[(a, b, c)]

    # TODO: test for sensible output when invalid a, b, c, or too many


