import copy
from dataclasses import asdict, dataclass, field, fields
import json
import logging
from os import PathLike
from pathlib import Path
from typing import Any, ClassVar, final, Generator, NamedTuple, Self

import f90nml

from .io import read_ascii, write_ascii, read_netcdf, write_netcdf
from .utils import switch_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class JulesConfigMeta:
    """Dataclass containing metadata about a JULES configuration."""

    namelists_dir: Path
    desc: str = ""

    meta_file: ClassVar[str] = "meta.json"

    def __post_init__(self):
        namelists_dir = Path(self.namelists_dir)
        assert not namelists_dir.is_absolute()
        assert namelists_dir.resolve().is_relative_to(Path.cwd())

    @classmethod
    def load(cls, config_dir: str | PathLike) -> Self:
        config_dir = Path(config_dir).resolve()

        with (config_dir / cls.meta_file).open("r") as file:
            meta_dict = json.load(file)

        return cls(**meta_dict)

    def dump(self, config_dir: str | PathLike) -> None:
        config_dir = Path(config_dir).resolve()

        # TODO: check (de-)serialisation of pathlib.Path
        with (config_dir / self.meta_file).open("w") as file:
            json.dump(asdict(self), file)


@final
@dataclass(kw_only=True)
class JulesNamelists:
    """Dataclass containing JULES namelists."""

    ancillaries: f90nml.Namelist
    crop_params: f90nml.Namelist
    drive: f90nml.Namelist
    fire: f90nml.Namelist
    imogen: f90nml.Namelist
    initial_conditions: f90nml.Namelist
    jules_deposition: f90nml.Namelist
    jules_hydrology: f90nml.Namelist
    jules_irrig: f90nml.Namelist
    jules_prnt_control: f90nml.Namelist
    jules_radiation: f90nml.Namelist
    jules_rivers: f90nml.Namelist
    jules_snow: f90nml.Namelist
    jules_soil_biogeochem: f90nml.Namelist
    jules_soil: f90nml.Namelist
    jules_surface: f90nml.Namelist
    jules_surface_types: f90nml.Namelist
    jules_vegetation: f90nml.Namelist
    jules_water_resources: f90nml.Namelist
    model_environment: f90nml.Namelist
    model_grid: f90nml.Namelist
    nveg_params: f90nml.Namelist
    output: f90nml.Namelist
    pft_params: f90nml.Namelist
    prescribed_data: f90nml.Namelist
    science_fixes: f90nml.Namelist
    timesteps: f90nml.Namelist
    triffid_params: f90nml.Namelist
    urban: f90nml.Namelist

    def __post_init__(self) -> None:
        # Strongly discourage subclasses that introduce additional non-namelist
        # fields, along with @final decorator
        assert all([field.type == f90nml.Namelist for field in fields(self)])

        # Assert that all relative paths are to subdirectories, i.e. aren't
        # given by e.g. "../../file.nc"
        for path in self.file_paths(absolute=False):
            assert path.resolve().is_relative_to(Path.cwd())

    @classmethod
    def load(cls, namelists_dir: str | PathLike) -> Self:
        """Loads a JulesNamelists object from a directory containing namelist files."""

        namelists_dir = Path(namelists_dir).resolve()

        names = [field.name for field in fields(cls)]

        namelists_dict = {
            name: f90nml.read((namelists_dir / name).with_suffix(".nml"))
            for name in names
        }

        return cls(**namelists_dict)

    def dump(self, namelists_dir: str | PathLike) -> None:
        """Writes namelist files to a directory."""

        namelists_dir = Path(namelists_dir).resolve()

        names = [field.name for field in fields(self)]

        for name in names:
            file_path = (namelists_dir / name).with_suffix(".nml")
            getattr(self, name).write(file_path)

    def __getitem__(
        self, key: str | tuple[str] | tuple[str, str] | tuple[str, str, str]
    ) -> f90nml.Namelist | Any:
        if isinstance(key, str):
            key = (key,)
        if len(key) == 1:
            return getattr(self, key[0])
        elif len(key) == 2:
            return getattr(self, key[0]).get(key[1])
        elif len(key) == 3:
            return getattr(self, key[0]).get(key[1]).get(key[2])

    @property
    def parameters(self) -> dict[tuple[str, str, str], Any]:
        """Return a flattened dict containing all parameters."""
        result = {}
        for field in fields(self):
            namelist = getattr(self, field.name)
            for (group, param), value in namelist.groups():
                result[(field.name, group, param)] = value
        return result

    @property
    def files(self) -> dict[tuple[str, str, str], str]:
        """Return a subset of `parameters` that point to input files."""
        valid_extensions = [".nc", ".cdf", ".asc", ".txt", ".dat"]
        return {
            key: value
            for key, value in self.parameters.items()
            if isinstance(value, string) and value.endswith(valid_extensions)
        }

    def file_paths(self, relative: bool = True, absolute: bool = True) -> list[Path]:
        paths = [Path(path).expanduser() for path in set(self.files.values())]

        if relative and absolute:
            return paths
        elif absolute and not relative:
            return [path for path in paths if path.is_absolute()]
        elif relative and not absolute:
            return [path for path in paths if not path.is_absolute()]
        else:
            raise ValueError("`relative` and `absolute` cannot both be False")


