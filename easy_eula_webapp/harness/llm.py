import abc
import json
from typing import Dict, Any, Optional

from google import genai
from google.genai import types
import ollama

class LLMProvider(abc.ABC):
    """Abstract base class for LLM Providers."""
    
    @abc.abstractmethod
    def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Any:
        """
        Generates text from the LLM. 
        If schema is provided, the provider must structure the output as JSON and validate/load it.
        """
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=api_key)
        
    def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Any:
        config = types.GenerateContentConfig()
        if schema:
            config.response_mime_type = "application/json"
            config.response_schema = schema
            
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=config
        )
        
        text = response.text
        if schema:
            try:
                data = json.loads(text)
                return data
            except json.JSONDecodeError:
                raise ValueError(f"Failed to decode JSON from Gemini. Raw text: {text}")
        return text

class OllamaProvider(LLMProvider):
    def __init__(self, host: str, model: str):
        self.client = ollama.Client(host=host)
        self.model = model
        
    def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Any:
        try:
            options = {}
            if schema:
                options['format'] = 'json'
                # Append a strict instruction to abide by the schema
                prompt += "\n\nIMPORTANT: Return strictly valid JSON that matches the following schema:\n"
                prompt += json.dumps(schema, indent=2)

            response = self.client.generate(
                model=self.model, 
                prompt=prompt,
                format=options.get('format', "")
            )
            text = response['response']
            
            if schema:
                try:
                    data = json.loads(text)
                    return data
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to decode JSON from Ollama. Raw text: {text}")
            return text
        except Exception as e:
            raise ValueError(f"Ollama generation failed: {e}")
