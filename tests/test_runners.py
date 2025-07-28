# WIP
from jules_pytk.runners import JulesExeRunner, JulesUdockerRunner


def _test_exe():
    jules_exe = (
        "/home/joe/github.com/NERC-CEH/portable-jules/_build/build/bin/jules.exe"
    )
    jules = JulesExeRunner(jules_exe)

    jules(namelists_dir="loobos/config", run_dir="loobos")


def _test_udocker():
    container_name = "jules"

    jules = JulesUdockerRunner(container_name)

    jules(namelists_dir="loobos/config", run_dir="loobos")
