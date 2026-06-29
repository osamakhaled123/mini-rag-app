from fastapi import FastAPI
from routes import base, data
from contextlib import asynccontextmanager
from helpers.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to MongoDB...")
    
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]
    
    print(f"Connected to database: '{settings.MONGODB_DATABASE}'")
    
    try:
        yield

    finally:
        print("Closing MongoDB connection...")
        app.mongo_conn.close()
        print("MongoDB connection cleanly closed.")       
        

app = FastAPI(lifespan=lifespan)             

app.include_router(base.base_router)
app.include_router(data.data_router)
