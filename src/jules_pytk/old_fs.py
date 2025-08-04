from abc import ABC, abstractmethod
from collections.abc import Sequence
import dataclasses
import logging
from os import PathLike
from pathlib import Path
from typing import Any, ClassVar, Self

import numpy
import xarray

from .exceptions import InvalidPath

logger = logging.getLogger(__name__)


class _FilesystemInterface(ABC):
    """ABC for objects acting as interfaces with the filesystem."""

    def __init__(
        self,
        path: str | PathLike,
        *,
        data: Any = None,
        children: list[Self] | None = None,
    ) -> None:
        self._path = Path(path) if path is not None else path

    @property
    def path(self) -> Path | None:
        """Path to a directory associated with this object, or `None` if detached."""
        return self._path

    @property
    def data(self) -> Any:
        """Data contained within file or directory."""
        return self._data

    @property
    def children(self) -> list[Self]:
        return self._children

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def __str__(self) -> str:
        return f"{type(self)}(path={self.path}, contents={type(self.contents)})"

    @classmethod
    def _check_path_for_read(cls, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Provided path {path} does not exist")

    @classmethod
    def read(cls, path: str | PathLike, **kwargs) -> Self:
        """Read data from a location in the filesystem."""
        path = Path(path)

        cls._check_path_for_read(path)

        logger.info(f"Reading from {path}")
        inst = cls._read(path, **kwargs)

        inst._path = path

        return inst

    @classmethod
    @abstractmethod
    def _read(cls, path: Path, **kwargs) -> Self: ...

    @classmethod
    def _check_path_for_write(self, path: Path, overwrite_existing: bool) -> None:
        pass

    def write(
        self, path: str | PathLike, overwrite_existing: bool = False, **kwargs
    ) -> None:
        """Write data to a location in the filesystem."""
        path = Path(path).resolve()

        self._check_path_for_write(path, overwrite_existing)

        logger.info(f"Writing to {path}")
        self._write(path, **kwargs)

    @abstractmethod
    def _write(self, path: Path, **kwargs) -> None: ...

    def update(self, **kwargs) -> None:
        """Update the filesystem (attached objects only).

        This is functionally equivalent to
        `self.write(self.path, **kwargs)`
        """
        if self.is_detached:
            logger.warning("Cannot call 'update()' on a detached object!")
            return

        logger.info(f"Updating {self.path}")
        self._write(self.path, **kwargs)

    def detach(self) -> Self:
        """Returns a detached but otherwise identical instance.

        Here, 'detached' means that the object is not associated with any real
        files living on the disk. I.e. it can be safely modified without
        affecting any files.

        The opposite of detached implies that the object is tracking a real
        file `self.path` or set of files in the directory `self.path`. Any
        changes to the object made using the `update()` method will trigger
        a corresponding update to these files.
        """
        if self.is_detached:
            logger.warning(
                "Calling `detach()` on an object that is already detached. Was this intentional?"
            )
        return self._detach()

    @abstractmethod
    def _detach(self) -> Self: ...


class File(_FilesystemInterface):
    valid_extensions: ClassVar[list[str]]

    @classmethod
    def _check_path_for_read(cls, path: Path) -> None:
        super()._check_path_for_read(path)
        if path.suffix not in cls.valid_extensions:
            raise InvalidPath(
                f"Path must have a file extension that is one of: {cls.valid_extensions}"
            )

    def _check_path_for_write(self, path: Path, overwrite_existing: bool) -> None:
        super()._check_path_for_write(path, overwrite_existing)
        if path.suffix not in self.valid_extensions:
            raise InvalidPath(
                f"Path must have a file extension that is one of: {self.valid_extensions}"
            )
        if path.exists() and not overwrite_existing:
            raise FileExistsError(f"There is already a file at {path}")
        if not path.parent.exists():
            logger.info(f"Creating parent directory at {path.parent}")
            path.parent.mkdir(parents=True)


class Directory(_FilesystemInterface):
    def _check_path_for_write(self, path: Path, overwrite_existing: bool) -> None:
        super()._check_path_for_write(path, overwrite_existing)
        if path.is_dir() and (len(list(path.iterdir())) > 0) and not overwrite_existing:
            raise FileExistsError(f"There is already a non-empty directory at {path}")
        if not path.exists():
            logger.info(f"Creating directory at {path}")
            path.mkdir(parents=True)


class AsciiFile(File):
    valid_extensions: ClassVar[list[str]] = [".asc", ".dat", ".txt"]

    def __init__(self, data: numpy.ndarray, comment: str = "") -> None:
        assert data is not None
        data = numpy.asarray(data)

        if data.ndim == 1:
            data = data.reshape(1, -1)

        self.data = data
        self.comment = comment

    def __eq__(self, other: Any) -> bool:
        return (
            (type(other) is type(self))
            and (type(other.data) is type(self.data))
            and numpy.allclose(self.data, other.data, atol=1e-4)
        )

    def __str__(self) -> str:
        return f"""
    {type(self)}
    # {self.comment}
    Array, shape {self.data.shape}
    """

    @property
    def data(self) -> numpy.ndarray:
        return self._data

    @data.setter
    def data(self, new: list[float] | numpy.ndarray) -> None:
        new = numpy.asarray(new)
        if self.data is None and new.shape != self.data.shape:
            logger.warning(
                f"Data has changed shape! (new) {new.shape} =/= {self.data.shape} (old)"
            )

        self._data = new

    @property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, new: str) -> None:
        self._comment = new

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

    def _write(self, path: Path) -> None:
        numpy.savetxt(
            str(path),
            self.data,
            fmt="%.5f",
            header=self.comment,
            comments="#",
        )

    def _detach(self) -> Self:
        return type(self)(data=self.data, comment=self.comment)


