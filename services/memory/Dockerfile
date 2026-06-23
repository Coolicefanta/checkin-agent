FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY services/memory/ services/memory/
COPY shared/ shared/

EXPOSE 8002

CMD ["uvicorn", "services.memory.main:app", "--host", "0.0.0.0", "--port", "8002"]
