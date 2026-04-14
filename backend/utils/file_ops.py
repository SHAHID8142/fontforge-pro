"""
Safe file operations — move, rename with conflict resolution and logging.
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def safe_move(source: Path, target: Path, log_func=None) -> Path:
    """
    Move a file safely. Creates target directory if needed.

    Args:
        source: Source file path.
        target: Destination file path.
        log_func: Optional callback for logging the operation.

    Returns:
        The target path.
    """
    source = Path(source)
    target = Path(target)

    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    # Create target directory if needed
    target.parent.mkdir(parents=True, exist_ok=True)

    # Handle name conflicts
    target = resolve_conflicts(target)

    logger.info(f"Move: {source.name} → {target}")
    shutil.move(str(source), str(target))

    if log_func:
        log_func("move", str(source), str(target))

    return target


def resolve_conflicts(target: Path) -> Path:
    """If target exists, append _1, _2, etc."""
    if not target.exists():
        return target

    counter = 1
    stem = target.stem
    suffix = target.suffix
    parent = target.parent

    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def safe_rename(source: Path, new_name: str, log_func=None) -> Path:
    """
    Rename a file safely.

    Args:
        source: Source file path.
        new_name: New filename.
        log_func: Optional callback for logging the operation.

    Returns:
        The new file path.
    """
    source = Path(source)
    target = source.parent / new_name
    target = resolve_conflicts(target)

    logger.info(f"Rename: {source.name} → {target.name}")
    shutil.move(str(source), str(target))

    if log_func:
        log_func("rename", str(source), str(target))

    return target
