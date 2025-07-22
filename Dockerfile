# Start from a standard, lightweight Python 3.10 image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# THE FIX IS HERE: Install git before trying to install Python packages
RUN apt-get update && apt-get install -y git

# Copy the files needed to install dependencies
COPY pyproject.toml .

# Install all dependencies from your pyproject.toml
RUN pip install .

# Copy the rest of your project's source code
COPY ./uc_intg_xbox ./uc_intg_xbox
COPY ./driver.json .

# The command to run your driver when the container starts
CMD ["python", "-m", "uc_intg_xbox.driver"]