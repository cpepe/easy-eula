import os
import json
from typing import Optional, Dict, Any

from easy_eula_webapp.harness.llm import LLMProvider

class Agent:
    """An agent encompasses a specific persona/role, an LLM Provider, and instructions."""
    
    def __init__(self, role: str, prompt_template_path: str, provider: LLMProvider):
        self.role = role
        self.provider = provider
        self.prompt_template = self._load_prompt(prompt_template_path)
        
    def _load_prompt(self, filename: str) -> str:
        # Resolve from `easy_eula_webapp/agent_policies` securely
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, 'agent_policies', filename)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

class Task:
    """A task bounds the execution of an agent given a specific expected output schema."""
    
    def __init__(self, agent: Agent, expected_schema: Optional[Dict[str, Any]] = None):
        self.agent = agent
        self.expected_schema = expected_schema
        
    def execute(self, context: dict) -> Any:
        prompt = self.agent.prompt_template.format(**context)
        return self.agent.provider.generate(prompt, schema=self.expected_schema)
