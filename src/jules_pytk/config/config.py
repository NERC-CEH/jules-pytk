from dataclasses import dataclass, field
import logging
from os import PathLike
from pathlib import Path
from typing import ClassVar, Generator, Self

from jules_pytk.exceptions import InvalidPath
from jules_pytk.utils import FrozenDict
from .inputs import JulesInput
from .namelists import JulesNamelists

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

    _path: ClassVar[Path | None] = None

    def __post_init__(self) -> None:
        # Assert that namelists path is either "." or a subdirectory
        namelists_subdir = Path(self.namelists_subdir)
        if namelists_subdir.expanduser().is_absolute():
            raise InvalidPath(
                "`namelists_subdir` should be relative to the run directory"
            )
        if not namelists_subdir.resolve().is_relative_to(Path.cwd()):
            raise InvalidPath("`namelists_subdir` should not include '..'")

        # TODO: If namelists object is attached to a concrete directory, we can
        # infer `config_path` from `namelists.path` and `namelists_subdir`.
        # We would also need to infer data paths.
        if not self.namelists.is_detached:
            logger.warning("Attached namelists not yet implemented.")

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

    @property
    def path(self) -> Path | None:
        """Path to a configuration directory, or `None` if detached."""
        return self._path

    @property
    def is_detached(self) -> bool:
        """Returns `True` if this object is detached, and `False` otherwise."""
        result = self.path is None
        assert result == self.namelists.is_detached
        return result

    def detach(self) -> Self:
        """Returns a detached but otherwise identical instance of `JulesConfig`."""
        if self.is_detached:
            logger.warning(
                "Calling `detach()` on an instance of `JulesConfig` that is already detached. Was this intentional?"
            )

        return type(self)(
            namelists=self.namelists.detach(),
            namelists_dir=self.namelists_dir,
            data=...,  # TODO: load data?
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
