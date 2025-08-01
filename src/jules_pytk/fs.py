from abc import ABC, abstractmethod
import logging
from os import PathLike
from pathlib import Path
from typing import ClassVar, Self

logger = logging.getLogger(__name__)


class FilesystemInterface(ABC):
    """Base class for objects acting as interfaces with the filesystem."""

    # NOTE: we specify _path in this way so that Dataclasses can inherit from this ABC
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
        """Read data from a location in the filesystem."""
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

    def write(
        self, path: str | PathLike, overwrite_existing: bool = False, **kwargs
    ) -> None:
        """Write data to a location in the filesystem."""
        path = Path(path).resolve()

        if not overwrite_existing:
            if path.is_file():
                raise FileExistsError(f"There is already a file at {path}")
            if path.is_dir() and len(list(path.iterdir())) > 0:
                raise FileExistsError(f"There is already a non-empty directory at {path}")

        logger.info(f"Writing to {path}")
        self._write(path, **kwargs)

    def update(self, **kwargs) -> None:
        """Update the filesystem (attached objects only).

        This is functionally equivalent to
        `self.write(self.path, overwrite_existing=True, **kwargs)`
        """
        if self.is_detached:
            logger.warning("Cannot call 'update()' on a detached object!")
            return

        logger.info(f"Updating {self.path}")
        self._write(self.path, **kwargs)

    @abstractmethod
    def _write(self, path: Path, **kwargs) -> None: ...

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
        return self._detach()

    @abstractmethod
    def _detach(self) -> Self: ...
