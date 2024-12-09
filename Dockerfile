# Use an official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies if needed (e.g. for psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
# Ensure you have generated a minimal requirements.txt using pipreqs or similar
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Use environment variables from the container’s environment
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
