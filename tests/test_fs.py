from pathlib import Path
import tempfile

from dcdir import Handler
import numpy
import pytest

from jules_pytk.fs import AsciiFileHandler, NetcdfFileHandler, NamelistFileHandler, NamelistsDirectory

@pytest.mark.parametrize("handler", [AsciiFileHandler, NetcdfFileHandler, NamelistFileHandler, NamelistsDirectory])
def test_handler_satisfies_protocol(handler):
    assert isinstance(handler(), Handler)

# NOTE: this does not seem to work with fixtures..
#@pytest.mark.parametrize("path,handler", [(ascii_file, AsciiFileHandler), (netcdf_file, NetcdfFileHandler), (namelist_file, NamelistFileHandler), (namelists_dir, NamelistsDirectory)])
def _test_handler_read(path, handler):
    _ = handler().read(path)


def test_read_ascii(ascii_file):
    handler = AsciiFileHandler()
    _ = handler.read(ascii_file)

def test_read_netcdf(netcdf_file):
    handler = NetcdfFileHandler()
    _ = handler.read(netcdf_file)

def test_read_namelist(namelist_file):
    handler = NamelistFileHandler()
    _ = handler.read(namelist_file)

def test_read_namelists_dir(namelists_dir):
    handler = NamelistsDirectory()
    _ = handler.read(namelists_dir)


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
