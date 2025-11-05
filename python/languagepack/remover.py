"""
Language pack remover.
Handles removal of language packs from Pentaho BI Server.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from .metadata import LanguagePackMetadata
from .utils import remove_language_files, get_pentaho_directories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LanguagePackRemover:
    """Handles language pack removal operations."""

    def __init__(
        self,
        plugin_dir: str,
        pentaho_base_dir: Optional[str] = None
    ):
        """
        Initialize the remover.

        Args:
            plugin_dir: Path to the language pack plugin directory
            pentaho_base_dir: Path to Pentaho installation (auto-detected if None)
        """
        self.plugin_dir = Path(plugin_dir)
        self.data_dir = self.plugin_dir / "data"

        # Get Pentaho directories
        self.directories = get_pentaho_directories(
            Path(pentaho_base_dir) if pentaho_base_dir else None
        )

        # Initialize metadata handler
        self.metadata_handler = LanguagePackMetadata(plugin_dir)

    def remove_language_pack(
        self,
        language_code: str
    ) -> Dict[str, Any]:
        """
        Remove a language pack.

        Args:
            language_code: ISO language code (e.g., 'ru', 'pt_PT')

        Returns:
            Dictionary with removal results:
            {
                'success': bool,
                'language_code': str,
                'message': str,
                'files_removed': int,
                'errors': list
            }
        """
        result = {
            'success': False,
            'language_code': language_code,
            'message': '',
            'files_removed': 0,
            'errors': []
        }

        # Get metadata
        metadata = self.metadata_handler.get_metadata(language_code)
        if not metadata:
            result['message'] = f"Language pack '{language_code}' not found"
            result['errors'].append(f"No metadata.json found for {language_code}")
            return result

        logger.info(f"Removing language pack: {metadata.get('language', language_code)}")

        total_removed = 0

        try:
            # Remove from system plugins
            system_dir = self.directories['system']
            if system_dir.exists():
                removed = remove_language_files(
                    system_dir,
                    language_code,
                    pattern=f'*_{language_code}.properties'
                )
                total_removed += removed
                logger.info(f"System plugins: {removed} files removed")

                # Also remove JavaScript i18n files
                js_removed = remove_language_files(
                    system_dir,
                    language_code,
                    pattern=f'**/nls/{language_code}/**'
                )
                total_removed += js_removed
                logger.info(f"JavaScript i18n: {js_removed} files removed")

            # Remove from Tomcat resources
            tomcat_dir = self.directories['tomcat']
            if tomcat_dir.exists():
                removed = remove_language_files(
                    tomcat_dir,
                    language_code,
                    pattern=f'*_{language_code}.properties'
                )
                total_removed += removed
                logger.info(f"Tomcat resources: {removed} files removed")

            result['success'] = True
            result['files_removed'] = total_removed
            result['message'] = f"Successfully removed {metadata.get('language', language_code)} language pack ({total_removed} files)"

            logger.info(f"Removal completed: {total_removed} files removed")

        except Exception as e:
            error_msg = f"Removal failed: {str(e)}"
            logger.error(error_msg)
            result['message'] = error_msg
            result['errors'].append(str(e))

        return result

    def remove_all_language_packs(self) -> Dict[str, Any]:
        """
        Remove all installed language packs.

        Returns:
            Dictionary with removal results for all languages
        """
        results = {
            'success': True,
            'languages_removed': [],
            'total_files_removed': 0,
            'errors': []
        }

        # Get all available languages
        languages = self.metadata_handler.list_available_languages()

        for lang_code in languages.keys():
            result = self.remove_language_pack(lang_code)

            if result['success']:
                results['languages_removed'].append(lang_code)
                results['total_files_removed'] += result['files_removed']
            else:
                results['success'] = False
                results['errors'].extend(result['errors'])

        return results
