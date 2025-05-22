from os import PathLike
from pathlib import Path
from typing import Generator, Self

from .namelists import JulesNamelists
from .inputs import JulesInput

__all__ = ["JulesConfig"]


def _find_namelists(exec_dir: Path) -> Path:
    # TODO: decide how much effort to put into this
    raise NotImplementedError


class JulesConfig:
    """
    Class representing a JULES configuration.

    This couples a `JulesNamelists` object with a set of `JulesInput` objects
    associated with each unique file path specified in the namelists. These
    `JulesInput` objects can, optionally, be loaded with data and edited to
    dynamically create new configurations.
    """

    def __init__(self, namelists: JulesNamelists):
        self._namelists = namelists
        self._inputs = [JulesInput(path) for path in namelists.file_paths]

    @property
    def namelists(self) -> JulesNamelists:
        return self._namelists

    @property
    def inputs(self) -> list[JulesInput]:
        # TODO: consider dict with file paths and/or namelist params as keys
        return self._inputs

    def __eq__(self, other) -> bool:
        if type(other) != type(self):
            return False
        return self.namelists == other.namelists and self.inputs == other.inputs

    @classmethod
    def load(
        cls, exec_dir: str | PathLike, nml_subdir: str | PathLike | None = None
    ) -> Self:
        """Load an existing configuration.

        This requires two paths:
        1) The directory where JULES is executed.
        2) The namelists directory, which should be a subdirectory of 1)
           or the same directory.

        All _relative_ paths in the namelists are loaded into memory to
        make the configuration portable. _Absolute_ paths are not loaded,
        since these paths would remain valid when the configuration is dumped
        to a new location.
        """

        exec_dir = Path(exec_dir).resolve()

        if nml_subdir is None:
            nml_subdir = _find_namelists(exec_dir)

        namelists = JulesNamelists.load(exec_dir / nml_subdir)

        config = cls(namelists=namelists)

        # Load data from relative paths
        for input in config.inputs:
            if not input.path.is_absolute():
                input.load(exec_dir / input.path)

        return config

    def dump(self, exec_dir: str | PathLike, nml_subdir: str | PathLike = ".") -> None:
        """Dump the configuration to a new location."""
        exec_dir = Path(exec_dir).resolve()

        namelists_dir = exec_dir / nml_subdir
        namelists_dir.mkdir(parents=True, exist_ok=True)
        self.namelists.dump(namelists_dir)

        for input in self.inputs:
            if not input.path.is_absolute():
                file_path = exec_dir / input.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                input.dump(file_path)

    def validate(self) -> NotImplemented:
        # TODO: check that all files are accounted for etc
        return NotImplemented


type JulesConfigGenerator = Generator[JulesConfig, None, None]
