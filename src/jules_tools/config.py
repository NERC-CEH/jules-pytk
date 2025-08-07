import logging
from os import PathLike
from typing import TypedDict

import metaconf
import f90nml
import numpy
import xarray

logger = logging.getLogger(__name__)

__all__ = [
    "AsciiFileHandler",
    "NetcdfFileHandler",
    "NamelistFileHandler",
    "NamelistFilesConfig",
    "InputFilesConfig",
    "JulesConfig",
]


class NamelistFileHandler:
    def read(self, path: str | PathLike) -> dict:
        data = f90nml.read(path)
        return data.todict()

    def write(
        self, path: str | PathLike, data: dict, *, overwrite_ok: bool = False
    ) -> None:
        f90nml.write(data, path, force=overwrite_ok)


_jules_namelists = [
    "ancillaries",
    "crop_params",
    "drive",
    "fire",
    "imogen",
    "initial_conditions",
    "jules_deposition",
    "jules_hydrology",
    "jules_irrig",
    "jules_prnt_control",
    "jules_radiation",
    "jules_rivers",
    "jules_snow",
    "jules_soil_biogeochem",
    "jules_soil",
    "jules_surface",
    "jules_surface_types",
    "jules_vegetation",
    "jules_water_resources",
    "model_environment",
    "model_grid",
    "nveg_params",
    "output",
    "pft_params",
    "prescribed_data",
    "science_fixes",
    "timesteps",
    "triffid_params",
    "urban",
]

NamelistFilesConfig = metaconf.make_metaconfig(
    cls_name="NamelistFilesConfig",
    config={
        name: {"path": f"{name}.nml", "handler": NamelistFileHandler}
        for name in _jules_namelists
    },
)


@metaconf.handle_missing(
    test_on_read=lambda path: path.exists(),
    test_on_write=lambda path, data, **_: not (
        data is metaconf.MISSING or path.is_absolute()
    ),
)
class AsciiFileHandler:
    class AsciiData(TypedDict):
        values: numpy.ndarray
        comment: str

    def read(self, path: str | PathLike) -> AsciiData:
        comment_lines = []
        with open(path, "r") as file:
            for line in file:
                # remove leading/trailing whitespace and newline
                line = line.strip()
                if line.startswith(("#", "!")):
                    comment_lines.append(line)
                else:
                    break
        comment = "\n".join(comment_lines)

        values = numpy.loadtxt(str(path), comments=("#", "!"))

        return {"values": values, "comment": comment}

    def write(
        self,
        path: str | PathLike,
        data: AsciiData,
        *,
        overwrite_ok: bool = False,
    ) -> None:
        numpy.savetxt(
            str(path),
            data["values"],
            fmt="%.5f",
            header=data["comment"],
            comments="#",
        )


@metaconf.handle_missing(
    test_on_read=lambda path: path.exists() and not path.is_absolute(),
    test_on_write=lambda path, data, **_: not (
        data is metaconf.MISSING or path.is_absolute()
    ),
)
class NetcdfFileHandler:
    def read(self, path: str | PathLike) -> xarray.Dataset:
        logger.warning("Loading full dataset from {path}")
        dataset = xarray.load_dataset(path)
        return dataset

    def write(
        self, path: str | PathLike, data: xarray.Dataset, *, overwrite_ok: bool = False
    ) -> None:
        if not overwrite_ok and path.is_file():
            raise FileExistsError(f"There is already a file at '{path}'")
        data.to_netcdf(path)


metaconf.register_handler("ascii", AsciiFileHandler, [".txt", ".dat", ".asc"])
metaconf.register_handler("netcdf", NetcdfFileHandler, [".nc", ".cdf"])

# TODO: currently this is a minimal subset of possible input files
# and should be expanded to include more/all of them
InputFilesConfig = metaconf.make_metaconfig(
    cls_name="InputFilesConfig",
    config={
        "initial_conditions": {},
        "driving_data": {},
        "tile_fractions": {},
    },
)


JulesConfig = metaconf.make_metaconfig(
    cls_name="JulesDirectoryConfig",
    config={
        "namelists": {
            "handler": NamelistFilesConfig
        },
        "inputs": {},
    },
)
