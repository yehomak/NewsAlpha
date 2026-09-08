FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# Install CPU-only torch first so sentence-transformers doesn't pull CUDA (~2GB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY pyproject.toml .
COPY app/ ./app/

RUN pip install --no-cache-dir .

COPY alembic/ ./alembic/
COPY alembic.ini .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
