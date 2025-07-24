from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Generator, Self

from jules_pytk.exceptions import InvalidPath
from jules_pytk.utils import FrozenDict

from .base import ConfigBase
from .inputs import JulesInput
from .namelists import JulesNamelists, find_namelists

__all__ = ["JulesConfig"]

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class JulesConfig(ConfigBase):
    """
    Dataclass representing a JULES configuration.

    This couples a `JulesNamelists` object with a set of `JulesInput` objects
    associated with each unique file path specified in the namelists. These
    `JulesInput` objects can, optionally, be loaded with data and edited to
    dynamically create new configurations.
    """

    namelists: JulesNamelists
    namelists_subdir: str
    inputs: FrozenDict[str, JulesInput]

    def __post_init__(self) -> None:
        # Assert that namelists path is either "." or a subdirectory
        namelists_subdir = Path(self.namelists_subdir)
        if namelists_subdir.expanduser().is_absolute():
            raise InvalidPath(
                "`namelists_subdir` should be relative to the run directory"
            )
        if not namelists_subdir.resolve().is_relative_to(Path.cwd()):
            raise InvalidPath("`namelists_subdir` should not include '..'")

        assert list(self.inputs.keys()) == [
            str(path) for path in self.namelists.input_files(rel_only=True)
        ]

        if not self.namelists.is_detached:
            # Check that namelists path ends with namelists_subdir
            assert self.namelists.path.match(self.namelists_subdir)

    def __eq__(self, other) -> bool:
        return (
            (type(other) is type(self))
            and (self.namelists == other.namelists)
            and (self.namelists_subdir == other.namelists_subdir)
            and (self.inputs == other.inputs)
        )

    @classmethod
    def _read(cls, path: Path, namelists_subdir: str | None = None) -> Self:
        if namelists_subdir is None:
            namelists_subdir = find_namelists(path)

        namelists_dir = path / namelists_subdir
        namelists = JulesNamelists.read(namelists_dir)

        # Attempt to read all input files with relative paths
        inputs = FrozenDict(
            {
                str(file_path): JulesInput(file_path.suffix).read(path / file_path)
                for file_path in namelists.input_files(rel_only=True)
            }
        )

        return cls(
            namelists=namelists, namelists_subdir=namelists_subdir, inputs=inputs
        )

    def _write(self, path: Path, overwrite: bool) -> None:
        namelists_dir = path / self.namelists_subdir

        namelists_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Writing namelists to {namelists_dir}")
        self.namelists.write(namelists_dir, overwrite=overwrite)

        assert self.check_inputs_match_required_files()

        for path_in_namelists in self.namelists.input_files(rel_only=True):
            full_path = path / path_in_namelists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            self.inputs[str(path_in_namelists)].write(full_path, overwrite=overwrite)

    def _update(self, new_values) -> None:
        raise NotImplementedError("Cannot update JulesConfig directly")

    def _detach(self) -> Self:
        return type(self)(
            namelists=self.namelists.detach(),
            namelists_subdir=self.namelists_subdir,
            inputs=FrozenDict(
                {file_path: input.detach() for file_path, input in self.inputs.items()}
            ),
        )

    # -----------------------------------

    def check_required_files_exist(self) -> bool:
        rel_paths, abs_paths = [], []
        for path in self.namelists.input_files():
            (abs_paths if path.is_absolute() else rel_paths).append(path)

        if self.is_detached:
            paths_to_check = abs_paths
            logger.warning(
                "Detached configuration: Only checking for existence of absolute paths!"
            )
        else:
            paths_to_check = abs_paths + [
                self.path / file_path for file_path in rel_paths
            ]

        result = True

        for path in paths_to_check:
            if not path.exists():
                logger.warning(f"Path '{path}' does not exist!")
                result = False
            elif not path.is_file():
                logger.warning(f"Path '{path}' is not a file!")
                result = False

        return result

    def check_inputs_match_required_files(self) -> bool:
        required_files = set(
            [str(path) for path in self.namelists.input_files(rel_only=True)]
        )
        inputs = set(self.inputs.keys())

        result = True

        # if required_files | inputs != required_files & inputs:

        for file in required_files:
            if file not in inputs:
                logger.warning(f"Required file '{file}' is not in self.inputs.")
                result = False

        for file in inputs:
            if file not in required_files:
                logger.warning(f"Input '{file}' is not required by namelists.")
                result = False

        return result

    @property
    def namelists_dir(self) -> Path | None:
        return None if self.is_detached else self.path / self.namelists_subdir

    @property
    def input_files(self) -> list[Path | None]:
        return [
            path if path.is_absolute() else self.path / path
            for path in self.namelists.input_files()
        ]

    @property
    def output_dir(self) -> Path | None:
        path_in_namelists = Path(
            getattr(self.namelists, "output").get("jules_output").get("output_dir")
        )

        if path_in_namelists.is_absolute():
            return path_in_namelists

        if not self.is_detached:
            return self.path / path_in_namelists

        logger.warning(
            "Unable to infer output directory for detached configurations. Returning `None`."
        )
        return None


#type JulesConfigGenerator = Generator[JulesConfig, None, None]
