import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="NVIDIA NIM API Gateway", version="1.0.0")

# Point the Langchain client to the local/self-hosted NIM endpoint.
# In a load-balanced setup, this points to your NGINX Load Balancer.
NIM_BASE_URL = os.getenv("NIM_BASE_URL", "http://localhost:8000/v1")
NIM_API_KEY = os.getenv("NIM_API_KEY", "dummy-key-for-local") # NIM container expects some API key or 'none'

client = ChatNVIDIA(
    model="moonshotai/kimi-k2.5",
    api_key=NIM_API_KEY,
    base_url=NIM_BASE_URL,
    temperature=1,
    top_p=1,
    max_completion_tokens=16384,
)

class ChatRequest(BaseModel):
    messages: list
    stream: bool = True

async def stream_generator(messages):
    try:
        # Using astream for async concurrent streaming support
        async for chunk in client.astream(messages, chat_template_kwargs={"thinking": True}):
            # Stream reasoning content if available
            if chunk.additional_kwargs and "reasoning_content" in chunk.additional_kwargs:
                reasoning = chunk.additional_kwargs['reasoning_content'].replace('\n', '\\n')
                yield f"data: {{\"type\": \"reasoning\", \"content\": \"{reasoning}\"}}\n\n"
            
            # Stream typical content
            if chunk.content:
                content = chunk.content.replace('\n', '\\n')
                yield f"data: {{\"type\": \"content\", \"content\": \"{content}\"}}\n\n"
                
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"content\": \"{str(e)}\"}}\n\n"

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    """
    Handle incoming chat completion requests and forward them to the NVIDIA NIM nodes
    via async streaming.
    """
    if req.stream:
        return StreamingResponse(
            stream_generator(req.messages), 
            media_type="text/event-stream"
        )
    else: # Non-streaming call
        try:
            response = await client.ainvoke(req.messages, chat_template_kwargs={"thinking": True})
            reasoning = response.additional_kwargs.get("reasoning_content", "")
            return {
                "content": response.content,
                "reasoning_content": reasoning
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}