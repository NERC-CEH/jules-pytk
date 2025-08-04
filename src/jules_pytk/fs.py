import dataclasses
import logging
from os import PathLike

import dcdir
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

dcdir.register_handler(".txt", AsciiFileHandler)
dcdir.register_handler(".dat", AsciiFileHandler)
dcdir.register_handler(".asc", AsciiFileHandler)
dcdir.register_handler(".nc", NetcdfFileHandler)
dcdir.register_handler(".cdf", NetcdfFileHandler)
dcdir.register_handler(".nml", NamelistFileHandler)

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
NamelistsDirectory = dataclasses.make_dataclass(
    cls_name="NamelistsDirectory",
    fields=[
        (name, str, dataclasses.field(init=False, default=f"{name}.nml"))
        for name in _jules_namelists
    ],
    bases=(dcdir.DataclassDirectory,),
)

"""
@dataclass(kw_only=True)
_class NamelistsDirectory(dcdir.DataclassDirectory):
    ancillaries: str = field(init=False, default="ancillaries.nml")
    crop_params: str = field(init=False, default="crop_params.nml")
    drive: str = field(init=False, default="drive.nml")
    fire: str = field(init=False, default="fire.nml")
    imogen: str = field(init=False, default="imogen.nml")
    initial_conditions:  str = field(init=False, default="initial_conditions.nml")
    jules_deposition:  str = field(init=False, default="jules_deposition.nml")
    jules_hydrology:  str = field(init=False, default="jules_hydrology.nml")
    jules_irrig:  str = field(init=False, default="jules_irrig.nml")
    jules_prnt_control:  str = field(init=False, default="jules_prnt_control.nml")
    jules_radiation:  str = field(init=False, default="jules_radiation.nml")
    jules_rivers:  str = field(init=False, default="jules_rivers.nml")
    jules_snow:  str = field(init=False, default="jules_snow.nml")
    jules_soil_biogeochem:  str = field(init=False, default="jules_soil_biogeochem.nml")
    jules_soil:  str = field(init=False, default="jules_soil.nml")
    jules_surface:  str = field(init=False, default="jules_surface.nml")
    jules_surface_types:  str = field(init=False, default="jules_surface_types.nml")
    jules_vegetation:  str = field(init=False, default="jules_vegetation.nml")
    jules_water_resources:  str = field(init=False, default="jules_water_resources.nml")
    model_environment:  str = field(init=False, default="model_environment.nml")
    model_grid:  str = field(init=False, default="model_grid.nml")
    nveg_params:  str = field(init=False, default="nveg_params.nml")
    output:  str = field(init=False, default="output.nml")
    pft_params:  str = field(init=False, default="pft_params.nml")
    prescribed_data:  str = field(init=False, default="prescribed_data.nml")
    science_fixes:  str = field(init=False, default="science_fixes.nml")
    timesteps:  str = field(init=False, default="timesteps.nml")
    triffid_params:  str = field(init=False, default="triffid_params.nml")
    urban:  str = field(init=False, default="urban.nml")
"""

