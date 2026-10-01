from fastapi import FastAPI
from routes import base, data, nlp
from contextlib import asynccontextmanager
from helpers.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
from stores.llm import LLMProviderFactory
from stores.llm.templates import TemplateParser
from stores.vectordb import VectorDBProviderFactory
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to PostgreSQL...")
    
    settings = get_settings()
    
    postgres_connection = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    
    app.db_engine = create_async_engine(url=postgres_connection)
    app.db_client = sessionmaker(bind=app.db_engine, class_=AsyncSession, expire_on_commit=False)
    
    print(f"Connected to PostgreSQL Database: '{settings.POSTGRES_MAIN_DATABASE}'")#Complete
    
    print("\n")
    
    #########################################################################################    
    llm_provider_factory = LLMProviderFactory(config=settings)
    
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)
    
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                             embedding_size=settings.EMBEDDING_SIZE)
    
    #########################################################################################
    vectordb_provider_factory = VectorDBProviderFactory(config=settings)
    app.vectordb_client = vectordb_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)
    
    await app.vectordb_client.connect()
    print(f"Connected to VectorDB: '{settings.VECTOR_DB_BACKEND}'")
    
    #########################################################################################
    app.template_parser = TemplateParser(default_language=settings.DEFAULT_LANG, language=settings.PRIMARY_LANG)
    
    try:
        yield
    finally:
        
        print("Closing PostgreSQL connection...")
        app.db_engine.dispose()
        print("PostgreSQL connection cleanly closed.")
        #############################################################
        print(f"Closing VectorDB {settings.VECTOR_DB_BACKEND} connection...")
        await app.vectordb_client.disconnect()
        print(f"{settings.VECTOR_DB_BACKEND} VectorDB connection cleanly closed.")
             
             
app = FastAPI(lifespan=lifespan)             

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
