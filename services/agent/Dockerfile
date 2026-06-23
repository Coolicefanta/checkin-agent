FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# 复制代码
COPY services/agent/ services/agent/
COPY shared/ shared/

EXPOSE 8000

CMD ["uvicorn", "services.agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
