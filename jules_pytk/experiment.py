from os import PathLike
from pathlib import Path
from typing import Self

from .config import JulesConfig, JulesConfigGenerator, read_config
from .run import run_jules

GLOBAL_PREFIX = "expt"
# NOTE: Unfortunately having a subdirectory for config means either
# (a) abs path for output_dir, which breaks if directory is moved, or
# (b) gymnastics with rel paths which breaks the simple `parallel jules.exe $paths`
CONFIG_DIR = ""


class JulesExperiment:
    """Python interface to a JULES experiment."""

    def __init__(self, path: str | PathLike):
        path = Path(path).resolve()
        self._path = path
        self._config = read_config(self.config_path)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def config_path(self) -> Path:
        return self._path / CONFIG_DIR

    @property
    def output_path(self) -> Path:
        config_output_path = self._config.output.get("jules_output").get("output_dir")

        # Assume it is a mistake if the output directory is absolute
        # TODO: create a whole post-init validation for conformity to standard setup?
        assert not Path(config_output_path).is_absolute()

        return self._path / config_output_path

    @property
    def has_run(self) -> bool:
        # TODO: figure out how to do this robustly
        raise NotImplementedError

    @property
    def config(self) -> JulesConfig:
        # NOTE: potential problem that this is mutable!
        return self._config

    def run(
        self, jules_exe: str | PathLike | None = None, overwrite_existing: bool = False
    ) -> None:
        # TODO: include has_run flag?
        run_jules(
            config_path=self.config_path,
            exec_path=self.path,
            jules_exe=jules_exe,
            overwrite_existing=overwrite_existing,
        )


class JulesExperimentCollection:
    def __init__(self, *paths: str | PathLike):
        self._paths = list(paths)
        self._index = 0

    @classmethod
    def from_path(cls, path: str | PathLike, prefix: str | None = None) -> Self:
        # TODO: use glob or regex to construct from base directory and optional prefix
        raise NotImplementedError

    def __iter__(self) -> Self:
        self._index = 0
        return self

    def __next__(self) -> JulesExperiment:
        if self._index < len(self._paths):
            path = self._paths[self._index]
            self._index += 1
            return JulesExperiment(path)
        else:
            raise StopIteration


def create_experiment(path: str | PathLike, config: JulesConfig) -> JulesExperiment:
    path = Path(path).resolve()
    path.mkdir(exist_ok=False, parents=True)

    config_path = path / CONFIG_DIR
    config_path.mkdir(exist_ok=True)  # exist_ok=True required if config_path==path

    config.dump(config_path)

    # NOTE: currently output_dir created on-demand
    # config_output_dir = config.output.get("jules_output").get("output_dir")
    # assert not Path(config_output_dir).is_absolute()
    # output_path = path / config_output_dir
    # output_path.mkdir(exist_ok=False, parents=True)

    # TODO: Metadata?

    return JulesExperiment(path)


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
