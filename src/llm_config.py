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


# from langchain_openai import ChatOpenAI
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # The gateway IP handling the 6 NIM Docker nodes
# NIM_CLUSTER_URL = "http://localhost:8080/v1" 

# def get_llm():
#     """
#     Returns the configured LLM for general text and evaluation via the NIM Cluster.
#     """
#     return ChatOpenAI(
#         model="moonshotai/kimi-k2.5",     # Use the Docker image model name
#         base_url=NIM_CLUSTER_URL,
#         api_key="dummy-key",              # NIM accepts any non-empty string locally
#         temperature=0.6,
#         model_kwargs={"response_format": {"type": "json_object"}},
        
#         # Token Limits Update:
#         max_tokens=32768,                 # Replaces Ollama's 'num_predict'
#     )

# def get_multimodal_llm():
#     """
#     Returns the configured LLM capable of processing images via the NIM Cluster.
#     """
#     return ChatOpenAI(
#         model="moonshotai/kimi-k2.5",
#         base_url=NIM_CLUSTER_URL,
#         api_key="dummy-key",
#         temperature=0.6,
        
#         # Token Limits Update:
#         max_tokens=32768,                 # Adjust max output tokens
#         # Note: NIM automatically handles max context window limits natively 
#         # based on VRAM constraints (no need for Ollama's 'num_ctx')
#     )