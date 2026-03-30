# Base image for Python application (using Python 3.6.8)
FROM python:3.12.2

# Set working directory
WORKDIR /app

# Copy requirements.txt (if you have one)
COPY requirements.txt .

# Instalar librerías necesarias para Pillow con soporte WebP
RUN apt-get update && apt-get install -y \
    libwebp-dev gcc make \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port for the Flask app
EXPOSE 5000

# Define the Gunicorn entrypoint
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "anpr_webhook_app:app"]
