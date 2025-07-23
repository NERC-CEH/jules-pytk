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

from jules_pytk.config import JulesConfig, JulesNamelists, JulesInput
```

```python
# get repo root
import subprocess

res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)

repo_root = Path(res.stdout.strip())

repo_root
```

```python
existing_experiment = repo_root / "tests" / "data" / "experiment"

config = JulesConfig.read(existing_experiment)

config.path
```

```python
config = config.detach()

config.path is None
```

## Create new experiment

```python
new_experiment = Path.cwd() / "new_experiment"

! ls {new_experiment}

config.write(new_experiment, overwrite=True)  # set overwrite=True if necessary

! ls {new_experiment}

del config

new_config = JulesConfig.read(new_experiment)
```

### Edit a namelist

```python
! grep "output_period" {new_experiment / "namelists" / "output.nml"}

# Alternative ways of accessing the namelist parameters
new_config.namelists[("output", "jules_output_profile", "output_period")], \
new_config.namelists.get("output", "jules_output_profile", "output_period")
```

```python
new_config.namelists.update({"output": {"jules_output_profile": {"output_period": 3600}}})

! grep "output_period" {new_experiment / "namelists" / "output.nml"}

new_config.namelists[("output", "jules_output_profile", "output_period")], \
new_config.namelists.get("output", "jules_output_profile", "output_period")
```

```python
# Did this get reflected in the file?

! grep "output_period" {new_experiment / "namelists" / "output.nml"}
```

```python

```
