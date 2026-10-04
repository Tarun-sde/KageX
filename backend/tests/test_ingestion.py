import io
import stat
import struct
import time
import zipfile
from collections.abc import Sequence
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx2
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import APIError
from app.services.github import download_github, parse_github_url
from app.services.storage import Storage, extract_archive
from tests.conftest import project, register


def archive(
    entries: Sequence[tuple[str | zipfile.ZipInfo, bytes]],
    compression: int = zipfile.ZIP_STORED,
) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as zipped:
        for name, data in entries:
            zipped.writestr(name, data)
    return output.getvalue()


def extract(data: bytes, settings: Settings, tmp_path: Path) -> tuple[int, int]:
    path = tmp_path / "archive.zip"
    path.write_bytes(data)
    return extract_archive(path, tmp_path / "out", settings, time.monotonic() + 5)


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/absolute",
        "C:/evil",
        "a\\evil",
        "a/../../escape",
        "a//b",
        "./evil",
        "a/./b",
        "control\x01file",
        "a/" * 33 + "deep",
        "x" * 513,
    ],
)
def test_unsafe_paths(name: str, settings: Settings, tmp_path: Path) -> None:
    with pytest.raises(APIError, match="unsafe path"):
        extract(archive([(name, b"inert")]), settings, tmp_path)
    assert not (tmp_path.parent / "escape").exists()


@pytest.mark.parametrize(
    "kind", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFSOCK]
)
def test_special_files(kind: int, settings: Settings, tmp_path: Path) -> None:
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = (kind | 0o777) << 16
    with pytest.raises(APIError, match="Links and special"):
        extract(archive([(info, b"/etc/passwd")]), settings, tmp_path)


@pytest.mark.parametrize(
    "entries",
    [
        [("A", b"1"), ("a", b"2")],
        [("a", b"1"), ("a/b", b"2")],
        [("a/b", b"1"), ("a", b"2")],
    ],
)
def test_conflicting_paths(
    entries: list[tuple[str | zipfile.ZipInfo, bytes]],
    settings: Settings,
    tmp_path: Path,
) -> None:
    with pytest.raises(APIError, match="conflicting paths"):
        extract(archive(entries), settings, tmp_path)


@pytest.mark.parametrize(
    "case,code",
    [
        ("empty", "INVALID_ARCHIVE"),
        ("malformed", "INVALID_ARCHIVE"),
        ("size", "UPLOAD_TOO_LARGE"),
        ("count", "TOO_MANY_FILES"),
        ("ratio", "COMPRESSION_RATIO_LIMIT"),
        ("file", "FILE_TOO_LARGE"),
        ("expanded", "EXTRACTED_SIZE_LIMIT"),
        ("forged_count", "TOO_MANY_FILES"),
        ("crc", "INVALID_ARCHIVE"),
    ],
)
def test_archive_limits(
    case: str, code: str, settings: Settings, tmp_path: Path
) -> None:
    data = archive([])
    if case == "malformed":
        data = b"not a zip"
    elif case == "size":
        data = b"x" * (1048576 + 1)
    elif case in {"count", "forged_count"}:
        data = archive([(str(index), b"x") for index in range(11)])
        if case == "forged_count":
            forged = bytearray(data)
            struct.pack_into("<HH", forged, len(forged) - 22 + 8, 1, 1)
            data = bytes(forged)
    elif case == "ratio":
        data = archive([("bomb", b"0" * 100000)], zipfile.ZIP_DEFLATED)
    elif case == "file":
        data = archive([("large", b"x" * (1048576 + 1))])
        settings.max_upload_size_mb = 2
    elif case == "expanded":
        settings.max_upload_size_mb = 4
        data = archive([(str(index), b"x" * 800000) for index in range(3)])
    elif case == "crc":
        data = archive([("test", b"UNIQUE_CONTENT")]).replace(
            b"UNIQUE_CONTENT", b"BROKEN_CONTENT"
        )
    with pytest.raises(APIError) as failure:
        extract(data, settings, tmp_path)
    assert failure.value.code == code


def test_encrypted_nul_and_unsupported(settings: Settings, tmp_path: Path) -> None:
    for index, data in enumerate(
        [
            archive([("aXb", b"x")]).replace(b"aXb", b"a\x00b"),
            archive([("a", b"x")], zipfile.ZIP_BZIP2),
        ]
    ):
        folder = tmp_path / str(index)
        folder.mkdir()
        with pytest.raises(APIError):
            extract(data, settings, folder)
    encrypted = bytearray(archive([("a", b"x")]))
    struct.pack_into("<H", encrypted, 6, 1)
    offset = encrypted.find(b"PK\x01\x02")
    struct.pack_into("<H", encrypted, offset + 8, 1)
    with pytest.raises(APIError, match="Encrypted"):
        extract(bytes(encrypted), settings, tmp_path)


