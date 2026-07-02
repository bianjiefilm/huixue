#!/bin/bash
set -e

echo "Waiting for database..."
# Simple wait loop using python
python3 -c "
import time
import socket
import os
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL', 'postgresql://huixue:huixue_password@huixue-db:5432/huixue')
if 'sqlite' in db_url:
    print('Using SQLite, no wait needed.')
    exit(0)

parsed = urlparse(db_url)
host = parsed.hostname
port = parsed.port or 5432

print(f'Waiting for {host}:{port}...')
for i in range(30):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((host, port))
        s.close()
        print('Database is ready!')
        exit(0)
    except Exception as e:
        # print(e)
        time.sleep(2)
print('Database timeout!')
exit(1)
"

echo "Initializing database schema and admin user..."
python3 init_db.py

echo "Seeding training resources..."
# Run the seeder module
# Ensure we are in the backend root
cd /app
python3 -m app.utils.training_resource_seeder

echo "Production initialization complete!"

