from fastapi import FastAPI
from routes import base
from helpers.config import get_settings, Settings

print(Settings().APP_NAME)

print(Settings().APP_VERSION)

print(Settings().OPEN_API_KEY)

app=FastAPI()
app.include_router(base.base_router)

