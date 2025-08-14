FROM python:3.11-slim

WORKDIR /app
COPY engine/ engine/
COPY api/ api/
RUN pip install --no-cache-dir -e engine -e api

CMD ["uvicorn", "api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
