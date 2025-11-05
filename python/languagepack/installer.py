"""
Language pack installer.
Handles installation of language packs to Pentaho BI Server.
"""

import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from .metadata import LanguagePackMetadata
from .utils import (
    copy_directory_tree,
    get_pentaho_directories,
    validate_pentaho_installation
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LanguagePackInstaller:
    """Handles language pack installation operations."""

    def __init__(
        self,
        plugin_dir: str,
        pentaho_base_dir: Optional[str] = None,
        convert_encoding: bool = True
    ):
        """
        Initialize the installer.

        Args:
            plugin_dir: Path to the language pack plugin directory
            pentaho_base_dir: Path to Pentaho installation (auto-detected if None)
            convert_encoding: Whether to convert properties files to Java format
        """
        self.plugin_dir = Path(plugin_dir)
        self.data_dir = self.plugin_dir / "data"
        self.convert_encoding = convert_encoding

        # Get Pentaho directories
        self.directories = get_pentaho_directories(
            Path(pentaho_base_dir) if pentaho_base_dir else None
        )

        # Initialize metadata handler
        self.metadata_handler = LanguagePackMetadata(plugin_dir)

        # Validate installation
        if not validate_pentaho_installation(self.directories):
            logger.warning("Pentaho installation validation failed. Some operations may not work.")

    def install_language_pack(
        self,
        language_code: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Install a language pack.

        Args:
            language_code: ISO language code (e.g., 'ru', 'pt_PT')
            progress_callback: Optional callback function(stage, current, total)

        Returns:
            Dictionary with installation results:
            {
                'success': bool,
                'language_code': str,
                'message': str,
                'files_copied': int,
                'errors': list
            }
        """
        result = {
            'success': False,
            'language_code': language_code,
            'message': '',
            'files_copied': 0,
            'errors': []
        }

        # Get metadata
        metadata = self.metadata_handler.get_metadata(language_code)
        if not metadata:
            result['message'] = f"Language pack '{language_code}' not found"
            result['errors'].append(f"No metadata.json found for {language_code}")
            return result

        logger.info(f"Installing language pack: {metadata.get('language', language_code)}")

        lang_dir = self.data_dir / language_code
        total_copied = 0

        try:
            # Install system plugins
            system_src = lang_dir / "system"
            if system_src.exists():
                if progress_callback:
                    progress_callback("Installing system plugins", 0, 2)

                copied, total = copy_directory_tree(
                    system_src,
                    self.directories['system'],
                    convert_encoding=self.convert_encoding
                )
                total_copied += copied
                logger.info(f"System plugins: {copied}/{total} files copied")

            # Install Tomcat resources
            tomcat_src = lang_dir / "tomcat"
            if tomcat_src.exists():
                if progress_callback:
                    progress_callback("Installing Tomcat resources", 1, 2)

                # Handle JAR directory structure
                tomcat_dest = self.directories['tomcat']
                copied, total = self._install_tomcat_resources(tomcat_src, tomcat_dest)
                total_copied += copied
                logger.info(f"Tomcat resources: {copied}/{total} files copied")

            if progress_callback:
                progress_callback("Completed", 2, 2)

            result['success'] = True
            result['files_copied'] = total_copied
            result['message'] = f"Successfully installed {metadata.get('language', language_code)} language pack ({total_copied} files)"

            logger.info(f"Installation completed: {total_copied} files copied")

        except Exception as e:
            error_msg = f"Installation failed: {str(e)}"
            logger.error(error_msg)
            result['message'] = error_msg
            result['errors'].append(str(e))

        return result

    def _install_tomcat_resources(
        self,
        tomcat_src: Path,
        tomcat_dest: Path
    ) -> tuple[int, int]:
        """
        Install Tomcat resources, handling JAR directory structure.

        In the language pack, JAR contents are stored as directories like:
        tomcat/webapps/pentaho/WEB-INF/lib/pentaho-metadata_jar/...

        These need to be copied to:
        tomcat/webapps/pentaho/WEB-INF/lib/pentaho-metadata.jar (as JAR contents)

        For now, we'll copy them directly to allow overriding without JAR manipulation.
        A production version might want to inject into actual JAR files.
        """
        total_copied = 0
        total_files = 0

        lib_src = tomcat_src / "webapps" / "pentaho" / "WEB-INF" / "lib"
        if not lib_src.exists():
            return 0, 0

        lib_dest = tomcat_dest / "WEB-INF" / "lib"

        # For each _jar directory, copy contents
        for jar_dir in lib_src.iterdir():
            if jar_dir.is_dir() and jar_dir.name.endswith('_jar'):
                # Extract JAR name (remove _jar suffix)
                jar_name = jar_dir.name[:-4]  # Remove '_jar'

                # Copy properties files to a parallel directory structure
                # This allows Pentaho to load them without modifying JARs
                dest_dir = lib_dest / jar_name

                copied, total = copy_directory_tree(
                    jar_dir,
                    dest_dir,
                    convert_encoding=self.convert_encoding
                )
                total_copied += copied
                total_files += total

        return total_copied, total_files

    def get_installed_languages(self) -> list[str]:
        """
        Get list of currently installed language codes.

        This checks for the presence of language-specific files in the system.

        Returns:
            List of installed language codes
        """
        installed = set()
        system_dir = self.directories['system']

        if not system_dir.exists():
            return []

        # Check for language-specific properties files
        for properties_file in system_dir.rglob('messages_*.properties'):
            # Extract language code from filename
            # Format: messages_ru.properties or messages_pt_PT.properties
            name = properties_file.stem
            if name.startswith('messages_'):
                lang_code = name[9:]  # Remove 'messages_' prefix
                if lang_code and lang_code not in ['en', 'en_US']:
                    installed.add(lang_code)

        return sorted(list(installed))

    def is_language_installed(self, language_code: str) -> bool:
        """
        Check if a specific language pack is installed.

        Args:
            language_code: Language code to check

        Returns:
            True if installed, False otherwise
        """
        return language_code in self.get_installed_languages()
