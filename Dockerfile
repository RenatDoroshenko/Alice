# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Install SQLite library
RUN apt-get update && apt-get install -y libsqlite3-dev

# Copy the current directory contents into the container at /app
COPY . /app

# Copy the templates directory explicitly
COPY templates /app/templates

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run app.py when the container launches using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]
