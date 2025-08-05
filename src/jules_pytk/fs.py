import dataclasses
import logging
from os import PathLike

import dirconf
import f90nml
import numpy
import xarray

logger = logging.getLogger(__name__)


class AsciiFileHandler:
    def read(self, path: str | PathLike) -> dict[str, numpy.ndarray | str]:
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
        data: dict[str, numpy.ndarray | str],
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


class NamelistFileHandler:
    def read(self, path: str | PathLike) -> dict:
        data = f90nml.read(path)
        return data.todict()

    def write(
        self, path: str | PathLike, data: dict, *, overwrite_ok: bool = False
    ) -> None:
        data = f90nml.write(data, path, force=overwrite_ok)


dirconf.register_handler("ascii", AsciiFileHandler, [".txt", ".dat", ".asc"])
dirconf.register_handler("netcdf", NetcdfFileHandler, [".nc", ".cdf"])

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

NamelistsDirectory = dirconf.make_directory_config(
    cls_name="NamelistsDirectory",
    config={
        name: {"path": f"{name}.nml", "handler": NamelistFileHandler}
        for name in _jules_namelists
    },
)

JulesDirectory = dirconf.make_directory_config(
    cls_name="JulesDirectory",
    config={
        "namelists": {"handler": NamelistsDirectory},
        "initial_conditions": {},
        "driving_data": {},
        "tile_fractions": {},
    },
)

