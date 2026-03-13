from langchain_ollama import ChatOllama
import os
from dotenv import load_dotenv

# Load environment variables from .env file (useful for LangSmith tracing)
load_dotenv()

# For ollama locally, base_url is usually http://localhost:11434

def get_llm():
    """
    Returns the configured LLM for general text and evaluation.
    """
    return ChatOllama(
        model="kimi-k2.5:cloud",
        temperature=0.6, # Fixed at 0.6 per Kimi-K2.5 non-thinking spec for stable output
        format="json", # Ensure model adheres to structured output
        num_predict=32768, # Kimi supports up to 65.5K, using a safe 32K output limit
        num_ctx=131072, # Provide a massive context window for large evaluation tasks
    )

def get_multimodal_llm():
    """
    Returns the configured LLM capable of processing images.
    """
    return ChatOllama(
        model="kimi-k2.5:cloud",
        temperature=0.6,
        num_ctx=262144, # Instruct Ollama to utilize Kimi's full 262K context window natively for heavy images
    )
