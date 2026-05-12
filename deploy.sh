#!/bin/bash
set -e
cd ~/seo-platform

echo "🔄 Pull from GitHub..."
git pull origin master

echo "🔨 Rebuild API..."
docker compose build --no-cache api

echo "🗄️ Run migrations..."
docker compose exec -T api alembic upgrade head

echo "🔄 Restart services..."
docker compose up -d

sleep 5
echo "✅ Health check:"
curl -s https://seoviden.ru/health
