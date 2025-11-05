"""
Metadata handler for language packs.
Reads and validates metadata.json files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class LanguagePackMetadata:
    """Handles language pack metadata operations."""

    def __init__(self, plugin_dir: str):
        """
        Initialize metadata handler.

        Args:
            plugin_dir: Path to the plugin installation directory
        """
        self.plugin_dir = Path(plugin_dir)
        self.data_dir = self.plugin_dir / "data"

    def get_metadata(self, language_code: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific language pack.

        Args:
            language_code: ISO language code (e.g., 'ru', 'pt_PT')

        Returns:
            Dictionary containing metadata or None if not found
        """
        metadata_path = self.data_dir / language_code / "metadata.json"

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                metadata['languageCode'] = language_code
                return metadata
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Failed to read metadata for {language_code}: {e}")

    def list_available_languages(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available language packs.

        Returns:
            Dictionary mapping language codes to their metadata
        """
        languages = {}

        if not self.data_dir.exists():
            return languages

        for lang_dir in self.data_dir.iterdir():
            if lang_dir.is_dir():
                metadata = self.get_metadata(lang_dir.name)
                if metadata:
                    languages[lang_dir.name] = metadata

        return languages

    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate metadata structure.

        Args:
            metadata: Metadata dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['appTitle', 'language', 'languageCode']
        return all(field in metadata for field in required_fields)
