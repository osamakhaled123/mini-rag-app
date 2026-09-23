from abc import ABC, abstractmethod
from typing import List
from models.db_schemes import RetrievedDocument

class VectorDBInterface(ABC):
    
    @abstractmethod
    async def connect(self):
        pass
        
        
    @abstractmethod
    async def disconnect(self):
        pass
    
    
    @abstractmethod
    async def is_collection_exist(self, collection_name: str) -> bool:
        pass
    
    
    @abstractmethod
    async def list_all_collections(self) -> List:
        pass
    

    @abstractmethod
    async def delete_collection(self, collection_name: str):
        pass


    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> dict:
        pass

    
    @abstractmethod
    async def create_collection(self, collection_name: str, 
                          embedding_size: int, 
                          do_reset: bool = False):
        pass
    
    
    @abstractmethod
    async def insert_one(self, collection_name: str,
                   text: str,
                   vector: List,
                   metadata: dict = None,
                   record_id: str = None):
        pass
    
    
    @abstractmethod
    async def insert_many(self, collection_name: str,
                    text: List, 
                    vectors: List,
                    metadatas: List = None,
                    record_ids: List = None, 
                    batch_size: int = 50):
    
        pass
    
    
    @abstractmethod
    async def search_by_vector(self, collection_name: str,
                         vector: list,
                         limit: int) -> List[RetrievedDocument]:
        
        pass