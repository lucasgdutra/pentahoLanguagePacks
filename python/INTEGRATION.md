# Pentaho Language Pack Installer - Integration Guide

This guide explains how to integrate the Python-based Language Pack Installer with your Pentaho BI Server installation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Configuration](#configuration)
4. [Integration Options](#integration-options)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

- Pentaho BI Server 9.0 or higher
- Python 3.7 or higher
- Write access to Pentaho installation directories
- (Optional) nginx or Apache for reverse proxy

## Installation Methods

### Method 1: Standalone API Service (Recommended)

This method runs the Python API as a separate service alongside Pentaho.

#### Step 1: Install Python Dependencies

```bash
cd /opt/pentaho/pentaho-server/pentaho-solutions/system/languagePackInstaller/python
pip install -r requirements.txt
```

#### Step 2: Configure systemd Service

```bash
# Copy systemd service file
sudo cp deployment/systemd/pentaho-langpack-api.service /etc/systemd/system/

# Edit paths if your installation differs
sudo nano /etc/systemd/system/pentaho-langpack-api.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable pentaho-langpack-api
sudo systemctl start pentaho-langpack-api

# Check status
sudo systemctl status pentaho-langpack-api
```

#### Step 3: Configure Reverse Proxy

**For nginx:**

```bash
# Copy nginx configuration
sudo cp deployment/nginx/langpack.conf /etc/nginx/conf.d/

# Or add to existing Pentaho site configuration
sudo nano /etc/nginx/sites-available/pentaho

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

**For Apache:**

```apache
# Add to your Pentaho VirtualHost
<Location /plugin/languagePackInstaller/api>
    ProxyPass http://127.0.0.1:5000/plugin/languagePackInstaller/api
    ProxyPassReverse http://127.0.0.1:5000/plugin/languagePackInstaller/api
    ProxyTimeout 300
</Location>
```

### Method 2: Docker Container

Perfect for containerized Pentaho deployments.

```bash
# Build and run
cd python
docker-compose -f deployment/docker/docker-compose.yml up -d

# Check logs
docker logs pentaho-langpack-api

# Stop
docker-compose -f deployment/docker/docker-compose.yml down
```

### Method 3: Development Mode

For testing and development:

```bash
cd python
export PLUGIN_DIR="/opt/pentaho/pentaho-server/pentaho-solutions/system/languagePackInstaller"
export PENTAHO_BASE_DIR="/opt/pentaho/pentaho-server"
python api.py
```

### Method 4: CLI Only

Use only the command-line interface without REST API:

```bash
cd python
pip install -e .

# Use CLI
pentaho-langpack list
pentaho-langpack install ru
```

## Configuration

### Environment Variables

Set these environment variables for the API service:

```bash
# Required
PLUGIN_DIR="/opt/pentaho/pentaho-server/pentaho-solutions/system/languagePackInstaller"
PENTAHO_BASE_DIR="/opt/pentaho/pentaho-server"

# Optional
PORT=5000  # API port (default: 5000)
```

### File Permissions

Ensure proper permissions:

```bash
# API service needs write access to:
chown -R pentaho:pentaho /opt/pentaho/pentaho-server/pentaho-solutions/system
chown -R pentaho:pentaho /opt/pentaho/pentaho-server/tomcat/webapps/pentaho/WEB-INF/lib
```

## Integration Options

### Option A: Dashboard Integration (Full Integration)

The existing CDF dashboard will work with the Python API through the reverse proxy.

**No changes needed** if you're using the reverse proxy configuration!

The dashboard already calls these endpoints:
- `/plugin/languagePackInstaller/api/getpackmetadata`
- `/plugin/languagePackInstaller/api/installpack`
- `/plugin/languagePackInstaller/api/removepack`

### Option B: Update Plugin Configuration (Advanced)

If you want to remove Kettle dependencies entirely, update `plugin.spring.xml`:

```xml
<!-- Replace Kettle endpoint beans with Python REST calls -->
<bean id="languagePackApi" class="pt.webdetails.cpk.api.PluginApiRouter">
    <property name="baseUrl" value="http://localhost:5000/plugin/languagePackInstaller/api"/>
</bean>
```

### Option C: CLI Integration in Scripts

Use the CLI in deployment scripts:

```bash
#!/bin/bash
# deploy-pentaho.sh

# Install required language packs
pentaho-langpack install ru
pentaho-langpack install pt_BR
pentaho-langpack install zh_CN

# Start Pentaho
/opt/pentaho/pentaho-server/start-pentaho.sh
```

### Option D: Hybrid Approach

Keep the dashboard but use CLI for automation:

```bash
# Automated deployment
pentaho-langpack install ru

# Interactive management via dashboard
# Users access: http://pentaho-server/plugin/languagePackInstaller/api/...
```

## Testing

### Test API Endpoints

```bash
# Health check
curl http://localhost:5000/plugin/languagePackInstaller/api/health

# List languages
curl http://localhost:5000/plugin/languagePackInstaller/api/listlanguages

# Get metadata
curl "http://localhost:5000/plugin/languagePackInstaller/api/getpackmetadata?languageCode=ru"

# Install language (POST)
curl -X POST "http://localhost:5000/plugin/languagePackInstaller/api/installpack?languageCode=ru"

# Remove language (POST)
curl -X POST "http://localhost:5000/plugin/languagePackInstaller/api/removepack?languageCode=ru"
```

### Test Through Reverse Proxy

```bash
# Replace localhost with your Pentaho server domain
curl https://pentaho.example.com/plugin/languagePackInstaller/api/health
```

### Test CLI

```bash
# List available languages
pentaho-langpack list

# Show info
pentaho-langpack info ru

# Install
pentaho-langpack install ru

# Verify installation
pentaho-langpack installed

# Remove
pentaho-langpack remove ru
```

### Test Dashboard

1. Log into Pentaho as admin
2. Navigate to: **Tools > Language Packs**
3. Select a language pack
4. Click "Install"
5. Verify installation completes successfully

## Monitoring

### Check Service Status

```bash
# systemd service
sudo systemctl status pentaho-langpack-api
sudo journalctl -u pentaho-langpack-api -f

# Docker
docker logs -f pentaho-langpack-api
```

### Check Logs

The API logs to stdout. Configure your service manager to capture logs:

```bash
# systemd
sudo journalctl -u pentaho-langpack-api

# Docker
docker logs pentaho-langpack-api
```

### Monitor Performance

```bash
# Check process
ps aux | grep gunicorn

# Check port
netstat -tulpn | grep 5000

# Check connections
ss -tn | grep 5000
```

## Troubleshooting

### API Not Starting

1. Check Python version:
   ```bash
   python3 --version  # Should be 3.7+
   ```

2. Check dependencies:
   ```bash
   pip list | grep -i flask
   ```

3. Check permissions:
   ```bash
   ls -la /opt/pentaho/pentaho-server/pentaho-solutions/system
   ```

4. Check logs:
   ```bash
   sudo journalctl -u pentaho-langpack-api -n 100
   ```

### Installation Fails

1. Check file permissions:
   ```bash
   # API user needs write access
   namei -l /opt/pentaho/pentaho-server/pentaho-solutions/system
   ```

2. Check disk space:
   ```bash
   df -h /opt/pentaho
   ```

3. Test with CLI for detailed errors:
   ```bash
   pentaho-langpack install ru -v
   ```

### Dashboard Not Connecting

1. Check reverse proxy configuration:
   ```bash
   # nginx
   sudo nginx -t
   curl http://localhost:5000/plugin/languagePackInstaller/api/health

   # Apache
   sudo apachectl configtest
   ```

2. Check CORS headers:
   ```bash
   curl -v -H "Origin: http://pentaho.example.com" \
     http://localhost:5000/plugin/languagePackInstaller/api/health
   ```

3. Check browser console for errors

### Language Pack Not Working After Installation

1. Restart Pentaho server:
   ```bash
   /opt/pentaho/pentaho-server/stop-pentaho.sh
   /opt/pentaho/pentaho-server/start-pentaho.sh
   ```

2. Clear Pentaho cache:
   ```bash
   rm -rf /opt/pentaho/pentaho-server/tomcat/work/*
   rm -rf /opt/pentaho/pentaho-server/tomcat/temp/*
   ```

3. Verify files were copied:
   ```bash
   find /opt/pentaho/pentaho-server/pentaho-solutions/system -name "*_ru.properties"
   ```

### Encoding Issues

If you see garbled characters:

1. Check source file encoding:
   ```bash
   file -i data/ru/system/*/resources/lang/messages_ru.properties
   ```

2. Verify conversion is enabled:
   ```python
   # In installer initialization
   installer = LanguagePackInstaller(..., convert_encoding=True)
   ```

3. Re-install with encoding conversion:
   ```bash
   pentaho-langpack remove ru
   pentaho-langpack install ru
   ```

## Security Considerations

### Production Deployment

1. **Run behind reverse proxy**: Don't expose the Python API directly
2. **Use HTTPS**: Configure SSL/TLS in nginx/Apache
3. **Restrict access**: Use firewall rules to limit access
4. **Run as dedicated user**: Don't run as root
5. **Enable authentication**: Add authentication middleware if needed

### Example Security Configuration

```bash
# Firewall (allow only from Pentaho server)
sudo ufw allow from 127.0.0.1 to any port 5000

# Run as pentaho user (not root)
sudo -u pentaho gunicorn api:app

# SELinux context (if using SELinux)
sudo chcon -R -t httpd_sys_content_t /opt/pentaho/pentaho-server
```

## Backup and Recovery

### Backup Before Installation

```bash
# Backup system directory
tar -czf pentaho-system-backup-$(date +%Y%m%d).tar.gz \
  /opt/pentaho/pentaho-server/pentaho-solutions/system

# Backup Tomcat lib
tar -czf pentaho-tomcat-lib-backup-$(date +%Y%m%d).tar.gz \
  /opt/pentaho/pentaho-server/tomcat/webapps/pentaho/WEB-INF/lib
```

### Recovery

```bash
# Remove language pack
pentaho-langpack remove ru

# Or restore from backup
tar -xzf pentaho-system-backup-20250101.tar.gz -C /
```

## Performance Tuning

### Gunicorn Workers

Adjust worker count based on CPU cores:

```bash
# Rule of thumb: (2 × CPU_cores) + 1
gunicorn -w 9 -b 127.0.0.1:5000 api:app  # For 4-core system
```

### Timeout Configuration

For large language packs:

```bash
gunicorn -w 4 -b 127.0.0.1:5000 --timeout 300 api:app
```

### Memory Usage

Monitor and adjust:

```bash
# Check memory usage
ps aux | grep gunicorn | awk '{sum+=$6} END {print sum/1024 " MB"}'
```

## Migration from Kettle Version

1. **Install Python version** alongside existing Kettle version
2. **Test thoroughly** with CLI
3. **Switch reverse proxy** to Python API
4. **Monitor for issues** for 24-48 hours
5. **Disable Kettle endpoints** once stable
6. **Remove Kettle dependencies** (optional)

No data migration needed - Python version uses the same `data/` directory!

## Support

For issues:
- Check logs: `sudo journalctl -u pentaho-langpack-api`
- Increase verbosity: Add `-v` flag to CLI commands
- GitHub Issues: https://github.com/lucasgdutra/pentahoLanguagePacks/issues

## Next Steps

After successful integration:

1. Test all supported languages
2. Update deployment documentation
3. Train administrators on CLI usage
4. Set up monitoring and alerts
5. Plan regular updates
