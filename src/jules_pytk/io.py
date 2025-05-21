import numpy
import xarray


def read_ascii(path: str | PathLike) -> numpy.ndarray:
    with open(path, "r") as file:
        first_line = file.readline().strip()
        if first_line[0] in ("#", "!"):  # Treated as comments by JULES
            comment = first_line
        else:
            comment = ""

    data = numpy.loadtxt(path, comments=("#", "!"))

    return data


def write_ascii(data: numpy.ndarray, path: str | PathLike, comment="") -> None:
    numpy.savetxt(path, data, header=comment)


def read_netcdf(path: str | PathLike, lazy: bool = True) -> xarray.Dataset:
    # NOTE: loads entire dataset into memory. Bad idea for big files
    # TODO: lazy
    return xarray.load_dataset(path)


def write_netcdf(data: xarray.Dataset, path: str | PathLike) -> None:
    data.to_netcdf(path)
