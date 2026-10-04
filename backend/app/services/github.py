"""Only public GitHub archives from one fixed HTTPS host; no git subprocesses."""

import re
from pathlib import Path
from urllib.parse import urlsplit

import httpx2

from app.core.config import Settings
from app.core.errors import APIError
from app.services.storage import MIB, check_deadline


def parse_github_url(value: str) -> tuple[str, str]:
    if any(ord(character) <= 32 for character in value) or "\\" in value:
        raise APIError(
            400, "GITHUB_URL_INVALID", "Use https://github.com/owner/repository."
        )
    try:
        url = urlsplit(value)
    except ValueError as error:
        raise APIError(
            400, "GITHUB_URL_INVALID", "Use https://github.com/owner/repository."
        ) from error
    path = url.path.removesuffix("/")
    parts = path.split("/")
    if (
        url.scheme != "https"
        or url.netloc.lower() != "github.com"
        or url.query
        or url.fragment
        or len(parts) != 3
        or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", parts[1])
        or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", parts[2])
    ):
        raise APIError(
            400, "GITHUB_URL_INVALID", "Use https://github.com/owner/repository."
        )
    owner, repo = parts[1], parts[2].removesuffix(".git")
    if repo in {"", ".", ".."}:
        raise APIError(
            400, "GITHUB_URL_INVALID", "Use https://github.com/owner/repository."
        )
    return owner, repo


def download_github(
    owner: str, repo: str, destination: Path, settings: Settings, deadline: float
) -> None:
    # Inputs must have passed parse_github_url; redirects and proxy env are disabled.
    url = f"https://codeload.github.com/{owner}/{repo}/zip/HEAD"
    try:
        with httpx2.Client(
            timeout=5, follow_redirects=False, trust_env=False
        ) as client:
            with client.stream(
                "GET", url, headers={"Accept-Encoding": "identity"}
            ) as response:
                if response.status_code != 200:
                    raise APIError(
                        400,
                        "GITHUB_UNAVAILABLE",
                        "A public GitHub repository could not be downloaded.",
                    )
                length = response.headers.get("content-length")
                if length and (
                    not length.isdecimal()
                    or int(length) > settings.max_upload_size_mb * MIB
                ):
                    raise APIError(
                        413,
                        "UPLOAD_TOO_LARGE",
                        "The repository exceeds the download limit.",
                    )
                size = 0
                with destination.open("xb") as output:
                    for chunk in response.iter_raw():
                        check_deadline(deadline)
                        size += len(chunk)
                        if size > settings.max_upload_size_mb * MIB:
                            raise APIError(
                                413,
                                "UPLOAD_TOO_LARGE",
                                "The repository exceeds the download limit.",
                            )
                        output.write(chunk)
    except httpx2.HTTPError as error:
        raise APIError(
            502, "GITHUB_UNAVAILABLE", "The GitHub download failed. Try again later."
        ) from error
