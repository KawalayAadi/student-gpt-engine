# # app/config.py
# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     llm_base_url: str
#     llm_api_key: str
#     llm_model: str = "qwen/qwen3-30b-a3b-thinking-2507"
#     embedding_model: str = "text-embedding-3-small"
#     database_url: str
#     cache_similarity_threshold: float = 0.95
#     context_recent_turns: int = 4

#     class Config:
#         env_file = ".env"

# settings = Settings()
# app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    embedding_model: str
    database_url: str
    context_recent_turns: int = 4
    cache_similarity_threshold: float = 0.95
    
    model_config = SettingsConfigDict(env_file=".env", extra = "ignore")

settings = Settings()