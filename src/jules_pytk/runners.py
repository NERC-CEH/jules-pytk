import logging
import os
from os import PathLike
import pathlib
import shutil
import subprocess

from .utils import switch_dir

log = logging.getLogger(__name__)


class JulesRuntimeError(Exception):
    pass


class InvalidPath(Exception):
    pass


class UdockerError(Exception):
    pass


class JulesExeRunner:
    """
    Run a JULES binary executable in a shell subprocess.

    Parameters:
      jules_exe: Path to a jules executable.
    """

    def __init__(self, jules_exe: str | PathLike | None = None) -> None:
        # If path to executable provided, check it exists, is a file, and is executable
        if jules_exe is not None:
            jules_exe = pathlib.Path(jules_exe).resolve()
            if not jules_exe.is_file():
                raise FileNotFoundError(f"Provided path '{jules_exe}' is not a file")
            if not os.access(jules_exe, os.X_OK):
                raise PermissionError(f"Provided file '{jules_exe}' is not executable")

        # If path to executable not provided, attempt to locate it in $PATH
        else:
            jules_exe = shutil.which("jules.exe")
            if jules_exe is None:
                raise FileNotFoundError(
                    "Jules executable `jules.exe` was not found in PATH"
                )
            jules_exe = pathlib.Path(jules_exe).resolve()

        self._jules_exe = jules_exe

    @property
    def jules_exe(self) -> pathlib.Path:
        return self._jules_exe

    def __str__(self) -> str:
        return f"{type(self).__name__}(jules_exe={self.jules_exe})"

    def __call__(
        self, namelists_dir: str | PathLike, run_dir: str | PathLike | None = None
    ) -> None:
        """
        Run the JULES binary.

        Standard output and error are redirected to files `stdout.log` and `stderr.log`.

        Args:
          namelists_dir: Path to the directory containing the namelists.
          run_dir: Path to the directory in which the jules executable will be run.
        """
        namelists_dir = pathlib.Path(namelists_dir).resolve()
        run_dir = namelists_dir if run_dir is None else pathlib.Path(run_dir).resolve()

        # TODO: When API for namelists/config is stable.
        # Read output namelist and automatically create output directory
        # output_path = Path(config.output.get("jules_output").get("output_dir"))
        # if not output_path.is_absolute():
        #     output_path = exec_path / output_path
        # output_path.mkdir(exist_ok=overwrite, parents=True)

        with switch_dir(run_dir, verbose=True):
            stdout_file = "stdout.log"
            stderr_file = "stderr.log"

            log.info("Logging to %s and %s" % (stdout_file, stderr_file))

            with open(stdout_file, "w") as outfile, open(stderr_file, "w") as errfile:
                log.info("Running %s %s" % (self.jules_exe, namelists_dir))

                try:
                    subprocess.run(
                        args=[self.jules_exe, namelists_dir],
                        stdout=outfile,
                        stderr=errfile,
                        text=True,
                        check=True,
                    )

                except subprocess.CalledProcessError as exc:
                    log.error(
                        "An error was thrown by the subprocess. See details in %s."
                        % stderr_file
                    )

                    # TODO: fix this - errfile is not readable.
                    #errfile_contents = errfile.read()
                    #raise JulesRuntimeError(errfile_contents) from exc

                    raise JulesRuntimeError("An error was thrown by the subprocess. See details in stderr.log") from exc


class JulesUdockerRunner:
    """
    Run an existing JULES docker container using udocker.

    Parameters:
      container_name: name of an _existing_ JULES container.
      mount_point: an _absolute_ path in the container for mounting the run directory.

    Notes:
      List the containers udocker knows about using `udocker ps`
    """

    def __init__(
        self, container_name: str, mount_point: str | PathLike = "/root/run"
    ) -> None:
        # Check valid name (possibly overkill)
        try:
            subprocess.run(
                ["udocker", "inspect", container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            # If container doesn't exist, run
            subprocess.run(["udocker", "ps"])
            raise UdockerError(exc.stderr) from exc

        mount_point = pathlib.Path(mount_point)
        if not mount_point.is_absolute():
            raise InvalidPath("mount point must be an absolute path")

        self._container_name = container_name
        self._mount_point = mount_point

    @property
    def container_name(self) -> str:
        return self._container_name

    @property
    def mount_point(self) -> pathlib.Path:
        return self._mount_point

    def __str__(self) -> str:
        return f"{type(self).__name__}(container_name={self.container_name}, mount_point={self.mount_point})"

    def __call__(
        self, namelists_dir: str | PathLike, run_dir: str | PathLike | None = None
    ) -> None:
        """
        Run a containerised version of JULES.

        Args:
          namelists_dir: Path to the directory containing the namelists.
          run_dir: Path to the directory in which the jules executable will be run. This must be a parent of `namelists_dir`!
        """
        namelists_dir = pathlib.Path(namelists_dir).resolve()
        run_dir = namelists_dir if run_dir is None else pathlib.Path(run_dir).resolve()

        # We will mount `run_dir` to /root/run. Hence, `namelists_dir` must be a
        # subdirectory of `run_dir` or it will not be mounted.
        if not (namelists_dir.is_relative_to(run_dir)):
            msg = "`namelists_dir` must either be a subdirectory of `run_dir` or the same directory."
            raise InvalidPath(msg)

        subprocess.run(
            [
                "udocker",
                "run",
                "-v",
                f"{run_dir}:{self.mount_point}",
                self.container_name,
                "-d",
                self.mount_point,
                self.mount_point / namelists_dir.relative_to(run_dir),
            ],
        )
