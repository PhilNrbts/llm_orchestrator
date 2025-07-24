# Use a slim Python base image
FROM python:3.11-slim

# Set the working directory to the root
WORKDIR /

# Install system dependencies that some libraries might need
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY ./app /app
COPY models.yaml .

# Mount point for host filesystem access
VOLUME /workspace

# Expose the port the app runs on
EXPOSE 8000

# The command to run the application
ENTRYPOINT ["uvicorn", "app.orchestrator:app", "--host", "0.0.0.0", "--port", "8000"]

