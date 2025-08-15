# LedgAI Enhanced QuantConnect MCP Server with JWT Authentication
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv and dependencies
RUN pip install uv PyJWT cryptography

# Copy dependency files
COPY pyproject.toml .

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

# Run the enhanced server with JWT authentication
CMD ["python", "src/main_jwt.py"]