#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import socket, time
for i in range(30):
    try:
        s = socket.create_connection(("postgres", 5432), timeout=2)
        s.close()
        break
    except:
        time.sleep(2)
"
echo "Database ready"
echo "Running migrations..."
alembic upgrade head
echo "Starting app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
