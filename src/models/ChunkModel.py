from .enums.DataBaseEnum import DataBaseEnum
from .db_schemes import DataChunk
from .BaseDataModel import BaseDataModel
from bson.objectid import ObjectId
from pymongo import InsertOne

class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
        
    async def create_chunk(self, chunk: DataChunk):
        record = await self.collection.insert_one(
            chunk.model_dump(by_alias=True, exclude_unset=True)
            )
        chunk.id = record.inserted_id
        
        return chunk
    
    async def get_chunk(self, chunk_id: str):
        record = await self.collection.find_one({
            "_id": ObjectId(chunk_id)
        })
        
        if record is None:
            return None
        
        return DataChunk(**record)
    
        
    async def insert_many_chunks(self, chunks: list, batch_size: int=100):
        for chunk in range(0, len(chunks), batch_size):
            batch = chunks[chunk: chunk + batch_size]
    
            operations=[
                InsertOne(chunk_.model_dump(
                    by_alias=True, exclude_unset=True
                ))
                for chunk_ in batch
            ]
            
            await self.collection.bulk_write(operations)
            
        return len(chunks)
    
    
    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        records = await self.collection.delete_many({
            "chunk_project_id":project_id
        })
        
        return records.deleted_count
    