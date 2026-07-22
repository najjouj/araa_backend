FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Railway/Render both set $PORT — bind to it rather than a hardcoded port.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
