# Pentaho Language Pack Installer (Python Implementation)

This is a Python-based reimplementation of the Pentaho Language Pack Installer, designed to work with Pentaho BI Server version 9 and above. It replaces the Kettle (kjb/ktr) based approach with a pure Python solution.

## Features

- **Pure Python Implementation**: No dependency on Pentaho Data Integration (Kettle)
- **REST API**: Compatible with existing dashboard interfaces
- **Command-line Interface**: Standalone CLI for easy management
- **Encoding Support**: Automatic UTF-8 to Java properties encoding conversion
- **Multi-language Support**: Install/remove 42+ language packs
- **Progress Tracking**: Real-time installation progress feedback
- **Easy Integration**: Drop-in replacement for existing Pentaho installations

## Supported Languages

The installer supports 42 language locales including:

Arabic (ar), Catalan (ca), Czech (cs), Danish (da), German (de), Greek (el), English (en, en_US), Spanish (es, es_AR, es_ES, es_MX), Finnish (fi), French (fr), Galician (gl), Hindi (hi), Croatian (hr), Hungarian (hu), Italian (it), Japanese (ja), Korean (ko), Lithuanian (lt), Dutch (nl), Norwegian (no), Polish (pl), Portuguese (pt_BR, pt_PT), Romanian (ro), Russian (ru), Slovak (sk), Slovenian (sl), Albanian (sq_AL), Swedish (sv), Tamil (ta), Thai (th), Klingon (tlh), Turkish (tr), Ukrainian (uk), Chinese (zh, zh_CN, zh_TW)

## Requirements

- Python 3.7 or higher
- Pentaho BI Server 9.0 or higher
- Flask (for REST API)

## Installation

### 1. Install Python Dependencies

```bash
cd python
pip install -r requirements.txt
```

Or install as a package:

```bash
cd python
pip install -e .
```

### 2. Configuration

Set environment variables (optional):

```bash
export PLUGIN_DIR="/path/to/pentaho-server/pentaho-solutions/system/languagePackInstaller"
export PENTAHO_BASE_DIR="/path/to/pentaho-server"
```

## Usage

### Command-line Interface

#### List available language packs

```bash
python cli.py list
```

#### Show information about a language pack

```bash
python cli.py info ru
```

#### Install a language pack

```bash
python cli.py install ru
```

#### Remove a language pack

```bash
python cli.py remove ru
```

#### List installed language packs

```bash
python cli.py installed
```

#### Help

```bash
python cli.py --help
```

### REST API Server

Start the API server:

```bash
python api.py
```

Or using gunicorn (production):

```bash
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

#### API Endpoints

- `GET /plugin/languagePackInstaller/api/listlanguages` - List all language packs
- `GET /plugin/languagePackInstaller/api/getpackmetadata?languageCode=ru` - Get metadata
- `POST /plugin/languagePackInstaller/api/installpack?languageCode=ru` - Install language pack
- `POST /plugin/languagePackInstaller/api/removepack?languageCode=ru` - Remove language pack
- `GET /plugin/languagePackInstaller/api/health` - Health check
- `GET /plugin/languagePackInstaller/api/version` - Version information

### Python API

```python
from languagepack.installer import LanguagePackInstaller
from languagepack.remover import LanguagePackRemover
from languagepack.metadata import LanguagePackMetadata

# Initialize
installer = LanguagePackInstaller(
    plugin_dir="/path/to/plugin",
    pentaho_base_dir="/path/to/pentaho"
)

# Install a language pack
result = installer.install_language_pack('ru')
print(result)

# Remove a language pack
remover = LanguagePackRemover(plugin_dir, pentaho_base_dir)
result = remover.remove_language_pack('ru')
print(result)

