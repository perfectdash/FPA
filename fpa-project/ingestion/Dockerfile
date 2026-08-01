FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# creating and adding a non - root user for the security hardening 
RUN adduser --disabled-password --no-create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

# Reading PORT from environment — Cloud Run injects this dynamically
ENV PORT=8080
EXPOSE 8080


# the amount of the works needs to be configured here as 
# the number of the vcpus are changed
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
