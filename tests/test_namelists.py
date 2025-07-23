import dataclasses
import logging
from pathlib import Path
import random
import tempfile

from jules_pytk.config import JulesNamelists

logger = logging.getLogger(__name__)


def test_read(namelists_dir):
    """Test that namelists can be loaded."""
    _ = JulesNamelists.read(namelists_dir)


def test_write(jules_namelists):
    """Test that JulesNamelists writes all namelists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        _ = jules_namelists.write(temp_dir)

        names = [field.name for field in dataclasses.fields(jules_namelists)]

        assert all([(temp_dir / name).with_suffix(".nml").exists() for name in names])


def test_round_trip(jules_namelists):
    """Test that JulesNamelists round-trips correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        _ = jules_namelists.write(temp_dir)

        reloaded_jules_namelists = JulesNamelists.read(temp_dir)

    assert reloaded_jules_namelists == jules_namelists


def test_parameters(jules_namelists):
    for (namelist, group, param), value in jules_namelists.parameters():
        pass


def test_file_parameters(jules_namelists):
    for (namelist, group, param), value in jules_namelists.file_parameters():
        pass


def test_getitem(jules_namelists):
    a = random.choice([field.name for field in dataclasses.fields(jules_namelists)])

    namelist = jules_namelists[a]

    b = random.choice(list(namelist.keys()))

    group = jules_namelists[(a, b)]

    try:
        c = random.choice(list(group.keys()))
    except IndexError:
        logger.info("Empty namelist: skipping test of (a, b, c) access")
    else:
        _ = jules_namelists[(a, b, c)]

    # TODO: test for sensible output when invalid a, b, c, or too many


# TODO: test that patching causes correct update of namelists in memory
