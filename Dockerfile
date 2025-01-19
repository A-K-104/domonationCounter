# Use Python 3.12 slim image as base
FROM python:3.12-slim

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

# Copy only the files needed for installing dependencies
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-interaction --no-root

# Copy the rest of the application
COPY . .

# Install the project
RUN poetry install --no-interaction

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/instance && \
    chmod 777 /app/logs /app/instance

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=development
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=1
ENV PYTHONPATH=/app

# Run the application
CMD ["poetry", "run", "flask", "run", "--host=0.0.0.0", "--debug"]