def test_deadline(settings: Settings, tmp_path: Path) -> None:
    source = tmp_path / "upload.zip"
    source.write_bytes(archive([("file", b"safe")]))
    with pytest.raises(APIError) as failure:
        extract_archive(source, tmp_path / "out", settings, time.monotonic() - 1)
    assert failure.value.code == "INGESTION_TIMEOUT"


def test_upload_retry_isolation_delete_and_no_execution(
    client: TestClient, settings: Settings, tmp_path: Path
) -> None:
    register(client)
    identifier = project(client)
    base = f"/api/v1/projects/{identifier}"
    root = settings.project_storage_root
    failure = client.post(
        base + "/source/zip", content=archive([("../escape", b"bad")])
    )
    assert failure.status_code == 400
    assert client.get(base).json()["status"] == "FAILED"
    assert list((root / ".staging").iterdir()) == []
    assert not (root / identifier).exists()
    marker = tmp_path / "EXECUTED"
    payload = archive(
        [
            (
                "main.py",
                f"from pathlib import Path; Path({str(marker)!r}).touch()".encode(),
            ),
            ("nested.zip", archive([("../inert", b"x")])),
            ("image.bin", b"\x00\xff"),
            ("package.json", b'{"scripts":{"install":"touch EXECUTED"}}'),
        ]
    )
    response = client.post(base + "/source/zip", content=payload)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "READY"
    assert response.json()["file_count"] == 4
    assert str(root) not in response.text
    assert not marker.exists()
    assert (root / identifier / "nested.zip").is_file()
    assert (root / identifier / "main.py").stat().st_mode & 0o777 == 0o600
    assert list((root / ".staging").iterdir()) == []
    assert client.post(base + "/source/zip", content=payload).status_code == 409
    other = project(client)
    assert (
        client.post(f"/api/v1/projects/{other}/source/zip", content=payload).status_code
        == 200
    )
    assert client.delete(base).status_code == 204
    assert not (root / identifier).exists()
    assert (root / other).exists()
    assert list((root / ".trash").iterdir()) == []


def test_oversized_stream_failure_cleanup(
    client: TestClient, settings: Settings
) -> None:
    register(client)
    identifier = project(client)
    base = f"/api/v1/projects/{identifier}"
    response = client.post(
        base + "/source/zip", content=iter([b"x" * 700000, b"x" * 700000])
    )
    assert response.status_code == 413
    assert client.get(base).json()["status"] == "FAILED"
    assert list((settings.project_storage_root / ".staging").iterdir()) == []


def test_storage_failure_and_delete_rollback(
    client: TestClient, settings: Settings
) -> None:
    register(client)
    identifier = project(client)
    base = f"/api/v1/projects/{identifier}"
    with patch.object(Storage, "publish", side_effect=OSError("private path secret")):
        response = client.post(base + "/source/zip", content=archive([("safe", b"x")]))
    assert response.status_code == 503
    assert "secret" not in response.text
    assert client.get(base).json()["status"] == "FAILED"
    assert list((settings.project_storage_root / ".staging").iterdir()) == []
    assert (
        client.post(base + "/source/zip", content=archive([("safe", b"x")])).status_code
        == 200
    )
    storage = Storage(settings)
    with pytest.raises(RuntimeError), storage.deleting(UUID(identifier)):
        raise RuntimeError("transaction rollback")
    assert (storage.path(UUID(identifier)) / "safe").exists()
    malicious = uuid4()
    storage.path(malicious).symlink_to(settings.project_storage_root.parent)
    with pytest.raises(APIError):
        storage.remove(malicious)


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/a/b",
        "https://evil.com/a/b",
        "https://github.com.evil.com/a/b",
        "https://github.com@127.0.0.1/a/b",
        "file:///etc/passwd",
        "https://github.com:443/a/b",
        "https://github.com/a/b?token=secret",
        "https://github.com/a/b/tree/main",
        "https://github.com/a/%2e%2e",
        "https://github.com/a/..",
        "https://github.com/a/b#x",
        "https://github.com/a\\b",
        "https://[invalid/a/b",
    ],
)
def test_github_url_restriction(url: str) -> None:
    with pytest.raises(APIError):
        parse_github_url(url)


def test_github_normalization() -> None:
    assert parse_github_url("https://github.com/OpenAI/example.git/") == (
        "OpenAI",
        "example",
    )


