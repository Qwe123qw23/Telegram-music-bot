# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install ffmpeg, build tools and other necessary packages
RUN apt-get update && apt-get install -y ffmpeg build-essential libopus-dev libogg-dev python3-dev && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install setuptools and wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
# EXPOSE 80

# Run bot.py when the container launches
CMD ["python3", "bot.py"]
