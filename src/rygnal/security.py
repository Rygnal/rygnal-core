"""Security hardening helpers for Rygnal.

This module contains deterministic safety utilities used by the demo tool
adapters and core security checks.
"""

from __future__ import annotations

import ipaddress
import re
import shlex
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REDACTED = "[REDACTED]"

SENSITIVE_KEYWORDS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "credential",
    "authorization",
)

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)private[_-]?key"),
    re.compile(r"(?i)aws_access_key_id\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*[^\s,;]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
)

DANGEROUS_SHELL_TOKENS = {
    "rm",
    "sudo",
    "chmod",
    "chown",
    "mkfs",
    "dd",
    "nc",
    "netcat",
    "ssh",
    "scp",
    "curl",
    "wget",
    "python",
    "python3",
    "bash",
    "sh",
}

SHELL_METACHARACTERS = {";", "&&", "||", "|", "`", "$()", ">", ">>", "<"}

DEFAULT_ALLOWED_SHELL_COMMANDS = {"pwd", "ls", "cat", "echo"}
DEFAULT_ALLOWED_HTTP_HOSTS = {"example.com", "api.example.com"}


class SecurityViolation(ValueError):
    """Raised when a request violates a Rygnal safety boundary."""


def resolve_path_inside_sandbox(sandbox_path: str | Path, target: str | None) -> Path:
    """Resolve a target path and ensure it stays inside the sandbox."""
    if not target:
        raise SecurityViolation("Target path is required.")

    if "\x00" in target:
        raise SecurityViolation("Target path contains a null byte.")

    sandbox = Path(sandbox_path).resolve()
    candidate = (sandbox / target).resolve()

    if candidate != sandbox and sandbox not in candidate.parents:
        raise SecurityViolation("Target path is outside the allowed sandbox.")

    return candidate


def validate_shell_command(
    command_text: str,
    allowed_commands: set[str] | None = None,
) -> list[str]:
    """Validate a shell command using an allowlist and return parsed args."""
    allowed = allowed_commands or DEFAULT_ALLOWED_SHELL_COMMANDS

    if not command_text.strip():
        raise SecurityViolation("Shell command input is empty.")

    if any(token in command_text for token in SHELL_METACHARACTERS):
        raise SecurityViolation("Shell metacharacters are not allowed.")

    try:
        command_parts = shlex.split(command_text)
    except ValueError as exc:
        raise SecurityViolation(f"Invalid shell command: {exc}") from exc

    if not command_parts:
        raise SecurityViolation("Shell command input is empty.")

    command_name = command_parts[0]

    if command_name in DANGEROUS_SHELL_TOKENS and command_name not in allowed:
        raise SecurityViolation(f"Dangerous command is not allowed: {command_name}")

    if command_name not in allowed:
        raise SecurityViolation(f"Command not allowlisted: {command_name}")

    return command_parts


def validate_http_url(
    url: str,
    allowed_hosts: set[str] | None = None,
) -> str:
    """Validate an outbound HTTP URL using scheme, host, and private-IP checks."""
    allowed = allowed_hosts or DEFAULT_ALLOWED_HTTP_HOSTS

    parsed = urlparse(url)

    if parsed.scheme not in {"https"}:
        raise SecurityViolation("Only HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise SecurityViolation("URL hostname is required.")

    hostname = parsed.hostname.lower()

    if hostname not in allowed:
        raise SecurityViolation(f"Host is not allowlisted: {hostname}")

    if _is_private_or_local_host(hostname):
        raise SecurityViolation("Private or local network destinations are not allowed.")

    return url


def contains_secret(value: Any) -> bool:
    """Return True when a nested value appears to contain a secret."""
    if value is None:
        return False

    if isinstance(value, str):
        return any(pattern.search(value) for pattern in SECRET_PATTERNS)

    if isinstance(value, dict):
        if any(is_sensitive_key(key) for key in value):
            return True
        return any(contains_secret(item) for item in value.values())

    if isinstance(value, (list, tuple, set)):
        return any(contains_secret(item) for item in value)

    return False


def redact_sensitive_value(value: Any) -> Any:
    """Redact secrets from nested dict/list/string values."""
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            key: REDACTED if is_sensitive_key(key) else redact_sensitive_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [redact_sensitive_value(item) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_sensitive_value(item) for item in value)

    if isinstance(value, str):
        return redact_sensitive_string(value)

    return value


def is_sensitive_key(key: str) -> bool:
    """Return True when a key name looks sensitive."""
    normalized_key = key.lower().replace("-", "_")
    return any(keyword in normalized_key for keyword in SENSITIVE_KEYWORDS)


def redact_sensitive_string(value: str) -> str:
    """Redact common secret assignments inside strings."""
    redacted = value

    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(_redact_match, redacted)

    return redacted


def stringify(value: Any) -> str:
    """Convert nested values into a searchable string."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    return str(value)


def _redact_match(match: re.Match[str]) -> str:
    raw = match.group(0)

    if "=" in raw:
        key = raw.split("=", 1)[0].strip()
        return f"{key}={REDACTED}"

    if ":" in raw:
        key = raw.split(":", 1)[0].strip()
        return f"{key}: {REDACTED}"

    return REDACTED


def _is_private_or_local_host(hostname: str) -> bool:
    if hostname in {"localhost", "127.0.0.1"}:
        return True

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return False

    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified
