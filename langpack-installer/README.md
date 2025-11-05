# Pentaho Language Pack Installer - Standalone CLI

A simple, self-contained command-line tool to install language packs for Pentaho BI Server 9+.

## Features

- ✅ **Single Python file** - No complex dependencies
- ✅ **Bash wrapper** - Easy to use from shell
- ✅ **Self-contained** - Uses language pack data from parent directory
- ✅ **Simple** - Just point to your Pentaho installation
- ✅ **Fast** - Direct file copying with optional encoding conversion
- ✅ **Colorful output** - Clear success/error messages

## Requirements

- Python 3.7 or higher (standard library only, no pip packages needed)
- Pentaho BI Server 9.0 or higher
- Write access to Pentaho installation directory

## Quick Start

### 1. List Available Languages

```bash
./pentaho-langpack list
```

This will show all available language packs from the `../data` directory.

### 2. Install a Language Pack

```bash
./pentaho-langpack install ru --pentaho /opt/pentaho/pentaho-server
```

Replace:
- `ru` with your desired language code (e.g., `pt_PT`, `zh_CN`, `es`, `fr`)
- `/opt/pentaho/pentaho-server` with your Pentaho installation path

### 3. Remove a Language Pack

```bash
./pentaho-langpack remove ru --pentaho /opt/pentaho/pentaho-server
```

### 4. Restart Pentaho

After installing or removing language packs, restart your Pentaho server:

```bash
/opt/pentaho/pentaho-server/stop-pentaho.sh
/opt/pentaho/pentaho-server/start-pentaho.sh
```

## Usage

### Basic Commands

```bash
# List available language packs
./pentaho-langpack list

# Install a language pack
./pentaho-langpack install <language_code> --pentaho <pentaho_path>

# Remove a language pack
./pentaho-langpack remove <language_code> --pentaho <pentaho_path>

# Show help
./pentaho-langpack --help
```

### Examples

```bash
# List all available languages
./pentaho-langpack list

# Install Russian
./pentaho-langpack install ru --pentaho /opt/pentaho/pentaho-server

# Install Brazilian Portuguese
./pentaho-langpack install pt_BR --pentaho /opt/pentaho/pentaho-server

# Install Chinese (Simplified)
./pentaho-langpack install zh_CN --pentaho /opt/pentaho/pentaho-server

# Install Spanish (Spain)
./pentaho-langpack install es_ES --pentaho /opt/pentaho/pentaho-server

# Remove French
./pentaho-langpack remove fr --pentaho /opt/pentaho/pentaho-server

# Install without encoding conversion (if you have issues)
./pentaho-langpack install ru --pentaho /opt/pentaho/pentaho-server --no-encoding
```

### Using Python Directly

If you prefer to use Python directly:

```bash
# List languages
python3 pentaho-langpack.py list --data-dir ../data

# Install a language
python3 pentaho-langpack.py install ru \
  --pentaho /opt/pentaho/pentaho-server \
  --data-dir ../data

# Remove a language
python3 pentaho-langpack.py remove ru \
  --pentaho /opt/pentaho/pentaho-server \
  --data-dir ../data
```

## How It Works

1. **Reads metadata** from `../data/<language_code>/metadata.json`
2. **Copies system files** from `../data/<language_code>/system/` to `pentaho-solutions/system/`
3. **Copies Tomcat files** from `../data/<language_code>/tomcat/` to `tomcat/webapps/pentaho/`
4. **Converts encoding** (optional) from UTF-8 to Java properties format
5. **Reports progress** with colored output

### What Gets Installed

For each language pack:
- **System Plugin Translations** - Messages for 60+ Pentaho plugins
  - CTools (CDF, CDA, CDV, CDE)
  - Core plugins (Analyzer, WAQR, Reporting)
  - Admin interfaces
- **Tomcat JAR Resources** - Embedded translations for Java libraries
- **JavaScript i18n** - Web component localizations
- **Properties Files** - Standard Java ResourceBundle format

