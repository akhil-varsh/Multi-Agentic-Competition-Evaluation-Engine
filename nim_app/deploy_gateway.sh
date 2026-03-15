#!/bin/bash

# Start the Nginx Load Balancer
echo "Starting Nginx Load Balancer..."
docker run --name nginx-nim-lb -d \
    -p 8000:8000 \
    -v $(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
    --network host \
    nginx:latest

# Start the FastAPI Application with Gunicorn and Uvicorn workers for concurrency
# Using 4-8 workers depending on your CPU cores is standard.
# This setup handles the 200 concurrent requests smoothly.
echo "Starting FastAPI Gateway Layer (serving 200 concurrent requests)..."
export NIM_BASE_URL="http://127.0.0.1:8000/v1"
export NIM_API_KEY="dummy-key-for-local"

# Bind FastAPI onto port 8080 (client applications connect here)
# -k uvicorn.workers.UvicornWorker allows async serving
# --workers 8 allows utilizing multiple cores
gunicorn main:app \
    --workers 8 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8080 \
    --timeout 300 \
    --keep-alive 65
