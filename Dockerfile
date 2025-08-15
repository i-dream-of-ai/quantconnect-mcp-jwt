# LedgAI Enhanced QuantConnect MCP Server with JWT Authentication
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .

# Generate lock file and install dependencies
RUN uv lock
RUN uv sync --frozen

# Copy source code
COPY src/ src/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV MCP_TRANSPORT=stdio
ENV ENABLE_AUTH=true

# Create non-root user for security and setup cache directory
RUN useradd -r -s /bin/false mcpuser && \
    mkdir -p /home/mcpuser/.cache && \
    chown -R mcpuser:mcpuser /app /home/mcpuser
USER mcpuser

# Run the HTTP health check server (for DigitalOcean)
# The actual MCP server will be started separately via supervisor or as a sidecar
CMD ["uv", "run", "python", "src/http_server.py"]