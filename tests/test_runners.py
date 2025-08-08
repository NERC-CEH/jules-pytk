from pathlib import Path

from jules_tools.runners import JulesExeRunner, JulesUdockerRunner


def test_exe():
    jules_exe = (
        "/home/joe/github.com/NERC-CEH/portable-jules/_build/build/bin/jules.exe"
    )
    jules = JulesExeRunner(jules_exe)

    jules(exec_dir=Path(__file__).parent / "data" / "experiment", namelists_subdir="namelists")


def _test_udocker():
    container_name = "jules"

    jules = JulesUdockerRunner(container_name)

    jules(namelists_dir="loobos/config", run_dir="loobos")
