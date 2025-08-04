from dataclasses import asdict, dataclass, fields
import logging
from pathlib import Path
from typing import Any, Generator, Self

import f90nml

from ..exceptions import InvalidPath
from ..fs import FilesystemInterface

__all__ = ["JulesNamelists", "find_namelists"]

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class JulesNamelists(FilesystemInterface):
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

    def _post_init__(self) -> None:
        # Assert that all relative paths are to subdirectories, i.e. aren't
        # given by e.g. "../../file.nc"
        for file_path in self.input_files():
            if not (
                file_path.expanduser().is_absolute()
                or file_path.resolve().is_relative_to(Path.cwd())
                # or Path.cwd() in file_path.resolve().parents
            ):
                raise InvalidPath("Relative paths should not include '..'")

    @classmethod
    def _read(cls, path: Path) -> Self:
        names = [field.name for field in fields(cls)]

        namelists_dict = {
            name: f90nml.read((path / name).with_suffix(".nml")) for name in names
        }

        return cls(**namelists_dict)

    def _write(self, path: Path) -> None:
        namelists_dir = path

        names = [field.name for field in fields(self)]

        for name in names:
            file_path = (namelists_dir / name).with_suffix(".nml")
            getattr(self, name).write(file_path, force=True)

    def _detach(self) -> Self:
        return type(self)(**asdict(self))

    """
    def _update(self, new_values: dict[str, dict]) -> None:
        for namelist, patch in new_values.items():
            # Patch the namelists in-memory
            getattr(self, namelist).patch(patch)
    """

    # --------------------- Container access - experimental -----------------

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

        match len(key):
            case 1:
                return getattr(self, key[0])
            case 2:
                return getattr(self, key[0]).get(key[1])
            case 3:
                return getattr(self, key[0]).get(key[1]).get(key[2])
            case _:
                raise ValueError(f"`key` must have 1, 2, or 3 elements (got {len(key)}).")

    # -------------------- Properties - experimental -------------------

    def parameters(self) -> Generator[tuple[tuple[str, str, str], Any], None, None]:
        """Iterates over all parameters, labelled by 3-tuples.

        Yields:
            A 2-tuple containing (i) a 3-tuple (namelist, group, parameter)
            which labels the parameter, and (ii) the value of the parameter itself.
        """
        for field in fields(self):
            namelist = field.name
            for (group, param), value in getattr(self, namelist).groups():
                yield (namelist, group, param), value

    def _file_parameters(
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
        unique_files = set([Path(path) for _, path in self._file_parameters()])

        if rel_only:
            return [path for path in unique_files if not path.is_absolute()]
        else:
            return list(unique_files)

        rel, abs = [], []
        for path in unique_files:
            (abs if path.is_absolute() else rel).append(path)

        return rel, abs


def find_namelists(root: Path) -> str:
    # TODO: decide if symlinks allowed
    candidates = [
        path.parent.relative_to(root)
        for path in root.rglob("ancillaries.nml")
        if all(
            [
                (path.parent / field.name).with_suffix(".nml").exists()
                for field in fields(JulesNamelists)
            ]
        )
    ]
    if len(candidates) == 0:
        raise FileNotFoundError(f"Namelists not found under directory '{root}'")
    elif len(candidates) > 1:
        logger.warning(
            f"Found more than one candidate namelists directory: {candidates}. Returning the first one."
        )

    return str(candidates[0])
