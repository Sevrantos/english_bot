#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h db -U postgres; do
    sleep 1
done

echo "Running database migrations..."
migrate -path migrations -database "${DATABASE_URL}" up

echo "Starting bot..."
python main.py