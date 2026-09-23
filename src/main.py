from fastapi import FastAPI
from routes import base, data, nlp
from contextlib import asynccontextmanager
from helpers.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
from stores.llm import LLMProviderFactory
from stores.llm.templates import TemplateParser
from stores.vectordb import VectorDBProviderFactory

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to MongoDB...")
    
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]
    
    print(f"Connected to Document Database: '{settings.MONGODB_DATABASE}'")
    
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
        
        print("Closing MongoDB connection...")
        app.mongo_conn.close()
        print("MongoDB connection cleanly closed.")
        #############################################################
        print(f"Closing VectorDB {settings.VECTOR_DB_BACKEND} connection...")
        await app.vectordb_client.disconnect()
        print(f"{settings.VECTOR_DB_BACKEND} VectorDB connection cleanly closed.")
             
             
app = FastAPI(lifespan=lifespan)             

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