@pytest.mark.parametrize(
    "status,headers,data,expected",
    [
        (302, {"Location": "http://127.0.0.1/secret"}, b"", "GITHUB_UNAVAILABLE"),
        (404, {}, b"", "GITHUB_UNAVAILABLE"),
        (200, {"Content-Length": "2000000"}, b"", "UPLOAD_TOO_LARGE"),
        (200, {}, b"x" * 1100000, "UPLOAD_TOO_LARGE"),
    ],
)
def test_github_download_limits(
    status: int,
    headers: dict[str, str],
    data: bytes,
    expected: str,
    settings: Settings,
    tmp_path: Path,
) -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(status, headers=headers, stream=httpx2.ByteStream(data))

    real_client = httpx2.Client
    with (
        patch(
            "app.services.github.httpx2.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx2.MockTransport(handler), **kwargs
            ),
        ),
        pytest.raises(APIError) as failure,
    ):
        download_github(
            "a", "b", tmp_path / "download.zip", settings, time.monotonic() + 5
        )
    assert failure.value.code == expected
    assert len(requests) == 1
    assert str(requests[0].url) == "https://codeload.github.com/a/b/zip/HEAD"


def test_github_shared_pipeline(client: TestClient, settings: Settings) -> None:
    register(client)
    identifier = project(client, "GITHUB")
    base = f"/api/v1/projects/{identifier}"
    assert client.post(base + "/source/zip", content=b"x").status_code == 400
    with patch("app.api.projects.download_github") as download:
        download.side_effect = lambda owner, repo, destination, settings, deadline: (
            destination.write_bytes(archive([("repo-main/README.md", b"safe")]))
        )
        response = client.post(
            base + "/source/github", json={"url": "https://github.com/a/b.git"}
        )
    assert response.status_code == 200, response.text
    assert response.json()["github_url"] == "https://github.com/a/b"
    assert response.json()["status"] == "READY"
    assert (
        settings.project_storage_root / identifier / "repo-main/README.md"
    ).read_bytes() == b"safe"


def test_central_directory_offset_cannot_hide_unchecked_headers(
    settings: Settings, tmp_path: Path
) -> None:
    data = archive([("safe", b"x")])
    central = data[data.find(b"PK\x01\x02") : -22]
    # ZipFile compensates for prepended bytes by moving the central directory;
    # reject this layout so it can only allocate the directory we inspected.
    forged = data[:-22] + central + data[-22:]
    with pytest.raises(APIError) as failure:
        extract(forged, settings, tmp_path)
    assert failure.value.code == "INVALID_ARCHIVE"


def test_download_timeout_persists_failure_and_allows_retry(
    client: TestClient, settings: Settings
) -> None:
    register(client)
    identifier = project(client, "GITHUB")
    url = f"/api/v1/projects/{identifier}/source/github"
    with patch(
        "app.services.github.httpx2.Client",
        side_effect=httpx2.ReadTimeout("secret URL"),
    ):
        response = client.post(url, json={"url": "https://github.com/a/b"})
    assert response.status_code == 502
    assert "secret URL" not in response.text
    assert client.get(f"/api/v1/projects/{identifier}").json()["status"] == "FAILED"
    assert list((settings.project_storage_root / ".staging").iterdir()) == []
    with patch("app.api.projects.download_github") as download:
        download.side_effect = lambda owner, repo, destination, settings, deadline: (
            destination.write_bytes(archive([("main.py", b"# inert")]))
        )
        assert (
            client.post(url, json={"url": "https://github.com/a/b"}).status_code == 200
        )


def test_unavailable_storage_persists_failure(client: TestClient) -> None:
    register(client)
    identifier = project(client)
    base = f"/api/v1/projects/{identifier}"
    with patch.object(Storage, "staging", side_effect=OSError("secret path")):
        response = client.post(base + "/source/zip", content=b"unused")
    assert response.status_code == 503
    assert "secret path" not in response.text
    state = client.get(base).json()
    assert state["status"] == "FAILED"
    assert state["error_code"] == "STORAGE_UNAVAILABLE"


@pytest.mark.parametrize("failure", ["disconnect", "timeout"])
def test_interrupted_upload_cleanup(
    failure: str, client: TestClient, settings: Settings
) -> None:
    import asyncio
    from collections.abc import AsyncIterator

    from starlette.requests import ClientDisconnect, Request

    register(client)
    identifier = project(client)
    settings.ingestion_timeout_seconds = 1

    async def interrupted(request: Request) -> AsyncIterator[bytes]:
        yield b"partial"
        if failure == "disconnect":
            raise ClientDisconnect()
        await asyncio.sleep(2)

    base = f"/api/v1/projects/{identifier}"
    with patch.object(Request, "stream", interrupted):
        response = client.post(base + "/source/zip", content=b"unused")
    assert response.status_code == (503 if failure == "disconnect" else 408)
    assert client.get(base).json()["status"] == "FAILED"
    assert list((settings.project_storage_root / ".staging").iterdir()) == []
