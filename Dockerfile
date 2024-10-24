# Use an official Python runtime as a parent image
FROM python:3.12.7-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . /app

# Expose the port the app runs on (modify this based on your app's configuration)
EXPOSE 8000

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Run the application (modify this according to how you start your app)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
