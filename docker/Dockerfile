FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /code/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --without dev

COPY app/ /code/app/
COPY alembic/ /code/alembic/
COPY alembic.ini /code/alembic.ini
COPY frontend/dist/ /code/frontend/dist/
COPY docker/entrypoint.sh /code/docker/entrypoint.sh
RUN chmod +x /code/docker/entrypoint.sh

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
