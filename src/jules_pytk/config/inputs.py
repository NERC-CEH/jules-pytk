from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, ClassVar, Self

import numpy
import xarray

from jules_pytk.exceptions import InvalidPath
from .base import ConfigBase

logger = logging.getLogger(__name__)

__all__ = ["JulesInput", "JulesInputAscii", "JulesInputNetcdf"]


@dataclass(kw_only=True)
class JulesInputAscii(ConfigBase):
    data: numpy.ndarray
    comment: str = ""

    valid_extensions: ClassVar[list[str]] = [".asc", ".dat", ".txt"]

    def __post_init__(self) -> None:
        assert self.data is not None
        self.data = numpy.asarray(self.data)

        if self.data.ndim == 1:
            self.data = self.data.reshape(1, -1)

    def __eq__(self, other: Any) -> bool:
        return (
            (type(other) is type(self))
            and (type(other.data) is type(self.data))
            and numpy.allclose(self.data, other.data, atol=1e-4)
        )

    @classmethod
    def _read(cls, path: Path) -> Self:
        # Check if there is a single-line comment
        # TODO: extend to multi-line
        with path.open("r") as file:
            first_line = file.readline().strip()
            if first_line[0] in ("#", "!"):  # Treated as comments by JULES
                comment = first_line[1:]
            else:
                comment = ""

        data = numpy.loadtxt(str(path), comments=("#", "!"))
        data = data.squeeze()

        return cls(data=data, comment=comment)

    def _write(self, path: Path, overwrite: bool) -> None:
        if path.suffix not in self.valid_extensions:
            raise InvalidPath(
                f"Path must have a file extension that is one of: {self.valid_extensions}"
            )
        if not path.parent.exists():
            raise FileNotFoundError(f"Parent directory '{path.parent}' does not exist.")
        numpy.savetxt(
            str(path),
            self.data,
            fmt="%.5f",
            header=self.comment,
            comments="#",
        )

    def _update(self, new_values: list[float] | numpy.ndarray) -> None:
        new_data = numpy.asarray(new_values)
        if new_data.shape != self.data.shape:
            logger.warning("Data has changed shape.")

        self.data = new_data

    def _detach(self) -> Self:
        return type(self)(data=self.data, comment=self.comment)


@dataclass(kw_only=True)
class JulesInputNetcdf(ConfigBase):
    data: xarray.Dataset

    def __eq__(self, other: Any) -> bool:
        # NOTE: consider allclose; these are float arrays
        return (
            (type(other) is type(self))
            and (type(other.data) is type(self.data))
            and self.data.identical(other.data)
        )

    @classmethod
    def _read(cls, path: Path) -> Self:

        with path.open("r") as file:
            # open_dataset opens the file for lazy loading
            with xarray.open_dataset(file) as data:
                # Load full dataset into memory (could also use load_dataset)
                logger.warning("Loading full dataset from {self.path}")
                data.load()

        return cls(data=data)

    def _write(self, path: Path, overwrite: bool) -> None:
        self.data.to_netcdf(path)

    def _update(self, new_values: xarray.Dataset) -> None:
        assert isinstance(new_values, xarray.Dataset)
        self.data = self.new_values

    def _detach(self) -> Self:
        # NOTE: is probably useless since self.data is the same object as inst.data
        inst = type(self)(data=self.data)

        # TODO: in future, only load entire dataset into memory upon detach
        
        #logger.warning("Loading full dataset from {self.path}")
        #inst.data.load()
        
        return inst


def JulesInput(file_ext: str) -> type[JulesInputAscii] | type[JulesInputNetcdf]:
    """Representation of a file input to JULES."""
    match file_ext:
        case ".asc" | ".txt" | ".dat":
            return JulesInputAscii
        case ".nc" | ".cdf":
            return JulesInputNetcdf
        case _:
            raise ValueError(f"Invalid file extension: {file_ext}")
