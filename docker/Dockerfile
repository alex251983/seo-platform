FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Копируем зависимости и устанавливаем их (кэшируется отдельно)
COPY pyproject.toml poetry.lock* /code/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# === КОПИРУЕМ КОД ПРИЛОЖЕНИЯ ===
COPY app/ /code/app/
COPY alembic/ /code/alembic/
COPY alembic.ini /code/alembic.ini

# === КОПИРУЕМ ФРОНТЕНД ===
COPY frontend/dist/ /code/frontend/dist/

# === КОПИРУЕМ ENTRYPOINT (раскомментируйте, если используете) ===
# COPY docker/entrypoint.sh /code/entrypoint.sh
# RUN chmod +x /code/entrypoint.sh

EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
