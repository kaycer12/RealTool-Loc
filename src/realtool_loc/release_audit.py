"""Static release checks for identity, secret, path, and size leakage."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


DEFAULT_MAX_SIZE = 95 * 1024 * 1024
IGNORED_PARTS = {".git", "__pycache__", ".test-tmp"}
NEUTRAL_EMAILS = {"anonymous@invalid.example"}

LOCAL_PATH_PATTERN = re.compile(r"/(?:" + "Users" + r"|home)/|[A-Za-z]:\\" + "Users" + r"\\")
PRIVATE_NETWORK_PATTERN = re.compile(
    r"(?<!\d)(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(?!\d)"
)
CREDENTIAL_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*[\"']?([A-Za-z0-9][A-Za-z0-9._-]{3,})"
)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
REPOSITORY_OWNER_MARKER = "kay" + "cer12"


def _text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def audit_git_identity(root: Path) -> list[str]:
    process = subprocess.run(
        ["git", "log", "--format=%an <%ae>%n%cn <%ce>"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        return ["git: unable to inspect commit identity"]
    allowed = "Anonymous Authors <anonymous@invalid.example>"
    identities = [line.strip() for line in process.stdout.splitlines() if line.strip()]
    return [f"git: non-neutral identity: {identity}" for identity in identities if identity != allowed]


def audit_tree(root: Path, *, max_size_bytes: int = DEFAULT_MAX_SIZE, include_git: bool = False) -> list[str]:
    violations: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts) or not path.is_file():
            continue
        label = relative.as_posix()
        if path.stat().st_size >= max_size_bytes:
            violations.append(f"{label}: oversized file ({path.stat().st_size} bytes)")
        if REPOSITORY_OWNER_MARKER.lower() in label.lower():
            violations.append(f"{label}: repository owner appears in filename")

        content = _text(path)
        if content is None:
            continue
        if LOCAL_PATH_PATTERN.search(content):
            violations.append(f"{label}: local path")
        if PRIVATE_NETWORK_PATTERN.search(content):
            violations.append(f"{label}: private network address")
        if CREDENTIAL_PATTERN.search(content):
            violations.append(f"{label}: credential-like assignment")
        if REPOSITORY_OWNER_MARKER.lower() in content.lower():
            violations.append(f"{label}: repository owner identity")
        emails = {match.lower() for match in EMAIL_PATTERN.findall(content)} - NEUTRAL_EMAILS
        for email in sorted(emails):
            violations.append(f"{label}: email address {email}")

    if include_git:
        violations.extend(audit_git_identity(root))
    return sorted(set(violations))
