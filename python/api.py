"""
REST API for Pentaho Language Pack Installer.
Provides endpoints compatible with the existing dashboard interface.
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from languagepack.installer import LanguagePackInstaller
from languagepack.remover import LanguagePackRemover
from languagepack.metadata import LanguagePackMetadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for Pentaho dashboard integration

# Configuration
PLUGIN_DIR = os.environ.get('PLUGIN_DIR', '/opt/pentaho/pentaho-server/pentaho-solutions/system/languagePackInstaller')
PENTAHO_BASE_DIR = os.environ.get('PENTAHO_BASE_DIR', '/opt/pentaho/pentaho-server')

# Initialize components
metadata_handler = LanguagePackMetadata(PLUGIN_DIR)
installer = LanguagePackInstaller(PLUGIN_DIR, PENTAHO_BASE_DIR)
remover = LanguagePackRemover(PLUGIN_DIR, PENTAHO_BASE_DIR)


@app.route('/plugin/languagePackInstaller/api/getpackmetadata', methods=['GET'])
def get_pack_metadata():
    """
    Get metadata for a specific language pack.
    Compatible with the original getpackmetadata.ktr endpoint.

    Query Parameters:
        languageCode: Language code (e.g., 'ru', 'pt_PT')

    Returns:
        JSON response with metadata
    """
    language_code = request.args.get('languageCode', request.args.get('param_languageCode'))

    if not language_code:
        return jsonify({
            'error': 'Missing required parameter: languageCode',
            'success': False
        }), 400

    try:
        metadata = metadata_handler.get_metadata(language_code)

        if not metadata:
            return jsonify({
                'error': f'Language pack not found: {language_code}',
                'success': False
            }), 404

        # Add installation status
        metadata['installed'] = installer.is_language_installed(language_code)

        return jsonify({
            'success': True,
            'metadata': metadata,
            'resultset': [metadata]  # For compatibility with Kettle output format
        })

    except Exception as e:
        logger.error(f"Error getting metadata: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@app.route('/plugin/languagePackInstaller/api/listlanguages', methods=['GET'])
def list_languages():
    """
    List all available language packs.

    Returns:
        JSON response with list of languages and their metadata
    """
    try:
        languages = metadata_handler.list_available_languages()
        installed = installer.get_installed_languages()

        # Add installation status to each language
        for lang_code, metadata in languages.items():
            metadata['installed'] = lang_code in installed

        return jsonify({
            'success': True,
            'languages': languages,
            'installed': installed
        })

    except Exception as e:
        logger.error(f"Error listing languages: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@app.route('/plugin/languagePackInstaller/api/installpack', methods=['POST', 'GET'])
def install_pack():
    """
    Install a language pack.
    Compatible with the original installpack.kjb endpoint.

    Query/Form Parameters:
        languageCode: Language code to install

    Returns:
        JSON response with installation results
    """
    # Support both GET and POST for compatibility
    language_code = request.args.get('languageCode') or request.args.get('param_languageCode')
    if not language_code and request.method == 'POST':
        language_code = request.form.get('languageCode') or request.form.get('param_languageCode')

    if not language_code:
        return jsonify({
            'error': 'Missing required parameter: languageCode',
            'success': False
        }), 400

    try:
        logger.info(f"Installing language pack: {language_code}")

        result = installer.install_language_pack(language_code)

        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'languageCode': result['language_code'],
            'filesCopied': result['files_copied'],
            'errors': result['errors']
        }), 200 if result['success'] else 500

    except Exception as e:
        logger.error(f"Error installing language pack: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@app.route('/plugin/languagePackInstaller/api/removepack', methods=['POST', 'GET'])
def remove_pack():
    """
    Remove a language pack.
    Compatible with the original removepack.kjb endpoint.

    Query/Form Parameters:
        languageCode: Language code to remove

    Returns:
        JSON response with removal results
    """
    # Support both GET and POST for compatibility
    language_code = request.args.get('languageCode') or request.args.get('param_languageCode')
    if not language_code and request.method == 'POST':
        language_code = request.form.get('languageCode') or request.form.get('param_languageCode')

    if not language_code:
        return jsonify({
            'error': 'Missing required parameter: languageCode',
            'success': False
        }), 400

    try:
        logger.info(f"Removing language pack: {language_code}")

        result = remover.remove_language_pack(language_code)

        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'languageCode': result['language_code'],
            'filesRemoved': result['files_removed'],
            'errors': result['errors']
        }), 200 if result['success'] else 500

    except Exception as e:
        logger.error(f"Error removing language pack: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@app.route('/plugin/languagePackInstaller/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'running',
        'plugin_dir': PLUGIN_DIR,
        'pentaho_base_dir': PENTAHO_BASE_DIR
    })


@app.route('/plugin/languagePackInstaller/api/version', methods=['GET'])
def version():
    """Get API version information."""
    from languagepack import __version__
    return jsonify({
        'success': True,
        'version': __version__,
        'implementation': 'Python'
    })


if __name__ == '__main__':
    # Check if plugin directory exists
    if not Path(PLUGIN_DIR).exists():
        logger.warning(f"Plugin directory not found: {PLUGIN_DIR}")
        logger.warning("Using current directory for development")
        PLUGIN_DIR = str(Path(__file__).parent.parent)

    # Run Flask development server
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Language Pack Installer API on port {port}")
    logger.info(f"Plugin directory: {PLUGIN_DIR}")
    logger.info(f"Pentaho base directory: {PENTAHO_BASE_DIR}")

    app.run(host='0.0.0.0', port=port, debug=False)
