"""
Utility functions for language pack operations.
Handles file copying, encoding conversion, and path management.
"""

import os
import shutil
import re
from pathlib import Path
from typing import Optional, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_properties_encoding(content: str) -> str:
    """
    Convert UTF-8 properties file content to Java native-to-ascii format.
    Non-ASCII characters are converted to \\uXXXX escape sequences.

    Args:
        content: UTF-8 encoded properties file content

    Returns:
        Properties file content with escaped Unicode characters
    """
    result = []
    for line in content.splitlines():
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            result.append(line)
            continue

        # Convert non-ASCII characters to \uXXXX format
        escaped_line = ''
        for char in line:
            if ord(char) > 127:
                escaped_line += f'\\u{ord(char):04x}'
            else:
                escaped_line += char
        result.append(escaped_line)

    return '\n'.join(result)


def copy_file_with_encoding(src: Path, dest: Path, convert_encoding: bool = False) -> bool:
    """
    Copy a file from source to destination, optionally converting encoding.

    Args:
        src: Source file path
        dest: Destination file path
        convert_encoding: If True, convert UTF-8 to Java properties format

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create destination directory if it doesn't exist
        dest.parent.mkdir(parents=True, exist_ok=True)

        if convert_encoding and src.suffix == '.properties':
            # Read UTF-8 content and convert
            with open(src, 'r', encoding='utf-8') as f:
                content = f.read()

            converted_content = convert_properties_encoding(content)

            with open(dest, 'w', encoding='utf-8') as f:
                f.write(converted_content)
        else:
            # Direct copy
            shutil.copy2(src, dest)

        logger.debug(f"Copied: {src} -> {dest}")
        return True
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dest}: {e}")
        return False


def copy_directory_tree(
    src_dir: Path,
    dest_dir: Path,
    pattern: Optional[str] = None,
    convert_encoding: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> tuple[int, int]:
    """
    Copy directory tree from source to destination with optional filtering.

    Args:
        src_dir: Source directory
        dest_dir: Destination directory
        pattern: Optional glob pattern to filter files (e.g., '*.properties')
        convert_encoding: If True, convert properties file encoding
        progress_callback: Optional callback function(copied, total)

    Returns:
        Tuple of (successful_copies, total_files)
    """
    if not src_dir.exists():
        logger.warning(f"Source directory does not exist: {src_dir}")
        return 0, 0

    # Collect all files to copy
    if pattern:
        files_to_copy = list(src_dir.rglob(pattern))
    else:
        files_to_copy = [f for f in src_dir.rglob('*') if f.is_file()]

    total = len(files_to_copy)
    copied = 0

    for i, src_file in enumerate(files_to_copy):
        # Calculate relative path
        rel_path = src_file.relative_to(src_dir)
        dest_file = dest_dir / rel_path

        if copy_file_with_encoding(src_file, dest_file, convert_encoding):
            copied += 1

        if progress_callback:
            progress_callback(i + 1, total)

    return copied, total


def remove_language_files(
    target_dir: Path,
    language_code: str,
    pattern: Optional[str] = None
) -> int:
    """
    Remove language-specific files from target directory.

    Args:
        target_dir: Target directory to clean
        language_code: Language code (e.g., 'ru', 'pt_PT')
        pattern: Optional pattern (default: messages_{lang}.properties)

    Returns:
        Number of files removed
    """
    if not target_dir.exists():
        logger.warning(f"Target directory does not exist: {target_dir}")
        return 0

    if pattern is None:
        pattern = f'*_{language_code}.properties'

    removed = 0
    for file_path in target_dir.rglob(pattern):
        try:
            file_path.unlink()
            logger.debug(f"Removed: {file_path}")
            removed += 1
        except Exception as e:
            logger.error(f"Failed to remove {file_path}: {e}")

    return removed


def get_pentaho_directories(base_dir: Optional[Path] = None) -> dict:
    """
    Get standard Pentaho installation directories.

    Args:
        base_dir: Optional base Pentaho directory, auto-detected if None

    Returns:
        Dictionary with keys: 'system', 'tomcat', 'plugin'
    """
    if base_dir is None:
        # Try to auto-detect from environment or common locations
        env_var = os.environ.get('PENTAHO_INSTALLED_LICENSE_PATH')
        if env_var:
            base_dir = Path(env_var).parent
        else:
            # Default to relative paths assuming plugin is installed
            base_dir = Path('/opt/pentaho/pentaho-server')

    base_dir = Path(base_dir)

    return {
        'system': base_dir / 'pentaho-solutions' / 'system',
        'tomcat': base_dir / 'tomcat' / 'webapps' / 'pentaho',
        'plugin': base_dir / 'pentaho-solutions' / 'system' / 'languagePackInstaller'
    }


def validate_pentaho_installation(directories: dict) -> bool:
    """
    Validate that Pentaho directories exist.

    Args:
        directories: Dictionary from get_pentaho_directories()

    Returns:
        True if valid installation found
    """
    system_dir = Path(directories['system'])
    return system_dir.exists() and (system_dir / 'pentaho.xml').exists()
