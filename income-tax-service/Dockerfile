# ---- income-tax-service image ----
# Small official Python base image
FROM python:3.12-slim

# Don't write .pyc files, flush logs straight to stdout (so `docker logs` / `kubectl logs` show them)
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first -> this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the source code
COPY . .

# Run as a non-root user (security best practice)
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

# gunicorn = production WSGI server (Flask's built-in server is only for development)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
