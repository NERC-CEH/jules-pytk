from pathlib import Path
import tempfile

from dirconf import Handler
import numpy
import pytest

from jules_pytk.config import *


@pytest.mark.parametrize(
    "handler",
    [
        AsciiFileHandler,
        NetcdfFileHandler,
        NamelistFileHandler,
        NamelistsDirectoryConfig,
    ],
)
def test_handler_satisfies_protocol(handler):
    assert isinstance(handler(), Handler)


# NOTE: this does not seem to work with fixtures..
# @pytest.mark.parametrize("path,handler", [(ascii_file, AsciiFileHandler), (netcdf_file, NetcdfFileHandler), (namelist_file, NamelistFileHandler), (namelists_dir, NamelistsDirectory)])


def _test_handler_io(inpath, handler):
    config = handler().read(inpath)

    # tmp = Path.cwd() / "tmp"
    # tmp.mkdir(exist_ok=True)
    # if True:
    with tempfile.TemporaryDirectory() as tmp:
        outpath = Path(tmp) / inpath.name
        handler().write(outpath, config)
        config_roundtrip = handler().read(outpath)

    # assert config == config_roundtrip


def test_ascii_file_io(ascii_file):
    _test_handler_io(ascii_file, AsciiFileHandler)


def test_netcdf_file_io(netcdf_file):
    _test_handler_io(netcdf_file, NetcdfFileHandler)


def test_namelist_file_io(namelist_file):
    _test_handler_io(namelist_file, NamelistFileHandler)


def test_namelists_dir_io(namelists_dir):
    _test_handler_io(namelists_dir, NamelistsDirectoryConfig)


def test_inputs_dir_io(inputs_dir):
    handler_ = lambda: InputsDirectoryConfig(
        initial_conditions="initial_conditions_bb219.dat",
        driving_data="Loobos_1997.dat",
        tile_fractions="tile_fractions.dat",
    )
    _test_handler_io(inputs_dir, handler_)


def test_jules_dir_io(jules_dir):
    handler_ = lambda: JulesDirectoryConfig(
        namelists="namelists",
        inputs={
            "path": "inputs",
            "handler": lambda: InputsDirectoryConfig(
                initial_conditions="initial_conditions_bb219.dat",
                driving_data="Loobos_1997.dat",
                tile_fractions="tile_fractions.dat",
            ),
        },
    )
    _test_handler_io(jules_dir, handler_)


# NOTE: changed back to AsciiFileHandler reads abs paths but does not write them...
# @pytest.mark.xfail(reason="By design, AsciiFileHandler returns MISSING instead of reading from absolute paths.")
@pytest.mark.parametrize("suffix", [".txt", ".dat"])
def test_read_ascii_old(suffix):
    comment = ["# This is a comment.", "# This is a second line."]
    values = ["1 2 3 4 5" for _ in range(10)]
    file_contents = "\n".join(comment + values)

    handler = AsciiFileHandler()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete_on_close=False) as tmp:
        with open(tmp.name, "w") as file:
            file.write(file_contents)

        data = handler.read(tmp.name)

    assert isinstance(data, dict)

    values_ = data["values"]
    comment_ = data["comment"].split("\n")

    assert isinstance(values_, numpy.ndarray)
    assert len(values_) == len(values)

    assert all([line_ == line for line_, line in zip(comment_, comment, strict=True)])
