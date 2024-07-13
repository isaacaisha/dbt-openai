# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.12.0

# Set the working directory in the container
WORKDIR /usr/src/app

# Install Chrome and Chromedriver dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    libnss3 \
    libxss1 \
    libappindicator1 \
    fonts-liberation \
    xdg-utils

# Download and install specific version of Chromium
RUN wget https://example.com/path/to/chrome-linux64.zip && \
    unzip chrome-linux64.zip -d /usr/src/app/chrome && \
    mv /usr/src/app/chrome/chrome-linux64 /usr/src/app/chrome/chromium && \
    ln -s /usr/src/app/chrome/chromium/chrome /usr/bin/chromium && \
    rm chrome-linux64.zip

# Download and install specific version of Chromedriver
RUN wget https://example.com/path/to/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip -d /usr/src/app/chromedriver && \
    mv /usr/src/app/chromedriver/chromedriver-linux64/chromedriver /usr/local/bin && \
    rm chromedriver-linux64.zip

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Define environment variables
ENV PORT=8000
ENV CHROME_BINARY_PATH="/usr/src/app/chrome/chromium/chrome"
ENV CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"

# Expose the specified port
EXPOSE 8000

# Run the specified command within the container
CMD ["uvicorn", "main:asgi_app", "--host", "0.0.0.0", "--port", "8000"]
