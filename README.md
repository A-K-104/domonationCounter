# Domonation Counter

A web application for managing and tracking area control games, also known as domonation.

## Features

- Track game progress
- View game statistics
- Manage game records

## Setup

### Using Poetry
1. Clone the repository
2. Install Poetry if you haven't already: `curl -sSL https://install.python-poetry.org | python3 -`
3. Install dependencies: `poetry install`
4. Run the application: `poetry run flask run`

### Using Docker
1. Build the Docker image: `docker build -t domonation-counter .`
2. Run the container: `docker run -p 5000:5000 domonation-counter`
3. Access the application at `http://localhost:5000`

### Using Docker Compose (Recommended)
1. Start the application and database: `docker-compose up -d`
2. Access the application at `http://localhost:5000`
3. Stop the application: `docker-compose down`

## Project Structure

- `static/` - Contains CSS and other static assets
- `templates/` - Contains HTML templates
- `app.py` - Main application file
- `Dockerfile` - Docker container configuration
- `docker-compose.yml` - Multi-container Docker configuration

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## License

This project is licensed under the MIT License.
