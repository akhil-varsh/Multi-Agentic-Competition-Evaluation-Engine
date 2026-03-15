# Scalable NVIDIA NIM Inference Gateway

This directory contains a highly scalable proxy and load balancer configuration designed to serve 200 concurrent requests against a self-hosted implementation of **NVIDIA NIM `moonshotai/kimi-k2.5`**.

## Architecture Overview

1. **Client Request Layer**: FastAPI application serving on `0.0.0.0:8080`.
    * Implemented with `Gunicorn` and `Uvicorn` workers for native multi-threaded async request handling.
    * Uses LangChain's async stream generation functionality (`.astream()`) via `langchain-nvidia-ai-endpoints`.
2. **Load Balancer Layer**: Nginx serving on `127.0.0.1:8000`.
    * Distributes incoming LLM loads across multiple downstream Nvidia NIM nodes using the `least_conn` directive.
    * Specifically tuned with `proxy_buffering off;` and large timeouts for uninterrupted token streaming.
3. **NVIDIA NIM Compute Layer**: Dockerized Self-Hosted Models serving on `8001`, `8002`, `8003`, etc.
    * Fully parallelized GPU instances serving `moonshotai/kimi-k2.5`.

## Prerequisites
* Linux environment with Docker and NVIDIA Container Toolkit installed
* Valid `NGC_API_KEY` (NVIDIA API Key) setup
* Properly configured NVIDIA GPUs (e.g., A100s, H100s) with enough aggregate VRAM for the models.

## Setup Instructions

### 1. Install Gateway Requirements
Navigate to this directory and install Python dependencies.
```bash
cd nim_app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Deploy the NVIDIA NIM Nodes
Run the automated bash script that starts multiple NIM containers locally to handle concurrency. You can adjust `NODE_COUNT` in the script according to your hardware.

```bash
export NGC_API_KEY="<your-api-key>"
chmod +x deploy_nim.sh
./deploy_nim.sh
```

### 3. Start NGINX Load Balancer & FastAPI Gateway
Once the NIM containers have fully spun up and loaded their optimized engines (verify with `docker logs -f nim-moonshot-node-1`), start the load balancer and gateway layer:

```bash
chmod +x deploy_gateway.sh
./deploy_gateway.sh
```

## Testing Your Topology
The FastAPI gateway will be accessible on `http://localhost:8080`.

You can test a high-concurrency request via:
```bash
curl -X 'POST' \
  'http://localhost:8080/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "What is in this image?"
      }
    ],
    "stream": true
}'
```

By firing concurrently against port `:8080`, the traffic routes: `Client -> FastAPI Gateway (Gunicorn x8) -> Nginx Loadbalancer -> NIM Container (3+ Nodes)`.