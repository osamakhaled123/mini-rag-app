from abc import ABC, abstractmethod
from typing import List
from models.minirag.schemes import RetrievedDocument

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
                   chunk_id: str,
                   asset_id: str,
                   metadata: dict = None):
        pass
    
    
    @abstractmethod
    async def insert_many(self, collection_name: str,
                    texts: List, 
                    vectors: List,
                    chunks_ids: List[str],
                    asset_ids: List[str],
                    metadatas: List = None,
                    batch_size: int = 100
            ):
    
        pass
    
    
    @abstractmethod
    async def search_by_vector(self, collection_name: str,
                         vector: list,
                         limit: int) -> List[RetrievedDocument]:
        
        pass
    
    @abstractmethod
    async def delete_by_id(self, collection_name: str, asset_id: str):
        pass