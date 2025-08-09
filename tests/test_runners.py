import importlib
from pathlib import Path

import pytest

from jules_tools.runners import JulesExeRunner, JulesUdockerRunner

jules_exe = Path(
        "/home/joe/github.com/NERC-CEH/portable-jules/_build/build/bin/jules.exe"
    )

@pytest.mark.skipif(not jules_exe.exists(), reason="Only run on developer's computers for now.")
def test_exe():
    jules = JulesExeRunner(jules_exe)

    jules(exec_dir=Path(__file__).parent / "data" / "experiment", namelists_subdir="namelists")

def udocker_installed() -> bool:
    try:
        _ = importlib.import_module("udocker")
        return True
    except ModuleNotFoundError:
        return False

@pytest.mark.skipif(not udocker_installed(), reason="udocker is not installed.")
def test_udocker():
    # TODO: run udocker.UdockerCLI.do_ps() and check that jules is an existing 
    # container before running this test?
    container_name = "jules"

    jules = JulesUdockerRunner(container_name)

    jules(exec_dir=Path(__file__).parent / "data" / "experiment", namelists_subdir="namelists")
