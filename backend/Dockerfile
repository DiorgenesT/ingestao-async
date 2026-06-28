FROM python:3.12-slim AS deps
WORKDIR /deps
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS final
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
COPY --from=deps /install /usr/local
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY app/ ./app/
RUN adduser --disabled-password --gecos "" --uid 1001 appuser && chown -R appuser /app
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
