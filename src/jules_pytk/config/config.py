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
            str(path) for path in self.namelists.input_files()
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

        inputs = FrozenDict(
            {
                str(file_path): JulesInput(file_path.suffix).read(path / file_path)
                if not file_path.is_absolute()
                else None
                for file_path in namelists.input_files()
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

        for path_in_namelists in self.namelists.input_files():
            if not path_in_namelists.is_absolute():
                full_path = path / path_in_namelists
                full_path.parent.mkdir(parents=True, exist_ok=True)
                self.inputs[str(path_in_namelists)].write(
                    full_path, overwrite=overwrite
                )

    def _update(self, new_values) -> None:
        raise NotImplementedError("Cannot update JulesConfig directly")

    def _detach(self) -> Self:
        return type(self)(
            namelists=self.namelists.detach(),
            namelists_dir=self.namelists_dir,
            data=FrozenDict(
                {file_path: input.detach() for file_path, input in self.inputs.items()}
            ),
        )

    @property
    def namelists_dir(self) -> Path | None:
        return None if self.detached else self.path / self.namelists_subdir

    @property
    def input_files(self) -> list[Path | None]:
        return [
            path if path.is_absolute() else self.path / path
            for path in self.namelists.input_files()
        ]

    @property
    def output_dir(self) -> Path | None:
        return None if self.detached else self.path / self.namelists.output_dir


type JulesConfigGenerator = Generator[JulesConfig, None, None]
