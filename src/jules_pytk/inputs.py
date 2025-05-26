from dataclasses import dataclass, field
import logging
from os import PathLike
from pathlib import Path
from typing import Any, ClassVar

import numpy
import xarray

from jules_pytk.exceptions import InvalidPath

logging.getLogger(__name__)

__all__ = ["JulesInput", "JulesInputAscii", "JulesInputNetcdf"]


@dataclass(kw_only=True)
class _JulesInput:
    _data: Any = field(init=False, repr=False)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self)) and (type(other.data) is type(self.data))


@dataclass(kw_only=True)
class JulesInputAscii(_JulesInput):
    data: numpy.ndarray | None = None
    comment: str = ""

    valid_extensions: ClassVar[list[str]] = [".asc", ".dat", ".txt"]

    @property
    def data(self) -> numpy.ndarray:
        return self._data

    @data.setter
    def data(self, new_data: numpy.ndarray) -> None:
        logging.error(f"{hasattr(self, "_data")} --- {new_data}")
        # Do something different if self.data = None set in constructor...
        # Desperate hack to avoid self.data being initialised as
        # numpy.asarray(None) instead of None
        if not hasattr(self, "_data") and new_data is None:
            self._data = None
            print("SETTING self._data = None !!!")

        else:
            self._data = numpy.asarray(new_data)

    def read_(self, file_path: str | PathLike) -> None:
        logging.info(f"Reading data from {file_path}")

        # TODO: extend to multi-line
        # Check if there is a single-line comment
        with open(file_path, "r") as file:
            first_line = file.readline().strip()
            if first_line[0] in ("#", "!"):  # Treated as comments by JULES
                self.comment = first_line

        self.data = numpy.loadtxt(file_path, comments=("#", "!"))

    def write(self, file_path: str | PathLike) -> None:
        file_path = Path(file_path).resolve()

        if file_path.suffix not in self.valid_extensions:
            raise InvalidPath(
                f"Path must have a file extension that is one of: {self.valid_extensions}"
            )
        if not file_path.parent.exists():
            raise FileNotFoundError(
                f"Parent directory '{file_path.parent}' does not exist."
            )

        logging.info(f"Writing data to {file_path}")
        numpy.savetxt(str(file_path), self.data, header=self.comment)

    def __eq__(self, other: Any) -> bool:
        # NOTE: consider allclose; these are float arrays
        return super().__eq__(other) and numpy.array_equal(self.data, other.data)


@dataclass(kw_only=True)
class JulesInputNetcdf(_JulesInput):
    data: xarray.Dataset | None = None

    @property
    def data(self) -> xarray.Dataset:
        return self._data

    @data.setter
    def data(self, new_data: xarray.Dataset) -> None:
        if not hasattr(self, "_data") and new_data is None:
            self._data = None
        elif not isinstance(new_data, xarray.Dataset):
            raise TypeError(f"Expected xarray.Dataset, but got {type(new_data)}")
        else:
            self._data = new_data

    def read_(self, file_path: str | PathLike) -> None:
        # NOTE: loads entire dataset into memory. Bad idea for big files
        # TODO: lazy
        self.data = xarray.load_dataset(file_path)

    def write(self, file_path: str | PathLike) -> None:
        self.data.to_netcdf(file_path)

    def __eq__(self, other: Any) -> bool:
        # NOTE: consider allclose; these are float arrays
        return super().__eq__(other) and self.data.identical(other.data)


def JulesInput(file_ext: str, data: Any = None) -> JulesInputAscii | JulesInputNetcdf:
    """Representation of a file input to JULES."""
    match file_ext:
        case ".asc" | ".txt" | ".dat":
            return JulesInputAscii(data=data)
        case ".nc" | ".cdf":
            return JulesInputNetcdf(data=data)
        case _:
            raise ValueError(f"Invalid file extension: {file_ext}")


# ---------------------------------------------------------


'''
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
'''
