from os import PathLike
from pathlib import Path
from typing import Any

import numpy
import xarray

from jules_pytk.config.namelists import JulesNamelists

__all__ = [
    "read_ascii",
    "write_ascii",
    "read_netcdf",
    "write_netcdf",
    "JulesInput",
]


def read_ascii(path: str | PathLike) -> numpy.ndarray:
    with open(path, "r") as file:

        # TODO: comment not being used
        first_line = file.readline().strip()
        if first_line[0] in ("#", "!"):  # Treated as comments by JULES
            comment = first_line
        else:
            comment = ""

    data = numpy.loadtxt(path, comments=("#", "!"))

    return data


def write_ascii(data: numpy.ndarray, path: str | PathLike, comment="") -> None:
    numpy.savetxt(path, data, header=comment)


def read_netcdf(path: str | PathLike, lazy: bool = True) -> xarray.Dataset:
    # NOTE: loads entire dataset into memory. Bad idea for big files
    # TODO: lazy
    return xarray.load_dataset(path)


def write_netcdf(data: xarray.Dataset, path: str | PathLike) -> None:
    data.to_netcdf(path)


class JulesInput:
    """Representation of a file input to JULES."""

    def __init__(self, path_in_namelist: str | PathLike) -> None:
        path_in_namelist = Path(path_in_namelist)

        match Path(path_in_namelist).suffix:
            case ".nc" | ".cdf":
                self._loader = read_netcdf
                self._dumper = write_netcdf
            case ".asc" | ".txt" | ".dat":
                self._loader = read_ascii
                self._dumper = write_ascii
            case _:
                raise ValueError(f"Invalid suffix: {path_in_namelist.suffix}")

        self._path = path_in_namelist
        self._data = None

    def __eq__(self, other: Any) -> bool:
        if type(other) != type(self):
            return False
        if self.path != other.path:
            return False
        if self.data is None:
            return other.data is None
        if type(self.data) != type(other.data):
            return False
        if isinstance(self.data, numpy.ndarray):
            # NOTE: consider allclose; these are float arrays
            return numpy.array_equal(self.data, other.data)
        if isinstance(self.data, xarray.Dataset):
            return self.data.identical(other.data)

    @property
    def path(self) -> Path:
        """File path as it appears in namelist, as a pathlib.Path object."""
        return self._path

    @property
    def data(self) -> numpy.ndarray | xarray.Dataset | None:
        """Data to be associated with this file path."""
        return self._data

    @data.setter
    def data(self, new_data) -> None:
        if self.path.is_absolute():  # and self.path.exists() ?
            raise Exception("Cannot set data")
        if self._data is not None:
            # TODO: Do we want this? If so, clarify with custom exc
            raise Exception("data is already set. Create a new instance.")

        # TODO: some validation?

        self._data = new_data

    def validate(self, namelists: JulesNamelists) -> NotImplemented:
        # TODO: should this be called in data setter?
        # NOTE: the idea is to subclass JulesInput and create
        # validators specific to each type of input file, e.g.
        # for driving data etc. This seems like a very big task though.
        return NotImplemented

    def load(self, file_path: str | PathLike) -> None:
        """Populate `self.data` with contents of an existing ascii or netcdf file."""
        # TODO: warn if provided file path does not match self.file_path
        # TODO: handle absolute
        # TODO: warn/error if data is set?
        self.data = self._loader(file_path)

    def dump(self, file_path: str | PathLike) -> None:
        """Write `self.data` to a new file."""
        if self._data is None:
            # TODO: clarify with custom exc
            raise Exception("No data!")

        file_path = Path(file_path)
        file_path.parent.mkdir(exist_ok=True, parents=True)
        self._dumper(self._data, file_path)
