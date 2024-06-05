# Use an official Python runtime as a parent image
FROM python:3.12.0

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Define environment variable
ENV PORT 8000

# Run the specified command within the container
CMD ["uvicorn", "main:asgi_app", "--host", "0.0.0.0", "--port", "8000"]
