from dataclasses import dataclass, field
import logging
from os import PathLike
from pathlib import Path
from typing import ClassVar, Generator, Self

from jules_pytk.exceptions import InvalidPath
from jules_pytk.utils import FrozenDict

from .base import ConfigBase
from .inputs import JulesInput
from .namelists import JulesNamelists

__all__ = ["JulesConfig"]

logger = logging.getLogger(__name__)


@dataclass
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
    data: FrozenDict[str, JulesInput] = field(init=False)

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
                for file_path in self.namelists.input_files()
            }
        )

    def __eq__(self, other) -> bool:
        return (
            (type(other) is type(self))
            and (self.namelists == other.namelists)
            and (self.data == other.data)
        )

    def _read(cls, path: Path, namelists_subdir: str) -> Self:
        namelists_dir = path / namelists_subdir
        namelists = JulesNamelists.read(namelists_dir)

        data = FrozenDict(
            {
                str(file_path): JulesInput(file_path.suffix)
                if not file_path.is_absolute()
                else None
                for file_path in self.namelists.input_files()
            }
        )

        return cls(namelists=namelists, namelists_subdir=namelists_subdir, data=data)

    def _write(self, path: Path, overwrite: bool) -> None:
        namelists_dir = path / self.namelists_subdir

        namelists_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Writing namelists to {namelists_dir}")
        self.namelists.write(namelists_dir, overwrite=overwrite)

        for path_in_namelists in self.namelists.required_files:
            if not path_in_namelists.is_absolute():
                full_path = path / path_in_namelists
                full_path.parent.mkdir(parents=True, exist_ok=True)
                self.data[str(path_in_namelists)].write(full_path, overwrite=overwrite)

    def _update(self, new_values) -> None:
        raise NotImplementedError("Cannot update JulesConfig directly")

    def _detach(self) -> Self:
        return type(self)(
            namelists=self.namelists.detach(),
            namelists_dir=self.namelists_dir,
            data=FrozenDict(
                {file_path: input.detach() for file_path, input in self.data.items()}
            ),
        )

    # ---------------------------------------------------------------------------

    @property
    def output_dir(self) -> Path:
        if self.detached:
            return Path(self.namelists.output_dir)
        else:
            return self.path / self.namelists.output_dir

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


type JulesConfigGenerator = Generator[JulesConfig, None, None]
