from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("jules_tools")
except PackageNotFoundError:
    # package is not installed
    pass
