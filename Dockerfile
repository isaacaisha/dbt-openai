# DOCKERFILE

# Use an official Python runtime as a parent image
FROM python:3.12.0

# Set the working directory in the container
WORKDIR /usr/src/app

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    libnss3 \
    libxss1 \
    libappindicator1 \
    fonts-liberation \
    xdg-utils \
    libasound2 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libgtk-4-1 \
    libu2f-udev \
    libvulkan1 \
    libxkbcommon0 \
    ffmpeg

# Download and install specific version of Chromium (adjust version as needed)
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb && \
    apt-get install -y -f && \
    rm google-chrome-stable_current_amd64.deb

# Download and install specific version of Chromedriver (adjust version as needed)
RUN wget https://chromedriver.storage.googleapis.com/93.0.4577.63/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip -d /usr/src/app && \
    rm chromedriver_linux64.zip && \
    chmod +x /usr/src/app/chromedriver

# Debug step: List contents of installation directories
RUN ls -l /usr/src/app && \
    ls -l /usr/src/app/chromedriver && \
    ls -l /usr/bin/google-chrome

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Define environment variables
ENV PORT=8000
ENV CHROME_BINARY_PATH="/usr/bin/google-chrome"
ENV CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"

# Expose the specified port
EXPOSE 8000

# Run the specified command within the container
CMD ["uvicorn", "main:asgi_app", "--host", "0.0.0.0", "--port", "8000"]