class NetcdfFile(File):
    valid_extensions: ClassVar[list[str]] = [".nc", ".cdf"]

    def __init__(self, data: xarray.Dataset) -> None:
        self.data = data

    def __eq__(self, other: Any) -> bool:
        # NOTE: consider allclose; these are float arrays
        return (
            (type(other) is type(self))
            and (type(other.data) is type(self.data))
            and self.data.identical(other.data)
        )

    @property
    def data(self) -> numpy.ndarray:
        return self._data

    @data.setter
    def data(self, new: xarray.Dataset) -> None:
        if not isinstance(new, xarray.Dataset):
            raise TypeError(f"Expected xarray.dataset, but got {type(new)}")
        self._data = new

    @classmethod
    def _read(cls, path: Path) -> Self:
        logger.warning("Loading full dataset from {path}")
        data = xarray.load_dataset(path)

        return cls(data=data)

    def _write(self, path: Path) -> None:
        self.data.to_netcdf(path)

    def _detach(self) -> Self:
        # NOTE: is probably useless since self.data is the same object as inst.data
        inst = type(self)(data=self.data)

        # TODO: in future, only load entire dataset into memory upon detach

        # logger.warning("Loading full dataset from {self.path}")
        # inst.data.load()

        return inst


def NamelistFile(File):
    def __init__(self, data: f90nml.Namelist) -> None:
        self.data = data

    @property
    def data(self) -> f90nml.Namelist:
        return self._data

    @data.setter
    def data(self, new: f90nml.Namelist) -> None:
        # TODO: some validation
        assert isinstance(new, f90nml.Namelist)
        self._data = new

    @classmethod
    def _read(cls, path: Path) -> Self:
        data = f90nml.read(path)
        return cls(data=data)

    def _write(self, path: Path) -> None:
        self.data.write(path, force=True)

    def _detach(self) -> Self:
        return type(self)(data=self.data)


def JulesIOFile(
    file_ext: str,
) -> type[AsciiFile] | type[NetcdfFile] | type[NamelistFile]:
    """Representation of a file input/output to JULES."""
    match file_ext:
        case ".asc" | ".txt" | ".dat":
            return AsciiFile
        case ".nc" | ".cdf":
            return NetcdfFile
        case ".nml":
            return NamelistFile
        case _:
            raise ValueError(f"Invalid file extension: {file_ext}")


