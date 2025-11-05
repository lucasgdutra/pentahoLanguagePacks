#!/usr/bin/env python3
"""
Pentaho Language Pack Installer - Standalone CLI
A simple, self-contained tool to install language packs for Pentaho 9+

Usage:
    python3 pentaho-langpack.py list --data-dir ../data
    python3 pentaho-langpack.py install ru --pentaho /opt/pentaho/pentaho-server --data-dir ../data
    python3 pentaho-langpack.py remove ru --pentaho /opt/pentaho/pentaho-server --data-dir ../data
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message):
    """Print error message in red"""
    print(f"{Colors.RED}✗{Colors.RESET} {message}", file=sys.stderr)


def print_info(message):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def print_warning(message):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def convert_properties_encoding(content):
    """
    Convert UTF-8 properties file content to Java native-to-ascii format.
    Non-ASCII characters are converted to \\uXXXX escape sequences.
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


def copy_file(src, dest, convert_encoding=False):
    """Copy a file, optionally converting encoding"""
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

        return True
    except Exception as e:
        print_error(f"Failed to copy {src.name}: {e}")
        return False


def get_metadata(data_dir, language_code):
    """Get metadata for a language pack"""
    metadata_path = Path(data_dir) / language_code / "metadata.json"

    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            metadata['languageCode'] = language_code
            return metadata
    except Exception as e:
        print_error(f"Failed to read metadata for {language_code}: {e}")
        return None


def list_languages(data_dir):
    """List all available language packs"""
    data_path = Path(data_dir)

    if not data_path.exists():
        print_error(f"Data directory not found: {data_dir}")
        return 1

    languages = []
    for lang_dir in data_path.iterdir():
        if lang_dir.is_dir():
            metadata = get_metadata(data_dir, lang_dir.name)
            if metadata:
                languages.append(metadata)

    if not languages:
        print_warning("No language packs found")
        return 0

    # Sort by language code
    languages.sort(key=lambda x: x.get('languageCode', ''))

    print(f"\n{Colors.BOLD}Available Language Packs ({len(languages)}):{Colors.RESET}\n")
    print(f"{'Code':<12} {'Language':<30} {'Maintainer':<30}")
    print("-" * 75)

    for lang in languages:
        code = lang.get('languageCode', 'N/A')
        language = lang.get('language', 'N/A')
        maintainer = lang.get('maintainer', {}).get('name', 'Unknown')
        print(f"{code:<12} {language:<30} {maintainer:<30}")

    print()
    return 0


def install_language(language_code, pentaho_dir, data_dir, convert_encoding=True):
    """Install a language pack"""
    print_info(f"Installing language pack: {language_code}")

    # Get metadata
    metadata = get_metadata(data_dir, language_code)
    if not metadata:
        print_error(f"Language pack '{language_code}' not found in {data_dir}")
        return 1

    lang_name = metadata.get('language', language_code)
    print_info(f"Language: {lang_name}")

    # Validate Pentaho installation
    pentaho_path = Path(pentaho_dir)
    system_dir = pentaho_path / "pentaho-solutions" / "system"
    tomcat_dir = pentaho_path / "tomcat" / "webapps" / "pentaho"

    if not system_dir.exists():
        print_error(f"Pentaho system directory not found: {system_dir}")
        print_info("Please provide the correct Pentaho base directory")
        return 1

    lang_dir = Path(data_dir) / language_code
    total_copied = 0
    total_errors = 0

    # Install system plugins
    system_src = lang_dir / "system"
    if system_src.exists():
        print_info("Installing system plugins...")
        files = list(system_src.rglob('*'))
        file_count = len([f for f in files if f.is_file()])

        for src_file in files:
            if not src_file.is_file():
                continue

            rel_path = src_file.relative_to(system_src)
            dest_file = system_dir / rel_path

            if copy_file(src_file, dest_file, convert_encoding):
                total_copied += 1
            else:
                total_errors += 1

        print_success(f"System plugins: {total_copied} files installed")
    else:
        print_warning("No system plugins found")

    # Install Tomcat resources
    tomcat_src = lang_dir / "tomcat"
    if tomcat_src.exists():
        print_info("Installing Tomcat resources...")

        # Handle JAR directory structure
        lib_src = tomcat_src / "webapps" / "pentaho" / "WEB-INF" / "lib"
        if lib_src.exists():
            lib_dest = tomcat_dir / "WEB-INF" / "lib"
            tomcat_copied = 0

            for jar_dir in lib_src.iterdir():
                if jar_dir.is_dir() and jar_dir.name.endswith('_jar'):
                    # Extract JAR name (remove _jar suffix)
                    jar_name = jar_dir.name[:-4]
                    dest_dir = lib_dest / jar_name

                    for src_file in jar_dir.rglob('*'):
                        if not src_file.is_file():
                            continue

                        rel_path = src_file.relative_to(jar_dir)
                        dest_file = dest_dir / rel_path

                        if copy_file(src_file, dest_file, convert_encoding):
                            tomcat_copied += 1
                        else:
                            total_errors += 1

            total_copied += tomcat_copied
            print_success(f"Tomcat resources: {tomcat_copied} files installed")
        else:
            print_warning("No Tomcat resources found")
    else:
        print_warning("No Tomcat resources found")

    # Summary
    print()
    if total_errors == 0:
        print_success(f"Installation complete! {total_copied} files installed")
        print_info("Restart Pentaho server to apply changes")
        return 0
    else:
        print_warning(f"Installation completed with errors: {total_copied} files installed, {total_errors} errors")
        return 1


