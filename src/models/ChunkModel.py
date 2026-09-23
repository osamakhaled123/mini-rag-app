from .enums.DataBaseEnum import DataBaseEnum
from .db_schemes import DataChunk
from .BaseDataModel import BaseDataModel
from bson.objectid import ObjectId
from pymongo import InsertOne

class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
        
    @classmethod    
    async def create_instance(cls, db_client: object):
        instance = cls(db_client=db_client)
        await instance.init_collection()
        return instance
        
    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()  #useless
        if DataBaseEnum.COLLECTION_CHUNK_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
            indexes = DataChunk.get_indexes()
            
            for index in indexes:
                self.collection.create_index(
                    keys=index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )
    
        
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
    
    async def get_chunks_by_project_id(self, chunk_project_id: ObjectId, 
                                       page_no: int=1, page_size: int = 150):
        
        cursor = self.collection.find({
                "chunk_project_id": chunk_project_id
            }).skip(
                (page_no - 1) * page_size
            ).limit(page_size)
        
        batch = []    
        async for record in cursor:
            batch.append(
                DataChunk(**record)
            )
        
        return batch
    
    async def delete_chunks_by_asset_id(self, asset_id: ObjectId):
        records = await self.collection.delete_many({
            "chunk_asset_id":asset_id
        })
        return records.deleted_count
    
    async def get_total_chunks_count(self, project_id: ObjectId):
        num_records = await self.collection.count_documents(
            {"chunk_project_id": project_id}
        )
        
        if not num_records:
            num_records = 0
            
        return num_records