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

# Install additional dependencies directly with pip
RUN /app/.venv/bin/pip install PyJWT cryptography

# Copy source code
COPY src/ src/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV MCP_TRANSPORT=stdio
ENV ENABLE_AUTH=true

# Create non-root user for security
RUN useradd -r -s /bin/false mcpuser && \
    chown -R mcpuser:mcpuser /app
USER mcpuser

# Run the enhanced server with JWT authentication using the venv python
CMD ["/app/.venv/bin/python", "src/main_jwt.py"]