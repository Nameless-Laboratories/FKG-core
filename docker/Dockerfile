FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY schemas/ ./schemas/
COPY config/ ./config/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash fkg
USER fkg

EXPOSE 8000

CMD ["fkg", "serve", "--host", "0.0.0.0", "--port", "8000"]
