import logging
from os import PathLike
from pathlib import Path
import shutil
import subprocess

from .config import read_config
from .utils import switch_dir

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class JulesRuntimeError(Exception):
    pass


def run_jules(
    config_path: str | PathLike,
    exec_path: str | PathLike,
    jules_exe: str | PathLike | None = None,
    overwrite: bool = False,
) -> None:
    """Runs JULES.

    This is essentially a wrapper around `subprocess.run('jules.exe <config_path>')`.

    However, `stdout` and `stderr` are redirected to files `stdout.log` and `stderr.log`.

    Parameters
    ----------
    config_path:
        Path to the namelist directory.
    exec_path:
        Path to the directory in which JULES should be run.
    jules_exe:
        Path to a JULES executable, which defaults to `which jules.exe`.
    overwrite:
        If True, overwrites an existing output directory.
    """

    if jules_exe is None:
        jules_exe = shutil.which("jules.exe")
        if jules_exe is None:
            raise FileNotFoundError(
                "Jules executable `jules.exe` could not be automatically detected"
            )

    config_path = Path(config_path).resolve()
    config = read_config(config_path)

    exec_path = Path(exec_path).resolve()

    output_path = Path(config.output.get("jules_output").get("output_dir"))
    if not output_path.is_absolute():
        output_path = exec_path / output_path
    output_path.mkdir(exist_ok=overwrite, parents=True)

    with switch_dir(exec_path, verbose=True):

        stdout_file = "stdout.log"
        stderr_file = "stderr.log"

        log.info("Logging to %s and %s" % (stdout_file, stderr_file))

        with open(stdout_file, "w") as outfile, open(stderr_file, "w") as errfile:

            log.info("Running %s %s" % (jules_exe, config_path))

            try:
                subprocess.run(
                    args=[str(jules_exe), str(config_path)],
                    stdout=outfile,
                    stderr=errfile,
                    text=True,
                    check=True,
                )

            except subprocess.CalledProcessError as exc:
                log.error(
                    "An error was thrown by the subprocess. Reading details from %s."
                    % stderr_file
                )

                with open(stderr_file, "r") as errfile:
                    stderr = errfile.read()

                raise JulesRuntimeError(stderr) from exc
