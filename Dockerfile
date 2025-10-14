# Stage 1: Use the official Python slim image as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required by wkhtmltopdf
# wkhtmltopdf is needed by the pdfkit library to generate PDFs
RUN apt-get update \
    && apt-get install -y --no-install-recommends wkhtmltopdf \
    # Clean up the apt cache to keep the image size small
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir reduces image size, --upgrade pip ensures we have a modern pip
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
# This includes main.py, the 'templates' folder, and the 'static' folder
COPY . .

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application using uvicorn
# --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]