class JulesInput:
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

    @property
    def path(self) -> Path:
        return self._path

    @property
    def data(self) -> np.ndarray:
        return self._data

    @data.setter
    def data(self, new_data) -> None:
        # TODO: some validation?
        if self._data is None:
            self._data = new_data
        else:
            # TODO: clarify with custom exc
            raise Exception("data is already set. Create a new instance.")

    def validate(self, namelists: JulesNamelists) -> bool:
        # TODO: should this be called in data setter?
        return NotImplemented

    def load(self, file_path: str | PathLike = None) -> None:
        # TODO: warn if provided file path does not match self.file_path
        # TODO: handle absolute
        # TODO: warn/error if data is set?
        self.data = self._loader(file_path)

    def dump(self, file_path: str | PathLike) -> None:
        self._dump(self._data, file_path)


class JulesConfig:

    def __init__(self, namelists: JulesNamelists):
        self._namelists = namelists
        self._inputs = [JulesInput(path) for path in namelists.file_paths]

    @property
    def namelists(self) -> JulesNamelists:
        return self._namelists

    @property
    def inputs(self) -> list[JulesInputs]:
        return self._inputs

    def load_input_files(self, working_dir: str | PathLike) -> None:
        # for each relative path
        ...

    @classmethod
    def load(cls, exec_dir: str | PathLike, nml_subdir: str | PathLike = ".") -> Self:

        exec_dir = Path(exec_dir).resolve()

        namelists = JulesNamelists.load(exec_dir / nml_subdir)

        return cls(namelists=namelists)

    def dump(self, exec_dir: str | PathLike, nml_subdir: str | PathLike = ".") -> None:
        exec_dir = Path(exec_dir).resolve()
        if exec_dir.exists():
            # TODO: allow existing config_dir, but do not allow overriding
            # meta.json or namelists_dir
            raise FileExistsError

        namelists_dir = exec_dir / nml_subdir
        namelists_dir.mkdir(parents=True, exist_ok=True)
        self.namelists.dump(namelists_dir)

        for input in self.inputs:
            if not input.path.is_absolute():
                input_path = exec_dir / input.path
                input_path.mkdir(parents=True, exist_ok=True)
                input.dump(input_dir)

    def validate(self) -> bool:
        # TODO: check that all files are accounted for etc
        ...


# type JulesConfigGenerator = Generator[JulesConfig, None, None]


def make_paths_absolute(files: list[str | PathLike], pattern: str) -> None:
    for file in files:
        if fnmatch(file, pattern):
            pass
            # patch & logging.info
            # Requires self.meta.namelists_dir


