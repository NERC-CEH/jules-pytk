---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.17.2
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# Configuring a JULES experiment

```python
from pathlib import Path

from jules_tools.config import JulesConfig, NamelistFilesConfig, InputFilesConfig
```

```python
# get repo root
import subprocess

res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)

repo_root = Path(res.stdout.strip())

repo_root
```

```python
template_dir = repo_root / "tests" / "data" / "experiment"

[str(path.relative_to(template_dir)) for path in template_dir.glob("*/*")]
```

```python
handler = JulesConfig(
    namelists="namelists",
    inputs={
        "path": "inputs",
        "handler": lambda: InputFilesConfig(
            initial_conditions="initial_conditions_bb219.dat",
            driving_data="Loobos_1997.dat",
            tile_fractions="tile_fractions.dat",
            )
    }
)
```

```python
config = handler.read(template_dir)
```

## Edit config and create new experiment

```python
print("current output period: ", config["namelists"]["output"]["jules_output_profile"]["output_period"])

config["namelists"]["output"]["jules_output_profile"]["output_period"] = 3600
print("new output period: ", config["namelists"]["output"]["jules_output_profile"]["output_period"])
```

```python
new_dir = Path("new_experiment")

handler.write(new_dir, config, overwrite_ok=True)

[str(path.relative_to(new_dir)) for path in new_dir.glob("*/*")]
```

```python
# Did the change get reflected?
! grep "output_period" {new_dir / "namelists" / "output.nml"}
```

## Run JULES

```python
# todo
```
