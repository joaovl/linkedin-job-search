# Custom n8n image with Python support
FROM n8nio/n8n:latest

# Switch to root to install packages
USER root

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

# Install Python dependencies for the scraper and Excel support
RUN pip3 install --break-system-packages requests beautifulsoup4 openpyxl

# Switch back to node user for security
USER node
