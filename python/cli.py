#!/usr/bin/env python3
"""
Command-line interface for Pentaho Language Pack Installer.
Provides standalone installation and management of language packs.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from languagepack.installer import LanguagePackInstaller
from languagepack.remover import LanguagePackRemover
from languagepack.metadata import LanguagePackMetadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def progress_callback(stage: str, current: int, total: int):
    """Progress callback for installation."""
    percent = (current / total * 100) if total > 0 else 0
    print(f"  [{percent:3.0f}%] {stage} ({current}/{total})")


def cmd_install(args):
    """Install a language pack."""
    installer = LanguagePackInstaller(
        args.plugin_dir,
        args.pentaho_dir,
        convert_encoding=not args.no_encoding_conversion
    )

    result = installer.install_language_pack(
        args.language_code,
        progress_callback=progress_callback if args.verbose else None
    )

    if result['success']:
        print(f"✓ {result['message']}")
        return 0
    else:
        print(f"✗ {result['message']}")
        for error in result['errors']:
            print(f"  Error: {error}")
        return 1


def cmd_remove(args):
    """Remove a language pack."""
    remover = LanguagePackRemover(args.plugin_dir, args.pentaho_dir)

    result = remover.remove_language_pack(args.language_code)

    if result['success']:
        print(f"✓ {result['message']}")
        return 0
    else:
        print(f"✗ {result['message']}")
        for error in result['errors']:
            print(f"  Error: {error}")
        return 1


def cmd_list(args):
    """List available language packs."""
    metadata_handler = LanguagePackMetadata(args.plugin_dir)
    installer = LanguagePackInstaller(args.plugin_dir, args.pentaho_dir)

    languages = metadata_handler.list_available_languages()
    installed = installer.get_installed_languages()

    if not languages:
        print("No language packs found.")
        return 0

    print(f"\nAvailable language packs ({len(languages)}):\n")
    print(f"{'Code':<10} {'Language':<25} {'Status':<12} {'Maintainer':<30}")
    print("-" * 80)

    for lang_code, metadata in sorted(languages.items()):
        status = "INSTALLED" if lang_code in installed else "Available"
        maintainer = metadata.get('maintainer', {}).get('name', 'Unknown')
        language = metadata.get('language', lang_code)

        print(f"{lang_code:<10} {language:<25} {status:<12} {maintainer:<30}")

    print()
    return 0


def cmd_info(args):
    """Show information about a language pack."""
    metadata_handler = LanguagePackMetadata(args.plugin_dir)
    installer = LanguagePackInstaller(args.plugin_dir, args.pentaho_dir)

    metadata = metadata_handler.get_metadata(args.language_code)

    if not metadata:
        print(f"Language pack '{args.language_code}' not found.")
        return 1

    installed = installer.is_language_installed(args.language_code)

    print(f"\nLanguage Pack Information: {args.language_code}\n")
    print(f"Language:        {metadata.get('language', 'N/A')}")
    print(f"App Title:       {metadata.get('appTitle', 'N/A')}")
    print(f"Pentaho Version: {metadata.get('pentahoVersion', 'N/A')}")
    print(f"Status:          {'INSTALLED' if installed else 'Not installed'}")

    maintainer = metadata.get('maintainer', {})
    if maintainer:
        print(f"\nMaintainer:")
        print(f"  Name:  {maintainer.get('name', 'N/A')}")
        print(f"  Email: {maintainer.get('email', 'N/A')}")
        print(f"  URL:   {maintainer.get('url', 'N/A')}")

    maturity = metadata.get('maturity', {})
    if maturity:
        print(f"\nMaturity:")
        print(f"  Lane:  {maturity.get('lane', 'N/A')}")
        print(f"  Phase: {maturity.get('phase', 'N/A')}")

    credits = metadata.get('credits', [])
    if credits:
        print(f"\nCredits:")
        for credit in credits:
            print(f"  - {credit}")

    print()
    return 0


def cmd_installed(args):
    """List installed language packs."""
    installer = LanguagePackInstaller(args.plugin_dir, args.pentaho_dir)
    metadata_handler = LanguagePackMetadata(args.plugin_dir)

    installed = installer.get_installed_languages()

    if not installed:
        print("No language packs are currently installed.")
        return 0

    print(f"\nInstalled language packs ({len(installed)}):\n")

    for lang_code in sorted(installed):
        metadata = metadata_handler.get_metadata(lang_code)
        if metadata:
            language = metadata.get('language', lang_code)
            print(f"  {lang_code:<10} - {language}")
        else:
            print(f"  {lang_code:<10} - (metadata not found)")

    print()
    return 0


def main():
    """Main entry point."""
    # Default paths
    default_plugin_dir = os.environ.get(
        'PLUGIN_DIR',
        '/opt/pentaho/pentaho-server/pentaho-solutions/system/languagePackInstaller'
    )
    default_pentaho_dir = os.environ.get(
        'PENTAHO_BASE_DIR',
        '/opt/pentaho/pentaho-server'
    )

    # If running from plugin directory, use that
    if Path(__file__).parent.parent.name == 'pentahoLanguagePacks':
        default_plugin_dir = str(Path(__file__).parent.parent)

    # Main parser
    parser = argparse.ArgumentParser(
        description='Pentaho Language Pack Installer CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # List available language packs
  %(prog)s list

  # Install Russian language pack
  %(prog)s install ru

  # Remove Portuguese language pack
  %(prog)s remove pt_PT

  # Show information about a language pack
  %(prog)s info zh_CN

  # List installed language packs
  %(prog)s installed
        '''
    )

    parser.add_argument(
        '--plugin-dir',
        default=default_plugin_dir,
        help=f'Plugin directory (default: {default_plugin_dir})'
    )

    parser.add_argument(
        '--pentaho-dir',
        default=default_pentaho_dir,
        help=f'Pentaho base directory (default: {default_pentaho_dir})'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Install command
    install_parser = subparsers.add_parser('install', help='Install a language pack')
    install_parser.add_argument('language_code', help='Language code (e.g., ru, pt_PT)')
    install_parser.add_argument(
        '--no-encoding-conversion',
        action='store_true',
        help='Skip UTF-8 to Java properties encoding conversion'
    )
    install_parser.set_defaults(func=cmd_install)

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a language pack')
    remove_parser.add_argument('language_code', help='Language code (e.g., ru, pt_PT)')
    remove_parser.set_defaults(func=cmd_remove)

    # List command
    list_parser = subparsers.add_parser('list', help='List available language packs')
    list_parser.set_defaults(func=cmd_list)

    # Info command
    info_parser = subparsers.add_parser('info', help='Show language pack information')
    info_parser.add_argument('language_code', help='Language code (e.g., ru, pt_PT)')
    info_parser.set_defaults(func=cmd_info)

    # Installed command
    installed_parser = subparsers.add_parser('installed', help='List installed language packs')
    installed_parser.set_defaults(func=cmd_installed)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Execute command
    try:
        return args.func(args)
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
