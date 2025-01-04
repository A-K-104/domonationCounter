# Use Python 3.8 slim image as base
FROM python:3.8-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . .

# Install the project
RUN poetry install --no-interaction

# Create logs directory and set permissions
RUN mkdir -p /app/logs && \
    chmod 777 /app/logs

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production

# Run the application
CMD ["poetry", "run", "python", "app.py"]
