# Use a slim Python 3.11 base image to keep the container small.
FROM python:3.11-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy all project files into the container. This includes src/, pyproject.toml, etc.
# This must be done before 'poetry install' so it can find the source code.
COPY . .

# Install Poetry in the container.
RUN pip install poetry

# Use Poetry to install all project dependencies and the project itself.
# This creates an editable install, making the 'pipeline' module available.
RUN poetry install

# Expose any ports your application might need (e.g., for the Plotly web server).
EXPOSE 8000

# Set the entry point for the container.
# This defines the command that will run when the container starts.
# It uses the "eds" alias from your pyproject.toml file.
ENTRYPOINT ["poetry", "run", "eds"]