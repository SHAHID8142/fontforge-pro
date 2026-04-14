"""
File hashing utilities — SHA256 and quick hash for duplicate detection.
"""

import hashlib


def compute_sha256(file_path) -> str:
    """
    Compute full SHA256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_quick_hash(file_path, max_bytes: int = 1_048_576) -> str:
    """
    Compute SHA256 hash of the first N bytes of a file (default: 1MB).

    Used for fast initial duplicate detection before full hash.

    Args:
        file_path: Path to the file.
        max_bytes: Maximum bytes to read (default 1MB).

    Returns:
        Hex digest string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        data = f.read(max_bytes)
        sha256.update(data)
    return sha256.hexdigest()
