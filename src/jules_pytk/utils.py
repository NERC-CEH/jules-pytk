import logging
import os
import pathlib

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class switch_dir:
    """Context manager for changing to *existing* directory."""

    def __init__(self, path: str | os.PathLike, verbose: bool = False):
        self.new = pathlib.Path(path)

        if not self.new.is_dir():
            raise (
                NotADirectoryError(f"{self.new} is not a directory")
                if self.new.exists()
                else FileNotFoundError(f"{self.new} does not exist")
            )

        # TODO: consider a global verbosity instead
        self.verbose = verbose

    def __enter__(self):
        if self.verbose:
            logger.info("Switching directory to %s" % self.new)
        self.old = pathlib.Path.cwd()
        os.chdir(self.new)

    def __exit__(self, etype, value, traceback):
        if self.verbose:
            logger.info("Switching directory back to %s" % self.old)
        os.chdir(self.old)


class FrozenDict(dict):
    """Restricted version of `dict` that prohibits new keys after instantiation."""

    def __setitem__(self, key, value):
        if key not in self:
            allowed_keys = list(self.keys())
            raise TypeError(f"New keys may not be added. Allowed keys: {allowed_keys}")
        super().__setitem__(key, value)
