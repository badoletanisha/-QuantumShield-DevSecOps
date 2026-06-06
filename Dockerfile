# Lightweight Python base image
FROM python:3.10-alpine

# Set working directory
WORKDIR /app

# Copy dependencies first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app code
COPY . .

# Open port 5000
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]
