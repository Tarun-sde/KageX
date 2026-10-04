"""Linux resource boundary for KageX-owned analyzer executables only."""

import ctypes
import os
import resource
import signal
import sys

if __name__ == "__main__":
    parent = os.getppid()
    # The analyzer dies with its Celery parent even if the worker is SIGKILLed.
    if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
        raise RuntimeError("Analyzer parent-death protection unavailable")
    if parent == 1 or os.getppid() != parent:
        sys.exit(1)
    output, seconds = int(sys.argv[1]), int(sys.argv[2])
    resource.setrlimit(resource.RLIMIT_FSIZE, (output, output))
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.execve(sys.argv[3], sys.argv[3:], os.environ)
