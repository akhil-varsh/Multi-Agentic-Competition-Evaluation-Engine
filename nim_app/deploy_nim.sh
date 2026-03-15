#!/bin/bash

# NVIDIA NIM MoonshotAI/Kimi-k2.5 Self-Hosted Deployment Script
# This script deploys multiple NVIDIA NIM nodes locally for load balancing

# Check if NGC_API_KEY is provided
if [ -z "$NGC_API_KEY" ]; then
    echo "Error: NGC_API_KEY environment variable is not set."
    echo "Please set it using: export NGC_API_KEY=<your_api_key>"
    exit 1
fi

export LOCAL_NIM_CACHE=~/.cache/nim
mkdir -p "$LOCAL_NIM_CACHE"
chmod -R a+w "$LOCAL_NIM_CACHE"

echo "Logging into NVIDIA Container Registry (nvcr.io)..."
echo "$NGC_API_KEY" | docker login nvcr.io -u '$oauthtoken' --password-stdin

# Define how many nodes to run (e.g., 3 nodes for load balancing configuration)
NODE_COUNT=3
BASE_PORT=8000

for ((i=1; i<=NODE_COUNT; i++))
do
    NODE_PORT=$((BASE_PORT + i))
    echo "Deploying NVIDIA NIM Node $i on port $NODE_PORT..."

    # Starting container in detached mode (-d)
    docker run -d --rm \
        --name "nim-moonshot-node-$i" \
        --gpus all \
        --ipc host \
        --shm-size=32GB \
        -e NGC_API_KEY="$NGC_API_KEY" \
        -v "$LOCAL_NIM_CACHE:/opt/nim/.cache" \
        -p $NODE_PORT:8000 \
        nvcr.io/nim/moonshotai/kimi-k2.5:latest

    echo "Node $i started. Target: http://localhost:$NODE_PORT/v1/chat/completions"
done

echo "----------------------------------------"
echo "All NIM nodes have been started!"
echo "Check container logs using: docker logs -f nim-moonshot-node-1"
echo "Nginx will load balance across these ports as configured in nginx/nginx.conf."