# Get metadata
metadata_handler = LanguagePackMetadata(plugin_dir)
metadata = metadata_handler.get_metadata('ru')
print(metadata)
```

## Architecture

### Directory Structure

```
python/
├── languagepack/          # Core package
│   ├── __init__.py
│   ├── installer.py       # Installation logic
│   ├── remover.py         # Removal logic
│   ├── metadata.py        # Metadata handling
│   └── utils.py           # Utility functions
├── api.py                 # Flask REST API
├── cli.py                 # Command-line interface
├── requirements.txt       # Dependencies
├── setup.py              # Package setup
└── README.md             # This file
```

### How It Works

1. **Metadata Reading**: Reads `metadata.json` files from `data/{language_code}/` directories
2. **File Copying**: Copies language files from plugin data to Pentaho installation:
   - System plugins: `data/{lang}/system/*` → `pentaho-solutions/system/*`
   - Tomcat resources: `data/{lang}/tomcat/*` → `tomcat/webapps/pentaho/*`
3. **Encoding Conversion**: Converts UTF-8 properties files to Java native-to-ascii format
4. **REST Integration**: Provides REST endpoints compatible with existing dashboard UI

### What Gets Installed

For each language pack, the installer copies:

- **System Plugin Translations**: Messages for 60+ Pentaho plugins
  - CTools (CDF, CDA, CDV, CDE, etc.)
  - Core plugins (Analyzer, WAQR, Reporting, etc.)
  - Admin interfaces
- **Tomcat JAR Resources**: Embedded translations for Java libraries
  - Platform core messages
  - Metadata services
  - Reporting engine
  - Business intelligence components
- **JavaScript i18n**: Web component localizations
- **Properties Files**: Standard Java ResourceBundle format

## Integration with Pentaho

### Option 1: Run as Standalone Service

Run the Python API server alongside Pentaho:

```bash
# Start API server
gunicorn -w 4 -b 127.0.0.1:5000 api:app

# Configure reverse proxy in Pentaho (Apache/Tomcat)
# to forward /plugin/languagePackInstaller/api/* to localhost:5000
```

### Option 2: Update Plugin Configuration

Modify `plugin.spring.xml` to point to the Python REST endpoints instead of Kettle transformations.

### Option 3: Use CLI During Deployment

Use the CLI tool during Pentaho server deployment/configuration:

```bash
# In deployment scripts
pentaho-langpack install ru
pentaho-langpack install pt_BR
```

## Migration from Kettle Version

The Python implementation is designed as a drop-in replacement:

1. **Same Data Structure**: Uses the same `data/` directory structure and `metadata.json` format
2. **Compatible API**: REST endpoints match the original Kettle transformation outputs
3. **Same Dashboard**: Works with the existing CDF dashboard interface
4. **No Data Changes**: Language pack data files remain unchanged

### Migration Steps

1. Install Python dependencies: `pip install -r requirements.txt`
2. Start Python API server: `gunicorn api:app`
3. Update plugin configuration to use Python endpoints (optional)
4. Existing language pack data works as-is

## Advantages Over Kettle Version

1. **No Kettle Dependency**: Works without Pentaho Data Integration
2. **Lighter Weight**: Smaller footprint, faster startup
3. **Better Error Handling**: Detailed error messages and logging
4. **Version Compatible**: Works with Pentaho 9+ without Kettle version issues
5. **Easier Development**: Standard Python development workflow
6. **Modern API**: RESTful JSON API with proper HTTP status codes
7. **CLI Support**: Easy automation and scripting
8. **Cross-platform**: Works on any platform with Python

## Troubleshooting

### Permission Issues

Ensure the Python process has write access to:
- `pentaho-solutions/system/` (for system plugin translations)
- `tomcat/webapps/pentaho/WEB-INF/lib/` (for Tomcat resources)

### Language Pack Not Found

Check that the language code matches a directory in `data/`:
```bash
ls data/
```

### Encoding Issues

If you see mojibake (garbled characters), ensure:
1. Source files are UTF-8 encoded
2. Encoding conversion is enabled (default)

### API Connection Issues

Check that:
1. Flask server is running: `ps aux | grep api.py`
2. Correct port is configured
3. Firewall allows connections
4. CORS is properly configured for dashboard domain

## Development

### Running Tests

```bash
# Unit tests (when implemented)
pytest tests/

# Manual testing
python cli.py list
python cli.py info ru
```

### Adding New Features

1. Core logic: Add to `languagepack/` modules
2. REST endpoints: Add to `api.py`
3. CLI commands: Add to `cli.py`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

Apache License 2.0 (same as original project)

## Credits

This Python implementation maintains compatibility with the original Kettle-based Language Pack Installer while providing a modern, maintainable codebase for Pentaho 9+.

Original project: https://github.com/lucasgdutra/pentahoLanguagePacks

## Support

For issues and questions:
- GitHub Issues: https://github.com/lucasgdutra/pentahoLanguagePacks/issues
- Original project documentation: See `documentation/` directory
