"""Install a checksum-pinned trusted analyzer, never repository dependencies."""

import hashlib
import shutil
import subprocess
import urllib.request
from pathlib import Path

URL = "https://repo.maven.apache.org/maven2/com/github/mauricioaniche/ck/0.7.0/ck-0.7.0-jar-with-dependencies.jar"
SHA256 = "2ddfdc275b6b59c2033e03253c4fec511c338fe494a10b70f651bc039a72c74d"


def install() -> None:
    root = Path(__file__).resolve().parent
    jar = root / "ck.jar"
    if not jar.exists():
        with urllib.request.urlopen(URL, timeout=60) as response:
            data = response.read(20 * 1048576)
        if hashlib.sha256(data).hexdigest() != SHA256:
            raise RuntimeError("CK checksum mismatch")
        jar.write_bytes(data)
    if hashlib.sha256(jar.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError("CK checksum mismatch")
    compiler = shutil.which("javac")
    if compiler is None:
        raise RuntimeError("Install a JDK (Java 17 recommended) before preparing CK")
    subprocess.run(
        [compiler, "--release", "17", "-cp", str(jar), str(root / "KagexCK.java")],
        cwd=root,
        check=True,
        timeout=60,
    )


if __name__ == "__main__":
    install()
