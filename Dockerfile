FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY . .

# Set the Python Path so it can find your backend modules
ENV PYTHONPATH=/app

# Force the start command to use your specific routes file
CMD ["uvicorn", "backend.api.routes:app", "--host", "0.0.0.0", "--port", "8080"]
