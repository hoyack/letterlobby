FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for psycopg2, wkhtmltopdf, cups, and debugging tools
RUN apt-get update && apt-get install -y \
    libpq-dev gcc wkhtmltopdf cups libcups2-dev cups-client curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
