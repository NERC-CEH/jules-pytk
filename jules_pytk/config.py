import copy
from dataclasses import asdict, dataclass, fields
import logging
from os import PathLike
from pathlib import Path
from typing import Any, Generator, Self

import f90nml

from .utils import switch_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JulesConfig:
    """Dataclass representing a full JULES configuration."""

    ancillaries: f90nml.Namelist
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
    urban: f90nml.Namelist

    @staticmethod
    def load(config_dir: str | PathLike) -> Self:
        """Loads a JulesConfig from a directory containing namelist files."""
        return read_config(config_dir)

    def dump(self, config_dir: str | PathLike) -> None:
        """Writes namelist files to a directory."""
        # TODO: this should probably be write, not dump (dump can be to string)
        write_config(config_dir, self)

    def parameters(self):
        raise NotImplementedError
        # TODO: decide what form of key-value parameter iteration would be useful, if any
        # namelists = [getattr(self, field.name) for field in fields(self)]
        # return itertools.chain.from_iterable(
        #    [namelist.groups() for namelist in namelists]
        # )

    def get_value_from_tuple(self, namelist: str, group: str, param: str) -> Any:
        """Extracts a single value from the configuration."""
        return getattr(self, namelist).get(group).get(param)


type JulesConfigGenerator = Generator[JulesConfig, None, None]


# NOTE: unconvinced by my initial decision to maintain functions for i/o rather than
# attach them to the JulesConfig class


def read_config(config_dir: str | PathLike) -> JulesConfig:
    """Loads a JulesConfig from a directory containing namelist files."""

    config_dir = Path(config_dir).resolve()

    # Read namelists
    namelists = [
        field.name for field in fields(JulesConfig) if field.type is f90nml.Namelist
    ]

    config_dict = {
        namelist: f90nml.read((config_dir / namelist).with_suffix(".nml"))
        for namelist in namelists
    }

    return JulesConfig(**config_dict)


def write_config(config_dir: str | PathLike, config: JulesConfig) -> None:
    """Dumps JulesConfig (i.e. writes namelist files) to a directory."""
    config_dir = Path(config_dir).resolve()

    namelists = [
        field.name for field in fields(JulesConfig) if field.type is f90nml.Namelist
    ]

    for namelist in namelists:
        nml_file = (config_dir / namelist).with_suffix(".nml")
        getattr(config, namelist).write(nml_file)


def _make_paths_absolute(
    config: JulesConfig,
    skip_paths: list[str | PathLike] | None = None,
) -> JulesConfig:

    config_dict = asdict(copy.deepcopy(config))

    # TODO: skip_paths could instead be a glob pattern?
    if skip_paths is not None:
        resolved_skip_paths = [Path(path).resolve() for path in skip_paths]
        for path_str, resolved_path in zip(skip_paths, resolved_skip_paths):
            if not resolved_path.exists():
                raise FileNotFoundError(
                    "The path '%s' (provided to `skip_paths` as '%s') does not exist"
                    % (resolved_path, path_str)
                )
        skip_paths = resolved_skip_paths

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

            # Skip the parameter if its value is in skip_paths
            if skip_paths:
                if any([value_as_abs_path == skip_path for skip_path in skip_paths]):
                    logger.info(
                        "Skipping parameter %s.nml>%s::%s since value %s is in `skip_paths`"
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
    skip_paths: list[str | PathLike] | None = None,
) -> JulesConfig:
    """Converts relative paths to absolute paths in a JulesConfig object.

    Parameters
    ----------
    config:
        A `JulesConfig` object containing relative paths.
    working_dir:
        The directory with respect to which the relative paths are defined.
    skip_paths:
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
        modified_config = _make_paths_absolute(config, skip_paths)

    return modified_config
