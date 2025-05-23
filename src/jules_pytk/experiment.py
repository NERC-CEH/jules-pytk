import copy
import fnmatch
from os import PathLike
from pathlib import Path
from typing import Self

from jules_pytk.config import JulesConfig
from jules_pytk.namelists import JulesNamelists, find_namelists

__all__ = [
    "JulesExperiment",
]


class JulesExperiment:
    """Python interface to a JULES experiment.

    This is essentially a JulesConfig object combined with a concrete path
    to an 'experiment directory'.
    """

    def __init__(
        self,
        experiment_dir: str | PathLike,
        namelists_subdir: str | None = None,
    ) -> None:
        experiment_dir = Path(experiment_dir).resolve()

        if namelists_subdir is None:
            namelists_subdir = find_namelists(experiment_dir)

        namelists = JulesNamelists.load(experiment_dir / namelists_subdir)

        config = JulesConfig(namelists, namelists_subdir)

        self._config = config
        self._experiment_dir = experiment_dir

    @classmethod
    def new(cls, config: JulesConfig, experiment_dir: str | PathLike) -> Self:
        # TODO: check that config has data loaded

        experiment_dir = Path(experiment_dir).resolve()
        experiment_dir.mkdir(parents=True, exist_ok=False)

        namelists_dir = experiment_dir / config.namelists_subdir
        namelists_dir.mkdir(parents=True, exist_ok=True)

        config.namelists.write(namelists_dir)

        for file_path in config.namelists.required_files:
            if not file_path.is_absolute():
                (experiment_dir / file_path).parent.mkdir(parents=True, exist_ok=True)
                config.data[str(file_path)].write(experiment_dir / file_path)

        (experiment_dir / config.namelists.output_dir).mkdir(
            parents=True, exist_ok=False
        )

        return cls(experiment_dir, config.namelists_subdir)

    def load_input_data(self, pattern: str = "*", exclude_abspath: bool = True) -> None:
        """
        All _relative_ paths in the namelists are loaded into memory to
        make the configuration portable. _Absolute_ paths are not loaded,
        since these paths would remain valid when the configuration is dumped
        to a new location.
        """
        file_paths = [
            str(file_path) for file_path in self.config.namelists.required_files
        ]
        file_paths = fnmatch.filter(file_paths, pattern)

        for file_path in file_paths:
            if Path(file_path).is_absolute() and not exclude_abspath:
                self.config.data[file_path].read_(file_path)
            else:
                self.config.data[file_path].read_(self.experiment_dir / file_path)

    @property
    def config(self) -> JulesConfig:
        return self._config

    @property
    def experiment_dir(self) -> Path:
        return self._experiment_dir

    @property
    def namelists_dir(self) -> Path:
        return self.experiment_dir / self.config.namelists_subdir

    @property
    def output_dir(self) -> Path:
        return self.experiment_dir / self.config.namelists.output_dir

    @property
    def input_files(self) -> list[Path]:
        return [
            path if path.is_absolute() else self.experiment_dir / path
            for path in self.config.namelists.required_files
        ]

    # ----------------------------------------------------------------------------

    def clone(self, new_path: str | Path) -> Self:
        # TODO: allow shallow copy?
        return type(self)(config=copy.deepcopy(self.config), path=new_path)

    @property
    def has_run(self) -> bool:
        # TODO: figure out how to do this robustly
        raise NotImplementedError

    def run(
        self, jules_exe: str | PathLike | None = None, overwrite: bool = False
    ) -> None:
        # TODO: include has_run flag?
        run_jules(
            config_path=self.config_path,
            exec_path=self.path,
            jules_exe=jules_exe,
            overwrite=overwrite,
        )


class JulesExperimentCollection:
    def __init__(self, *paths: str | PathLike, namelists_subdir: str | None = None):
        self._paths = list(paths)
        self._namelists_subdir = namelists_subdir
        self._index = 0

    @classmethod
    def from_pattern(cls, root: str | PathLike, pattern: str = "*") -> Self:
        # TODO: use glob or regex to construct from base directory and optional prefix
        raise NotImplementedError

    def __iter__(self) -> Self:
        self._index = 0
        return self

    def __next__(self) -> JulesExperiment:
        if self._index < len(self._paths):
            path = self._paths[self._index]
            self._index += 1
            return JulesExperiment(path, self._namelists_subdir)
        else:
            raise StopIteration


"""
def create_experiment_collection(
    path: str | PathLike,
    configs: JulesConfigGenerator,
    prefix: str | None,
) -> JulesExperimentCollection:
    # TODO: possible add timestamp

    collection_path = Path(path).resolve()
    collection_path.mkdir(exist_ok=True, parents=True)

    experiment_paths = []

    for i, config in enumerate(configs):

        experiment_path = collection_path / f"{GLOBAL_PREFIX}_{prefix}_{i}"
        _ = create_experiment(path=experiment_path, config=config)

        experiment_paths.append(experiment_path)

    return JulesExperimentCollection(*experiment_paths)
"""
