FROM python:3.11-slim

LABEL maintainer="zhenzhen"
LABEL description="Zhen AI Code Review - AI-powered code review agent"

WORKDIR /app

# Install git for repository operations
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir -e .

# Set entrypoint
ENTRYPOINT ["zhen-review"]
CMD ["--help"]
