from dataclasses import dataclass, field
import logging
from os import PathLike
from pathlib import Path
from typing import Generator, Self

from jules_pytk.exceptions import InvalidPath
from jules_pytk.inputs import JulesInput
from jules_pytk.namelists import JulesNamelists
from jules_pytk.utils import FrozenDict

__all__ = ["JulesConfig"]

logger = logging.getLogger(__name__)


@dataclass
class JulesConfig:
    """
    Dataclass representing a JULES configuration.

    This couples a `JulesNamelists` object with a set of `JulesInput` objects
    associated with each unique file path specified in the namelists. These
    `JulesInput` objects can, optionally, be loaded with data and edited to
    dynamically create new configurations.
    """

    namelists: JulesNamelists
    namelists_subdir: str
    data: FrozenDict[str, JulesInput] = field(init=False)  # NOTE: wrong type ann

    def __post_init__(self) -> None:
        # Assert that namelists path is either "." or a subdirectory
        namelists_subdir = Path(self.namelists_subdir)
        if namelists_subdir.expanduser().is_absolute():
            raise InvalidPath(
                "`namelists_subdir` should be relative to the run directory"
            )
        if not namelists_subdir.resolve().is_relative_to(Path.cwd()):
            raise InvalidPath("`namelists_subdir` should not include '..'")

        # Populate self.data dict with correct keys, i.e. required file paths
        self.data = FrozenDict(
            {
                str(file_path): JulesInput(file_path.suffix)
                for file_path in self.namelists.required_files
            }
        )

    def __eq__(self, other) -> bool:
        return (
            (type(other) is type(self))
            and (self.namelists == other.namelists)
            and (self.data == other.data)
        )

    def write(self, experiment_dir: str | PathLike) -> None:
        # TODO: Check valid config, e.g. has it loaded data?

        experiment_dir = Path(experiment_dir).resolve()
        namelists_dir = experiment_dir / self.namelists_subdir

        namelists_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Writing namelists to {namelists_dir}")
        self.namelists.write(namelists_dir)

        for path_in_namelists in self.namelists.required_files:
            if not path_in_namelists.is_absolute():
                full_path = experiment_dir / path_in_namelists
                logger.info(f"Writing data to {full_path}")
                full_path.parent.mkdir(parents=True, exist_ok=True)
                self.data[str(path_in_namelists)].write(full_path)

    # ---------------------------------------------------------------------------

    def detach_(self) -> None:
        """Detach from a filesystem path; load all data etc."""
        ...

    @staticmethod
    def from_experiment(experiment_dir: str | PathLike) -> Self:
        """Load a JulesConfig object from an existing experiment."""
        from jules_pytk.experiment import JulesExperiment

        experiment = JulesExperiment(experiment_dir)
        experiment.load_input_data()

        # NOTE: do not use experiment.config, since this is a _property object_
        # and among other things causes __eq__ to fail!
        # TODO: Reconsider the whole rationale of making config a property.
        return experiment._config

    def load_input_data(self, src: str | PathLike, dest: str = "infer") -> None:
        src = Path(src)

        if dest == "infer":
            dest = src

    def dump(self) -> None:
        """Dump config to dict/json"""
        ...

    @property
    def is_portable(self) -> bool:
        """Returns True if all file inputs given by relative paths have data loaded."""
        rel_paths = [str(path) for path in self.file_paths if not path.is_absolute()]
        return all([self.input[path] is not None for path in rel_paths])

    def validate(self) -> NotImplemented:
        # TODO: check that all files are accounted for etc
        return NotImplemented


type JulesConfigGenerator = Generator[JulesConfig, None, None]
