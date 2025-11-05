FROM python:3.11-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python application
COPY python/ /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose API port
EXPOSE 5000

# Set environment variables
ENV PLUGIN_DIR=/opt/pentaho/pentaho-server/pentaho-solutions/system/languagePackInstaller
ENV PENTAHO_BASE_DIR=/opt/pentaho/pentaho-server
ENV PORT=5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/plugin/languagePackInstaller/api/health || exit 1

# Run gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "300", "api:app"]