def _make_paths_absolute(
    namelists: JulesNamelists,
    include: list[str | PathLike] | None = None,
    exclude: list[str | PathLike] | None = None,
) -> JulesConfig:

    assert not (include and exclude), "Use either `include` or `exclude`, but not both"

    config_dict = asdict(copy.deepcopy(config))

    # TODO: exclude could instead be a glob pattern?
    if exclude is not None:
        resolved_exclude = [Path(path).resolve() for path in exclude]
        for path_str, resolved_path in zip(exclude, resolved_exclude):
            if not resolved_path.exists():
                raise FileNotFoundError(
                    "The path '%s' (provided to `exclude` as '%s') does not exist"
                    % (resolved_path, path_str)
                )
        exclude = resolved_exclude

    # These keys contain 'file' but are never path-valued
    known_irrelevant_keys = ["use_file", "nfiles", "file_period"]

    for key, namelist in config_dict.items():

        patches = {}

        for (group, param), value in namelist.groups():

            # Skip any parameters that do not include the string 'file'
            if "file" not in param:
                # NOTE: This skips parameters that include 'dir', which we may not want!
                continue

            # Skip those parameters which include 'profile'
            if ("profile" in param) or (param in known_irrelevant_keys):
                continue

            # Skip parameters that are not path-valued
            try:
                value_as_path = Path(value)
            except TypeError:
                logger.info(
                    "Skipping parameter %s.nml>%s::%s since value %s is not path-valued"
                    % (key, group, param, value)
                )
                continue

            # Skip parameters which may look path-valued, but the path does not exist
            if not value_as_path.exists():
                logger.info(
                    "Skipping parameter %s.nml>%s::%s since value %s is not an existing path"
                    % (key, group, param, value)
                )
                continue

            # For the remaining parameters that are existing paths, resolve the path
            value_as_abs_path = value_as_path.resolve()

            # Skip the parameter if its value is in exclude
            if exclude:
                if any([value_as_abs_path == skip_path for skip_path in exclude]):
                    logger.info(
                        "Skipping parameter %s.nml>%s::%s since value %s is in `exclude`"
                        % (key, group, param, value)
                    )
                    continue

            # If the parameter reaches this point, update the value with the abs path
            logger.info(
                "Updating %s.nml>%s::%s to an absolute path: %s -> %s"
                % (key, group, param, value, value_as_abs_path)
            )

            # Add stringified version to the patches dict for this namelist
            patches[group] = {param: str(value_as_abs_path)}

        namelist.patch(patches)

    return JulesConfig(**config_dict)


def make_paths_absolute(
    config: JulesConfig,
    working_dir: str | PathLike,  # perhaps call this data_dir?
    exclude: list[str | PathLike] | None = None,
) -> JulesConfig:
    """Converts relative paths to absolute paths in a JulesConfig object.

    Parameters
    ----------
    config:
        A `JulesConfig` object containing relative paths.
    working_dir:
        The directory with respect to which the relative paths are defined.
    exclude:
        An optional list of paths to skip, i.e. leave as relative.

    Returns
    -------
    A _deep copy_ of the `JulesConfig` object with absolute paths.

    Examples
    --------
    >>> from jules_pytk.config import read_config, make_paths_absolute
    >>> config = read_config('examples/loobos')
    >>> config.get_value_from_tuple('ancillaries', 'jules_frac', 'file')
    'inputs/tile_fractions.dat'
    >>> modified_config = make_paths_absolute(config, 'examples/loobos')
    >>> modified_config.get_value_from_tuple('ancillaries', 'jules_frac', 'file')
    '/home/joe/github.com/NERC-CEH/jules-utils/examples/loobos/inputs/tile_fractions.dat'
    """

    with switch_dir(working_dir, verbose=True):
        modified_config = _make_paths_absolute(config, exclude)

    return modified_config
