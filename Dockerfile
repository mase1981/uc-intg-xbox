# Start from a lightweight Python image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install the project and all its dependencies from pyproject.toml
# This will also install xbox-webapi from GitHub
RUN pip install .

# The command to run when the container starts
CMD ["python", "-m", "uc_intg_xbox.driver"]