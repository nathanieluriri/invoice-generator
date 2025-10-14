# Stage 1: Use the official Python slim image as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies.
# We manually download wkhtmltopdf because it's no longer in the main Debian repos
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       wget \
       libxrender1 \
       libfontconfig1 \
       libxext6 \
       xz-utils \
    && wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && apt-get -f install -y \
    && rm wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]