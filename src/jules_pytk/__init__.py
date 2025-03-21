from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("jules_pytk")
except PackageNotFoundError:
    # package is not installed
    pass
