# Use slim Python image for small final size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install bash and curl (useful for debugging/healthchecks)
RUN apt-get update && apt-get install -y bash curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast dependency installer)
RUN pip install --no-cache-dir uv

# Copy only dependency metadata first (enables Docker layer caching)
COPY pyproject.toml uv.lock README.md ./

# Install project dependencies from lockfile (frozen = reproducible)
# --no-dev skips dev dependencies (equivalent to Poetry's --without dev)
RUN uv sync --frozen --no-dev

# Now copy the actual source code
COPY src/ ./src/

# Optional: copy any other needed files (e.g., data, config)
# COPY . .

# Expose port if your app runs a server (e.g., FastAPI/Flask)
EXPOSE 8000

# Run the CLI entrypoint using uv (equivalent to "poetry run eds")
ENTRYPOINT ["uv", "run", "eds"]

# Default command (can be overridden)
CMD ["--help"]