def remove_language(language_code, pentaho_dir, data_dir):
    """Remove a language pack"""
    print_info(f"Removing language pack: {language_code}")

    # Get metadata
    metadata = get_metadata(data_dir, language_code)
    if not metadata:
        print_warning(f"Language pack '{language_code}' not found in data directory")
        print_info("Will attempt to remove language files anyway...")
    else:
        lang_name = metadata.get('language', language_code)
        print_info(f"Language: {lang_name}")

    # Validate Pentaho installation
    pentaho_path = Path(pentaho_dir)
    system_dir = pentaho_path / "pentaho-solutions" / "system"
    tomcat_dir = pentaho_path / "tomcat" / "webapps" / "pentaho"

    if not system_dir.exists():
        print_error(f"Pentaho system directory not found: {system_dir}")
        return 1

    total_removed = 0

    # Remove from system plugins
    print_info("Removing system files...")
    pattern = f'*_{language_code}.properties'
    for file_path in system_dir.rglob(pattern):
        try:
            file_path.unlink()
            total_removed += 1
        except Exception as e:
            print_error(f"Failed to remove {file_path}: {e}")

    # Remove JavaScript i18n files
    for lang_path in system_dir.rglob(f'nls/{language_code}'):
        if lang_path.is_dir():
            try:
                shutil.rmtree(lang_path)
                removed_files = len(list(lang_path.rglob('*')))
                total_removed += removed_files
            except Exception as e:
                print_error(f"Failed to remove {lang_path}: {e}")

    print_success(f"System files: {total_removed} items removed")

    # Remove from Tomcat resources
    if tomcat_dir.exists():
        print_info("Removing Tomcat files...")
        tomcat_removed = 0

        for file_path in tomcat_dir.rglob(pattern):
            try:
                file_path.unlink()
                tomcat_removed += 1
            except Exception as e:
                print_error(f"Failed to remove {file_path}: {e}")

        total_removed += tomcat_removed
        print_success(f"Tomcat files: {tomcat_removed} items removed")

    # Summary
    print()
    print_success(f"Removal complete! {total_removed} items removed")
    print_info("Restart Pentaho server to apply changes")
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Pentaho Language Pack Installer - Standalone CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # List available language packs
  %(prog)s list --data-dir ../data

  # Install Russian language pack
  %(prog)s install ru --pentaho /opt/pentaho/pentaho-server --data-dir ../data

  # Remove Portuguese language pack
  %(prog)s remove pt_PT --pentaho /opt/pentaho/pentaho-server --data-dir ../data

  # Install without encoding conversion
  %(prog)s install ru --pentaho /opt/pentaho/pentaho-server --data-dir ../data --no-encoding
        '''
    )

    parser.add_argument(
        '--data-dir',
        default='../data',
        help='Path to language packs data directory (default: ../data)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List available language packs')

    # Install command
    install_parser = subparsers.add_parser('install', help='Install a language pack')
    install_parser.add_argument('language_code', help='Language code (e.g., ru, pt_PT)')
    install_parser.add_argument(
        '--pentaho',
        required=True,
        help='Pentaho base directory (e.g., /opt/pentaho/pentaho-server)'
    )
    install_parser.add_argument(
        '--no-encoding',
        action='store_true',
        help='Skip UTF-8 to Java properties encoding conversion'
    )

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a language pack')
    remove_parser.add_argument('language_code', help='Language code (e.g., ru, pt_PT)')
    remove_parser.add_argument(
        '--pentaho',
        required=True,
        help='Pentaho base directory (e.g., /opt/pentaho/pentaho-server)'
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    try:
        if args.command == 'list':
            return list_languages(args.data_dir)

        elif args.command == 'install':
            convert_encoding = not args.no_encoding
            return install_language(
                args.language_code,
                args.pentaho,
                args.data_dir,
                convert_encoding
            )

        elif args.command == 'remove':
            return remove_language(
                args.language_code,
                args.pentaho,
                args.data_dir
            )

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print()
        print_warning("Operation cancelled by user")
        return 130

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