@dataclasses.dataclass(kw_only=True)
class NamelistsDirectory(Directory):
    ancillaries: NamelistFile
    crop_params: NamelistFile
    drive: NamelistFile
    fire: NamelistFile
    imogen: NamelistFile
    initial_conditions: NamelistFile
    jules_deposition: NamelistFile
    jules_hydrology: NamelistFile
    jules_irrig: NamelistFile
    jules_prnt_control: NamelistFile
    jules_radiation: NamelistFile
    jules_rivers: NamelistFile
    jules_snow: NamelistFile
    jules_soil_biogeochem: NamelistFile
    jules_soil: NamelistFile
    jules_surface: NamelistFile
    jules_surface_types: NamelistFile
    jules_vegetation: NamelistFile
    jules_water_resources: NamelistFile
    model_environment: NamelistFile
    model_grid: NamelistFile
    nveg_params: NamelistFile
    output: NamelistFile
    pft_params: NamelistFile
    prescribed_data: NamelistFile
    science_fixes: NamelistFile
    timesteps: NamelistFile
    triffid_params: NamelistFile
    urban: NamelistFile

    @classmethod
    def _read(cls, path: Path) -> Self:
        namelists = [field.name for field in dataclasses.fields(cls)]

        namelist_files = {
            namelist: NamelistFile.read((path / namelist).with_suffix(".nml"))
            for namelist in namelists
        }

        return cls(**namelist_files)

    def _write(self, path: Path) -> None:
        namelists = [field.name for field in dataclasses.fields(self)]

        for namelist in namelists:
            file_path = (path / namelist).with_suffix(".nml")
            getattr(self, namelist).write(file_path)

    def _detach(self) -> Self:
        namelists = [field.name for field in dataclasses.fields(self)]

        detached_files = {getattr(self, namelist).detach() for namelist in namelists}

        return type(self)(**detached_files)

    def __getitem__(
        self, key: str | tuple[str] | tuple[str, str] | tuple[str, str, str]
    ):
        """Access the namelists/groups/parameters with 1-/2-/3-tuple keys."""
        if isinstance(key, str):
            key = (key,)

        match len(key):
            case 1:
                return getattr(self, key[0]).data
            case 2:
                return getattr(self, key[0]).data.get(key[1])
            case 3:
                return getattr(self, key[0]).data.get(key[1]).get(key[2])
            case _:
                raise ValueError(
                    f"`key` must have 1, 2, or 3 elements (got {len(key)})."
                )

    def parameters(self) -> Generator[tuple[tuple[str, str, str], Any], None, None]:
        """Iterates over all parameters, labelled by 3-tuples.

        Yields:
            A 2-tuple containing (i) a 3-tuple (namelist, group, parameter)
            which labels the parameter, and (ii) the value of the parameter itself.
        """
        namelists = [field.name for field in dataclasses.fields(self)]

        for namelist in namelists:
            for (group, param), value in getattr(self, namelist).groups():
                yield (namelist, group, param), value

    def file_parameters(
        self,
    ) -> Generator[tuple[tuple[str, str, str], str], None, None]:
        """A subset of parameters that point to input files."""
        valid_extensions = (".nc", ".cdf", ".asc", ".txt", ".dat")
        yield from filter(
            lambda label_value: (
                isinstance(label_value[1], str)
                and label_value[1].endswith(valid_extensions)
            ),
            self.parameters(),
        )

    def input_files(self, rel_only: bool = False) -> list[Path]:
        """List of all unique file paths present in the namelists."""
        unique_files = set([Path(path) for _, path in self.file_parameters()])

        if rel_only:
            return [path for path in unique_files if not path.is_absolute()]
        else:
            return list(unique_files)

        rel, abs = [], []
        for path in unique_files:
            (abs if path.is_absolute() else rel).append(path)

        return rel, abs

    def to_dict(self) -> dict:
        """Return a dict representation of the entire set of namelists."""
        namelists = [field.name for field in dataclasses.fields(self)]

        return {
            namelist: getattr(self, namelist).data.todict() for namelist in namelists
        }


class ExperimentDirectory(Directory):
    def __init__(
        self,
        namelists: NamelistsDirectory,
        inputs: FrozenDict[str, AsciiFile | NetcdfFile],
        namelists_subdir: str | None = None,
    ):
        # TODO: check that all required files are present
        pass

    @property
    def namelists_subdir(self) -> str:
        return self._namelists_subdir

    @classmethod
    def _read(cls, path: Path, namelists_subdir: str | None = None) -> Self:
        if namelists_subdir is None:
            namelists_subdir = find_namelists(path)

        namelists = NamelistsDirectory.read(path / namelists_subdir)

        # Attempt to read all input files with relative paths
        inputs = FrozenDict(
            {
                str(input_file): JulesIOFile(input_file.suffix).read(path / input_file)
                for input_file in namelists.input_files(rel_only=True)
            }
        )

        return cls(
            namelists=namelists, inputs=inputs, namelists_subdir=namelists_subdir
        )

    def _write(self, path: Path) -> None: ...

    def _detach(self) -> Self:
        ...
        detached_experiment.namelists_subdir = x
