FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY services/tool_api/ services/tool_api/
COPY shared/ shared/

EXPOSE 8001

CMD ["uvicorn", "services.tool_api.main:app", "--host", "0.0.0.0", "--port", "8001"]
