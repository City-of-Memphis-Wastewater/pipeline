# Use a slim Python 3.11 base image to keep the container small.
FROM python:3.11-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy only the files needed for dependency installation first.
# This leverages Docker's build cache, making subsequent builds faster.
COPY pyproject.toml poetry.lock ./

# Install Poetry in the container.
RUN pip install poetry

# Use Poetry to install all project dependencies.
# The --no-root flag ensures the project itself isn't installed as a package yet.
# The --only main flag installs only the main dependencies, not dev dependencies.
RUN poetry install --no-root --only main

# Copy the rest of your application code into the container.
COPY . .

# Expose any ports your application might need (e.g., for the Plotly web server).
EXPOSE 8000

# Set the entry point for the container.
# This defines the command that will run when the container starts.
# It uses the "eds" alias from your pyproject.toml file.
ENTRYPOINT ["poetry", "run", "eds"]