import yaml
import os
from pydantic import BaseModel, Field
from typing import Optional

class LLMConfig(BaseModel):
    service_type: str = Field(default="openai", description="Service type: openai, local, etc.")
    base_url: str = Field(default="http://localhost:1234/v1", description="LLM API Base URL")
    api_key: Optional[str] = Field(default=None, description="API Key")
    timeout: int = Field(default=60, description="Request timeout in seconds")

class ModelConfig(BaseModel):
    name: str = Field(default="text-embedding-qwen3-embedding-4b", description="Model name")
    context_window: int = Field(default=4096, description="Context window size")
    temperature: float = Field(default=0.7, description="Generation temperature")

class ProcessingConfig(BaseModel):
    chunk_count: int = Field(default=5, description="Number of chunks to split the file into")

class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)

def load_config(config_path: str) -> AppConfig:
    if not os.path.exists(config_path):
        # If config file doesn't exist, return default
        return AppConfig()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data:
        return AppConfig()
        
    return AppConfig(**data)
