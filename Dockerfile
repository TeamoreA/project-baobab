# Use the official Python base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY src ./src
COPY migrations ./migrations
COPY app.py app.py

# Command to run the Flask application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3000", "app:app"]
