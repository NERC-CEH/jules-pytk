from abc import ABCMeta, abstractmethod
from dataclasses import asdict, dataclass, fields
import logging
from os import PathLike
from pathlib import Path
from typing import Any, ClassVar, Self


@dataclass(kw_only=True)
class ConfigBase:
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
            logger.warning("Calling `detach()` on an object that is already detached. Was this intentional?")

        self.on_detach()

        return type(self)(**asdict(self))

    def on_detach(self) -> None:
        """Actions to take before returning a detached copy of the object."""
        ...

    @classmethod
    def read(cls, path: str | PathLike) -> Self:
        """Read an existing configuration from this location."""
        inst = cls._read(path)
        inst._path = path
        return inst

    @classmethod
    @abstractmethod
    def _read(cls, path: str | PathLike) -> Self:
        ...


    def write(self, path: str | PathLike, overwrite: bool = False) -> Self:
        """Write a configuration to a location in the filesystem.

        Parameters:
            path: A location to write the configuration.
            overwrite: Whether to overwrite existing files.

        Returns:
            A copy of `self` that is 'attached' to the path.
        """
        self._write(path, overwrite)
        return type(self).read(path)

    @abstractmethod
    def _write(self, path: str | PathLike, overwrite: bool) -> None:
        ...

    def update(self, new_values: Any, **kwargs) -> None:
        """Update the configuration in-place."""
        self._update(new_values, **kwargs)

        if not self.is_detached():
            logger.info("Updating configuration at {self.path}")
            self.write(self.path, overwrite=True)

    @abstractmethod
    def _update(self, new_values: Any, **kwargs) -> None:
        ...

