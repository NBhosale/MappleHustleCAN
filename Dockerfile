FROM python:3.11-slim

# Set working dir
WORKDIR /code

# Install system deps for psycopg2 & Postgres
RUN apt-get update && apt-get install -y gcc libpq-dev

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]