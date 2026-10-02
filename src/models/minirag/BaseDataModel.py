from helpers.config import get_settings
from sqlalchemy.orm import sessionmaker

class BaseDataModel:
    def __init__(self, db_client: sessionmaker):
        self.app_settings = get_settings()
        self.db_client = db_client