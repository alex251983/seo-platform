#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import asyncio, asyncpg, os, sys

async def wait():
    url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
    for i in range(30):
        try:
            conn = await asyncpg.connect(url)
            await conn.close()
            print('Database ready')
            return
        except Exception as e:
            print(f'Attempt {i+1}/30: {e}')
            await asyncio.sleep(2)
    print('Database not available after 60s')
    sys.exit(1)

asyncio.run(wait())
"

echo "Running migrations..."
alembic upgrade head

echo "Starting app..."
exec "\$@"