### Directory Structure

```
langpack-installer/
├── pentaho-langpack          # Bash wrapper (use this!)
├── pentaho-langpack.py       # Python CLI script
├── README.md                 # This file
└── ../data/                  # Language pack data (auto-detected)
    ├── ru/                   # Russian
    ├── pt_PT/                # Portuguese (Portugal)
    ├── zh_CN/                # Chinese (Simplified)
    └── ...                   # 42 languages total
```

## Supported Languages

The installer supports 42 language locales:

| Code | Language | Code | Language |
|------|----------|------|----------|
| ar | Arabic | it | Italian |
| ca | Catalan | ja | Japanese |
| cs | Czech | ko | Korean |
| da | Danish | lt | Lithuanian |
| de | German | nl | Dutch |
| el | Greek | no | Norwegian |
| en | English | pl | Polish |
| es | Spanish | pt_BR | Portuguese (Brazil) |
| fi | Finnish | pt_PT | Portuguese (Portugal) |
| fr | French | ro | Romanian |
| gl | Galician | ru | Russian |
| hi | Hindi | sk | Slovak |
| hr | Croatian | sl | Slovenian |
| hu | Hungarian | sq_AL | Albanian |
| sv | Swedish | ta | Tamil |
| th | Thai | tlh | Klingon |
| tr | Turkish | uk | Ukrainian |
| zh | Chinese | zh_CN | Chinese (Simplified) |
| zh_TW | Chinese (Traditional) | | |

See metadata in `../data/<code>/metadata.json` for details.

## Troubleshooting

### Permission Denied

If you get permission errors:

```bash
# Run with sudo
sudo ./pentaho-langpack install ru --pentaho /opt/pentaho/pentaho-server

# Or fix ownership
sudo chown -R $USER:$USER /opt/pentaho/pentaho-server
```

### Python Not Found

```bash
# Install Python 3 on Ubuntu/Debian
sudo apt-get install python3

# Install Python 3 on CentOS/RHEL
sudo yum install python3

# Install Python 3 on macOS
brew install python3
```

### Data Directory Not Found

If the script can't find the data directory:

```bash
# Specify custom data directory
python3 pentaho-langpack.py list --data-dir /path/to/data

# Or use absolute path
python3 pentaho-langpack.py install ru \
  --pentaho /opt/pentaho/pentaho-server \
  --data-dir /path/to/pentahoLanguagePacks/data
```

### Encoding Issues (Garbled Characters)

If you see mojibake (corrupted characters) after installation:

1. Try installing again (encoding conversion is enabled by default)
2. Check that source files are UTF-8 encoded
3. If problems persist, file an issue on GitHub

### Language Not Appearing in Pentaho

1. **Clear Pentaho cache:**
   ```bash
   rm -rf /opt/pentaho/pentaho-server/tomcat/work/*
   rm -rf /opt/pentaho/pentaho-server/tomcat/temp/*
   ```

2. **Restart Pentaho:**
   ```bash
   /opt/pentaho/pentaho-server/stop-pentaho.sh
   /opt/pentaho/pentaho-server/start-pentaho.sh
   ```

3. **Verify files were installed:**
   ```bash
   find /opt/pentaho/pentaho-server -name "*_ru.properties" | head -5
   ```

## Advanced Usage

### Batch Installation

Install multiple languages at once:

```bash
#!/bin/bash
for lang in ru pt_BR zh_CN es fr de; do
    echo "Installing $lang..."
    ./pentaho-langpack install "$lang" --pentaho /opt/pentaho/pentaho-server
done
echo "All languages installed. Restart Pentaho server."
```

### Deployment Script

```bash
#!/bin/bash
# deploy-languages.sh
PENTAHO_HOME=/opt/pentaho/pentaho-server
LANGUAGES="ru pt_BR es"

echo "Installing language packs for Pentaho..."

for lang in $LANGUAGES; do
    echo "→ Installing $lang"
    ./pentaho-langpack install "$lang" --pentaho "$PENTAHO_HOME"
    if [ $? -eq 0 ]; then
        echo "  ✓ $lang installed successfully"
    else
        echo "  ✗ $lang installation failed"
        exit 1
    fi
done

echo ""
echo "Restarting Pentaho server..."
"$PENTAHO_HOME/stop-pentaho.sh"
sleep 5
"$PENTAHO_HOME/start-pentaho.sh"

echo "Deployment complete!"
```

### Docker Integration

```dockerfile
FROM pentaho/pentaho-server:9.0

# Copy language pack installer
COPY langpack-installer /opt/langpack-installer
COPY data /opt/langpack-installer/data

# Install language packs
RUN cd /opt/langpack-installer && \
    ./pentaho-langpack install ru --pentaho /opt/pentaho/pentaho-server && \
    ./pentaho-langpack install pt_BR --pentaho /opt/pentaho/pentaho-server

CMD ["/opt/pentaho/pentaho-server/start-pentaho.sh"]
```

## Comparison with Full Python Implementation

This standalone CLI is a simplified version. If you need more features, see the full Python implementation in `../python/`:

| Feature | Standalone CLI | Full Python |
|---------|---------------|-------------|
| Installation | ✅ | ✅ |
| Removal | ✅ | ✅ |
| List languages | ✅ | ✅ |
| REST API | ❌ | ✅ |
| Dashboard integration | ❌ | ✅ |
| Progress callbacks | ❌ | ✅ |
| systemd service | ❌ | ✅ |
| Docker deployment | Manual | ✅ |
| Dependencies | None (stdlib only) | Flask, gunicorn |

**Use this standalone CLI when:**
- You want simplicity
- You only need command-line usage
- You prefer bash scripts
- You don't need a REST API

**Use the full Python implementation when:**
- You need REST API endpoints
- You want dashboard integration
- You need systemd service
- You want production deployment

## FAQ

**Q: Do I need to install any Python packages?**
A: No! The standalone CLI uses only Python's standard library.

**Q: Can I use this with Pentaho 8 or earlier?**
A: This tool is designed for Pentaho 9+. For older versions, use the original Kettle-based installer.

**Q: Will this overwrite my existing Pentaho files?**
A: Yes, it copies language files to your Pentaho installation. Always backup first!

**Q: Can I uninstall a language pack?**
A: Yes, use the `remove` command. It will delete language-specific files.

**Q: How long does installation take?**
A: Usually 10-30 seconds depending on language pack size and disk speed.

**Q: Can I run this on Windows?**
A: Yes, use `python3 pentaho-langpack.py` directly. The bash wrapper is for Linux/macOS only.

## Backup Before Installing

**Always backup your Pentaho installation before installing language packs:**

```bash
# Backup Pentaho system directory
sudo tar -czf pentaho-backup-$(date +%Y%m%d).tar.gz \
  /opt/pentaho/pentaho-server/pentaho-solutions/system \
  /opt/pentaho/pentaho-server/tomcat/webapps/pentaho/WEB-INF/lib
```

To restore:

```bash
sudo tar -xzf pentaho-backup-20250101.tar.gz -C /
```

## Security Considerations

- Run with appropriate permissions (usually requires sudo or pentaho user)
- Don't run as root unless necessary
- Verify file ownership after installation
- Review language pack contents before installing

## Contributing

Language pack translations are maintained in the `data/` directory. To contribute translations:

1. Edit files in `data/<language_code>/`
2. Test with this installer
3. Submit a pull request

See main project README for details.

## License

Apache License 2.0 (same as parent project)

## Support

For issues and questions:
- GitHub Issues: https://github.com/lucasgdutra/pentahoLanguagePacks/issues
- Documentation: See `../python/` for full implementation docs

## Credits

This is a simplified standalone version of the Pentaho Language Pack Installer project.

Original project: https://github.com/webdetails/pentahoLanguagePacks
