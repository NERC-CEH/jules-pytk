# Jules Tools

The [Joint UK Land Environment Simulator](https://jules.jchmr.org/) (JULES) is a [land surface model](https://en.wikipedia.org/wiki/Land_surface_models_(climate)) that has been developed over the last 20 years by a community of UK researchers coordinated by the [Met Office](https://www.metoffice.gov.uk/) and the [UK Centre for Ecology & Hydrology](https://www.ceh.ac.uk/).

The purpose of this package is to collect useful Python tools for working with Jules.


## Getting started

This project uses [`uv`](https://docs.astral.sh/uv/), although you are free to substitute this with other tools for working on Python projects.

Install the project and development dependencies by running

```sh
uv sync
```

You can now run the tests in the repository root with

```sh
uv run pytest
```

## Package overview

### Configuration (`config.py`)

This module defines Python [dataclasses](https://docs.python.org/3/library/dataclasses.html) that essentially act as a read/write interface for Jules configurations, leaning heavily on the [`metaconf`](https://github.com/jmarshrossney/metaconf) package. 

```python
from jules_tools.config import InputFilesConfig, JulesConfig

# Define the (remaining) structure of a Jules configuration.
handler = JulesConfig(
    namelists="namelists",
    inputs={
        "path": "inputs",
        "handler": lambda: InputFilesConfig(
            initial_conditions="initial_conditions.dat",
            tile_fractions="tile_fractions.dat",
            driving_data="Loobos_1997.nc",
        )
    }
)

# config is a Python dict containing all of the parameters, initial
# conditions and (optionally) the driving data
config = handler.read("path/to/loobos/config/")

# ... validate `config`, add missing elements, edit ...

# Write the config to a new location
handler.write("/path/to/new/location/", config)
```

For explanation and further details you may be interested in the [`metaconf` documentation](https://jmarshrossney.github.io/metaconf/) and specifically the [Jules example](https://jmarshrossney.github.io/metaconf/examples/jules/notebook/).

### Runners (`runners.py`)

This module contains classes that make it easier to run Jules from a Python session, via `subprocess.run`.

Currently there are two runners:

1. `JulesExeRunner`, which requires a compiled Jules executable.

2. `JulesUdockerRunner`, which requires a udocker-compliant docker container.

Guidance on how to construct both the executable and the docker container can be found in the `README.md` file at [NERC-CEH/portable-jules](https://github.com/NERC-CEH/portable-jules).

In most situations these runners will be superfluous. The main anticipated use-case is in notebook-based training courses involving small-scale Jules runs.

### Validation (to do)

The ability to read a Jules configuration into a Python `dict` opens up some opportunities to perform validation of the configuration.

This is quite a high priority for this project, since Jules itself performs no meaningful validation (although `rose` sort of does through ['metadata' checks](https://metomi.github.io/rose/doc/html/tutorial/rose/metadata.html)). 

See [Issue #14](https://github.com/NERC-CEH/jules-tools/issues/14).

### Data tools (to do)

Converting data from popular sources into valid Jules inputs can be quite involved and messy. At the very least, one needs to address the following:

- Units, and possibly dimensions if data is aggregated.
- Variables names.
- Coordinate system and grid.
- Temporal resolution.

There is no one-size-fits-all for these steps, but I would like to make some progress towards standardising the data acquisition and pre-processing pipeline for some of the most popular data sources.

## Related work

- [NERC-CEH/portable-jules](https://github.com/NERC-CEH/portable-jules): tools for building and running Jules on any reasonable Unix-based computer.

- [NERC-CEH/jules-emu](https://github.com/NERC-CEH/jules-emu): an in-progress project looking at developing statistical emulators of JULES (uses `jules_tools`).

- [NERC-CEH/jules-academy](https://github.com/NERC-CEH/jules-academy): a notebook-based training course on Jules (uses `jules_tools`).

- [jmarshrossney/metaconf](https://github.com/jmarshrossney/metaconf): a package for working with multi-file configurations such as those used by Jules (used by `jules_tools`)


## Contributing

Contributions are very welcome. Please feel free to raise an issue or open a pull request.

> [!IMPORTANT]
> This is essentially a by-product of my work on other projects. This development model is unlikely to change going forward.

