import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "ollama")
    OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
    # OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'mistral:latest')
