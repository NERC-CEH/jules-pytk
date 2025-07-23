from abc import ABC, abstractmethod
import logging
from os import PathLike
from pathlib import Path
from typing import Any, ClassVar, Self

logger = logging.getLogger(__name__)


class ConfigBase(ABC):
    """Base class for configuration dataclasses."""

    _path: ClassVar[Path | None] = None

    @property
    def path(self) -> Path | None:
        """Path to a directory associated with this object, or `None` if detached."""
        return self._path

    @property
    def is_detached(self) -> bool:
        """Returns `True` if this object is detached, and `False` otherwise."""
        return self.path is None

    @classmethod
    def read(cls, path: str | PathLike, **kwargs) -> Self:
        """Read an existing configuration from this location."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"No file found at {path}")
        logger.info(f"Reading from {path}")

        inst = cls._read(path, **kwargs)

        inst._path = path
        return inst

    @classmethod
    @abstractmethod
    def _read(cls, path: Path, **kwargs) -> Self: ...

    def write(self, path: str | PathLike, overwrite: bool = False, **kwargs) -> None:
        """Write a configuration to a location in the filesystem.

        Parameters:
            path: A location to write the configuration.
            overwrite: Whether to overwrite existing files.
        """
        path = Path(path).resolve()
        if path.is_file() and not overwrite:
            raise FileExistsError(f"There is already a file at {path}")
        logger.info(f"Writing to {path}")

        self._write(path, overwrite)

    @abstractmethod
    def _write(self, path: Path, overwrite: bool) -> None: ...

    def update(self, new_values: Any | None = None) -> None:
        """Update the configuration in-place."""
        if new_values is None and self.is_detached:
            logger.warning(
                "Updating a detached object with no new values does nothing!"
            )
            return

        if new_values is not None:
            logger.info("Updating the object")
            self._update(new_values)

        if not self.is_detached:
            logger.info(f"Updating {self.path}")
            self._write(self.path, overwrite=True)

    @abstractmethod
    def _update(self, new_values: Any) -> None: ...

    def detach(self) -> Self:
        """Returns a detached but otherwise identical instance.

        Here, 'detached' means that the object is not associated with any real
        files living on the disk. I.e. it can be safely modified without
        affecting any files.

        The opposite of detached implies that the object is tracking a real
        file `self.path` or set of files in the directory `self.path`. Any
        changes to the object made using the `update()` method will trigger
        a corresponding update to these files.
        """
        if self.is_detached:
            logger.warning(
                "Calling `detach()` on an object that is already detached. Was this intentional?"
            )
        return self._detach(self)

    @abstractmethod
    def _detach(self) -> Self: ...
