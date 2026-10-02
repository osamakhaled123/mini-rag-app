from minirag.schemes import DataChunk
from .BaseDataModel import BaseDataModel
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func, delete
from sqlalchemy.dialects.postgresql import UUID

class ChunkModel(BaseDataModel):
    def __init__(self, db_client: sessionmaker):
        super().__init__(db_client=db_client)
        
    @classmethod    
    async def create_instance(cls, db_client: sessionmaker):
        instance = cls(db_client=db_client)
        return instance
        
    async def create_chunk(self, chunk: DataChunk):
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
            await session.commit()
            await session.refresh(chunk)
        
        return chunk
        
    async def get_chunk(self, chunk_id: str):
        async with self.db_client() as session:
            async with session.begin():
                query = select(DataChunk).where(DataChunk.id == chunk_id)
                chunk = await session.execute(query).scalar_one_or_none()
        
        return chunk
        
    async def insert_many_chunks(self, chunks: list, batch_size: int=100):
        async with self.db_client() as session:
            async with session.begin():
                for chunk in range(0, len(chunks), batch_size):
                    batch = chunks[chunk: chunk + batch_size]   
                    session.add_all(batch)   
                
                await session.commit()  
        return len(chunks)
    
    async def delete_chunks_by_project_id(self, project_id: UUID):
        async with self.db_client() as session:
            async with session.begin():
                query = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                execution = await session.execute(query)
                await session.commit()
        return execution.rowcount
    
    async def get_chunks_by_project_id(self, chunk_project_id: UUID, 
                                       page_no: int=1, page_size: int = 150):
        async with self.db_client() as session:
            async with session.begin():
                cursor = select(DataChunk).where(DataChunk.chunk_project_id == chunk_project_id).offset(
                    (page_no - 1) * page_size
                ).limit(page_size)
                
                execution = await session.execute(cursor)
                batch = execution.scalars().all()
        
        return batch    
                
    async def delete_chunks_by_asset_id(self, asset_id: UUID):
        async with self.db_client() as session:
            async with session.begin():
                query = delete(DataChunk).where(DataChunk.chunk_asset_id == asset_id)
                deleted_records = await session.execute(query)
        return deleted_records.rowcount
        
    
    async def get_total_chunks_count(self, project_id: UUID):
        async with self.db_client() as session:
            async with session.begin():
                query = select(func.count(DataChunk.id)).where(DataChunk.chunk_project_id == project_id)
                num_records = await session.execute(query).scalar()
        return num_records