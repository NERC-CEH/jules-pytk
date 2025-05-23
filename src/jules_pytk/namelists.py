from dataclasses import dataclass, fields
from os import PathLike
from pathlib import Path
from typing import Any, Self

import f90nml

from jules_pytk.exceptions import InvalidPath

__all__ = ["JulesNamelists", "find_namelists"]


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
        # Assert that all relative paths are to subdirectories, i.e. aren't
        # given by e.g. "../../file.nc"
        for file_path in self.required_files:
            if not (
                file_path.expanduser().is_absolute()
                or file_path.resolve().is_relative_to(Path.cwd())
                # or Path.cwd() in file_path.resolve().parents
            ):
                raise InvalidPath("Relative paths should not include '..'")

    @classmethod
    def read(cls, namelists_dir: str | PathLike) -> Self:
        """Loads a JulesNamelists object from a directory containing namelist files."""
        namelists_dir = Path(namelists_dir).resolve()

        names = [field.name for field in fields(cls)]

        namelists_dict = {
            name: f90nml.read((namelists_dir / name).with_suffix(".nml"))
            for name in names
        }

        return cls(**namelists_dict)

    def write(self, namelists_dir: str | PathLike) -> None:
        """Writes namelist files to a directory.

        Raises FileExistsError if files already exist.
        """
        namelists_dir = Path(namelists_dir).resolve()

        names = [field.name for field in fields(self)]

        for name in names:
            file_path = (namelists_dir / name).with_suffix(".nml")
            getattr(self, name).write(
                file_path, force=False
            )  # do not override existing

    @property
    def parameters(self) -> dict[tuple[str, str, str], Any]:
        """A flattened dict containing all parameters, indexed by 3-tuples."""
        result = {}
        for field in fields(self):
            namelist = getattr(self, field.name)
            for (group, param), value in namelist.groups():
                result[(field.name, group, param)] = value
        return result

    @property
    def file_parameters(self) -> dict[tuple[str, str, str], str]:
        """A subset of `parameters` that point to input files."""
        valid_extensions = (".nc", ".cdf", ".asc", ".txt", ".dat")
        return {
            key: value
            for key, value in self.parameters.items()
            if isinstance(value, str) and value.endswith(valid_extensions)
        }

    @property
    def required_files(self) -> list[Path]:
        """List of all unique file paths present in the namelists."""
        return [Path(path) for path in set(self.file_parameters.values())]

    @property
    def output_dir(self) -> Path:
        """Shortcut to JULES_OUTPUT::output_dir, for convenience"""
        return Path(getattr(self, "output").get("jules_output").get("output_dir"))

    # ----------------------------------------------------------------------------------

    def get(self, namelist: str, group: str | None = None, param: str | None = None):
        if group is None and param is not None:
            raise ValueError("Cannot provide `param` without also providing `group`")

        res = getattr(self, namelist)

        if group is not None:
            res = res.get(group)

        if param is not None:
            res = res.get(param)

        return res

    def __getitem__(
        self, key: str | tuple[str] | tuple[str, str] | tuple[str, str, str]
    ):
        """Access the namelists/groups/parameters with 1-/2-/3-tuple keys."""
        if isinstance(key, str):
            key = (key,)
        if len(key) == 1:
            return getattr(self, key[0])
        elif len(key) == 2:
            return getattr(self, key[0]).get(key[1])
        elif len(key) == 3:
            return getattr(self, key[0]).get(key[1]).get(key[2])

    @property
    def filenames(self) -> list[str]:
        return [f"{namelist}.nml" for namelist in fields(self)]


def find_namelists(root: Path) -> str:
    # TODO: decide if symlinks allowed
    candidates = [
        path.parent.relative_to(root)
        for path in root.rglob("ancillaries.nml", recurse_symlinks=False)
        if all(
            [(path.parent / nml_file).exists() for nml_file in JulesNamelists.files()]
        )
    ]
    if len(candidates) == 0:
        raise FileNotFoundError(f"Namelists not found under directory '{root}'")
    elif len(candidates) > 1:
        raise Exception(
            f"Found more than one candidate namelists directory: {candidates}."
        )

    return str(candidates[0])
