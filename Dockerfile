# Use a slim base image for Python 3.12
FROM python:3.12-slim

# Set a working directory inside the container
WORKDIR /app

# Install system dependencies needed for PySide and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxkbcommon-x11-0 \
    libxcb-util1 \
    libgl1-mesa-glx \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and poetry.lock first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install project dependencies using Poetry
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the project files
COPY . .

# Expose any necessary ports (optional, adjust based on your app's needs)
EXPOSE 5000

# Set the default command to run your PySide application
CMD ["poetry", "run", "python", "app/main.py"]
