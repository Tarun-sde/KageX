"""Bound trusted child processes; never invoke an uploaded executable or shell."""

import os
import signal
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryFile

from app.analyzers.contracts import AnalysisFailure
from app.core.config import Settings


def run_tool(
    arguments: list[str], cwd: Path, settings: Settings, deadline: float
) -> bytes:
    limit = min(deadline, time.monotonic() + settings.analyzer_timeout_seconds)
    # Deliberately omit PYTHONPATH, NODE_OPTIONS, CLASSPATH, JAVA_TOOL_OPTIONS,
    # credentials, and project configuration from the child environment.
    environment = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "HOME": str(cwd),
        "TMPDIR": str(cwd),
    }
    with TemporaryFile() as output, TemporaryFile() as errors:
        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-I",
                    str(Path(__file__).with_name("launcher.py")),
                    str(settings.max_analyzer_output_bytes),
                    str(settings.analyzer_timeout_seconds + 1),
                    *arguments,
                ],
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=errors,
                start_new_session=True,
            )
        except OSError as error:
            raise AnalysisFailure(
                "ANALYZER_UNAVAILABLE", "A required static analyzer is unavailable."
            ) from error
        try:
            while process.poll() is None:
                if time.monotonic() >= limit:
                    raise AnalysisFailure(
                        "ANALYZER_TIMEOUT", "A static analyzer exceeded its time limit."
                    )
                if (
                    max(
                        os.fstat(output.fileno()).st_size,
                        os.fstat(errors.fileno()).st_size,
                    )
                    > settings.max_analyzer_output_bytes
                ):
                    raise AnalysisFailure(
                        "ANALYZER_OUTPUT_LIMIT",
                        "Static analyzer output exceeded the limit.",
                    )
                time.sleep(0.025)
            if process.returncode != 0:
                raise AnalysisFailure(
                    "ANALYZER_FAILED", "A static analyzer could not finish."
                )
            output.seek(0)
            data = output.read(settings.max_analyzer_output_bytes + 1)
            if len(data) > settings.max_analyzer_output_bytes:
                raise AnalysisFailure(
                    "ANALYZER_OUTPUT_LIMIT",
                    "Static analyzer output exceeded the limit.",
                )
            return data
        finally:
            if process.poll() is None:
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
            process.wait()
