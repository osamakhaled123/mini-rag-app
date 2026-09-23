from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int #MB
    
    FILE_DEFAULT_CHUNK_SIZE: int #512 KB
    
    MONGODB_URL: str
    MONGODB_DATABASE: str
    
    INDEXING_PAGE_SIZE: int #BATCH_SIZE
    
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str
    COHER_API_KEY: str

    GENERATION_MODEL_ID: str
    EMBEDDING_MODEL_ID: str
    EMBEDDING_SIZE: int

    INPUT_DEFAULT_MAX_CHARACTERS: int
    GENERATION_DAFAULT_MAX_TOKENS: int
    GENERATION_DAFAULT_TEMPERATURE: float
    
    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    VECTOR_DB_DISTANCE_METHOD: str

    PRIMARY_LANG: str
    DEFAULT_LANG: str
    
    class Config:
        env_file=".env"

def get_settings():
    return Settings()        