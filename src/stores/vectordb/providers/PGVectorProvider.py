from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import (
    VectorDBEnums, DistanceMethodEnums, 
    PGVectorTableSchemeEnums, PGVectorDistanceMethodEnums,
    PGVectorSimilaritySearchMethodEnums, IndexingTypeEnums
)
from models.enums import DataBaseEnum
import logging
from typing import List
from models.minirag.schemes import RetrievedDocument
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text as sql_text
import json

class PGVectorProvider(VectorDBInterface):
    def __init__(self, db_client: sessionmaker, 
                 embedding_size: int, 
                 distance_method: str, 
                 index_threshold: int,
                 indexing_type: str,
                 default_vector_size: int = 786):
        
        self.db_client = db_client
        self.embedding_size = embedding_size, 
        self.distance_method = distance_method
        self.index_threshold = index_threshold
        self.default_vector_size = default_vector_size
        self.prefix_name = VectorDBEnums.PGVECTOR.value
        self.logger = logging.getLogger("uvicorn")
        self.indexing_type = indexing_type
        
        self.default_index_name = lambda collection_name: f"{collection_name}_vector_idx"
        
        if DistanceMethodEnums.DOT.value == distance_method:
            self.distance_mehtod = PGVectorDistanceMethodEnums.DOT.value
            self.similarity_search_method = PGVectorSimilaritySearchMethodEnums.DOT.value
                
        elif DistanceMethodEnums.COSINE.value == distance_method:
            self.distance_mehtod = PGVectorDistanceMethodEnums.COSINE.value
            self.similarity_search_method = PGVectorSimilaritySearchMethodEnums.COSINE.value
        
        elif DistanceMethodEnums.MANHATTAN.value == distance_method:
            self.distance_mehtod = PGVectorDistanceMethodEnums.MANHATTAN.value
            self.similarity_search_method = PGVectorSimilaritySearchMethodEnums.MANHATTAN.value
        
        elif DistanceMethodEnums.EUCLIDEAN.value == distance_method:
            self.distance_mehtod = PGVectorDistanceMethodEnums.EUCLIDEAN.value
            self.similarity_search_method = PGVectorSimilaritySearchMethodEnums.EUCLIDEAN.value
        
        else:
            self.distance_mehtod = None
            self.similarity_search_method = None
            self.logger.error("No distance method or similarity search method is passed correctly")
            
    
    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                query = sql_text("CREATE EXTENSION IF NOT EXISTS vector")
                await session.execute(query)
        await session.commit()
            
    async def disconnect(self):
        pass
    
    async def is_collection_exist(self, collection_name: str) -> bool:
        if not collection_name or len(collection_name) == 0:
            self.logger.error(f"collection name ({collection_name}) sent is empty")
            return None
        
        async with self.db_client() as session:
            async with session.begin():
                query = sql_text("SELECT tablename from pg_tables where tablename == :collection_name")
                result = await session.execute(query, {"collection_name": collection_name})
                record = result.scalar_one_or_none()
        
        return record
    
    async def list_all_collections(self) -> List:
        records = []
        async with self.db_client() as session:
            async with session.begin():
                query = sql_text(f"SELECT tablename from pg_tables where tablename LIKE :prefix")
                execution = await session.execute(query, {"prefix": self.prefix_name})
                records = execution.scalars().all()
        return records

    async def delete_collection(self, collection_name: str):
        is_exist = await self.is_collection_exist(collection_name=collection_name)
        if not is_exist:
            self.logger.error(f"{collection_name} collection to be deleted is not exist")
            return None
        
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")
                
                query = sql_text(f"DROP TABLE IF EXISTS {collection_name}")
                await session.execute(query)
                await session.commit()
        
        return True
                
    async def get_collection_info(self, collection_name: str) -> dict:
        is_exist = await self.is_collection_exist(collection_name=collection_name)
        if not is_exist:
            self.logger.error(f"{collection_name} collection is not exist")
            return None
            
        async with self.db_client() as session:
            async with session.begin():
                query = sql_text("SELECT schemename, tablename, tableowner, tablespace, hasindexes "
                                 "from pg_tables "
                                 "where tablename = :collection"
                                 )
                execution = await session.execute(query, {"collection": collection_name})
                
                count_query = sql_text(f"SELECT COUNT(*) FROM {collection_name}")
                count_query_execution = await session.execute(count_query)
                
                table_data = execution.fetchone() 
                table_count = count_query_execution.scalar_one()
                
                return {
                    "table_info":{
                        "schemename": table_data[0],
                        "tablename": table_data[1],
                        "tableowner": table_data[2],
                        "tablespace": table_data[3],
                        "hasindexes": table_data[4]
                    },
                    
                    "table_count": table_count
                }
            
    
    async def create_collection(self, collection_name: str, 
                            embedding_size: int, 
                            do_reset: bool = False):
        
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)
        
        else:
            is_collection_exist = self.is_collection_exist(collection_name=collection_name)
            if is_collection_exist:
                self.logger.error(f"{collection_name} collection is already exist")
                return False
                            
        async with self.db_client() as session:
            async with session.begin():
                create_extension_query = sql_text("CREATE EXTENSION IF NOT EXISTS pgcrypto")
                await session.execute(create_extension_query)
                
                query = sql_text(
                    f"CREATE TABLE {collection_name} ("
                    f"{PGVectorTableSchemeEnums.ID.value} UUID PRIMARY KEY DEFAULT gen_random_uuid(), "
                    f"{PGVectorTableSchemeEnums.TEXT.value} text, "
                    f"{PGVectorTableSchemeEnums.VECTOR.value} vector({embedding_size}), "
                    f"{PGVectorTableSchemeEnums.CHUNK_ID.value} UUID, "
                    f"{PGVectorTableSchemeEnums.ASSET_ID.value} UUID, "
                    f"{PGVectorTableSchemeEnums.METADATA.value} jsonb \'{{}}'\, "
                    f"FOREIGN KEY ({PGVectorTableSchemeEnums.CHUNK_ID.value}) REFERENCES {DataBaseEnum.COLLECTION_CHUNK_NAME.value}({PGVectorTableSchemeEnums.ID.value}) "
                    ")"
                )
                
                self.logger.info(f"Creating a {self.prefix_name} collection: {collection_name}")
                await session.execute(query)
                await session.commit()
        return True
    
    async def insert_one(self, collection_name: str,
                    text: str,
                    vector: List,
                    metadata: dict = None,
                    chunk_id: str = None,
                    asset_id: str = None):
        
        if not collection_name or len(collection_name) == 0:
            self.logger.error(f"collection name ({collection_name}) sent is empty")
            return None
        
        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return None
        
        if not text or len(text) == 0:
            self.logger.error("text passed is empty")
            return None
        
        if len(vector) == 0:
            self.logger.error(f"Vextor list passed to be inserted in VectorDB {self.prefix_name} is empty")
            return None
        
        async with self.db_client() as session:
            async with session.begin():
                query = sql_text(f"INSERT INTO {collection_name} "
                                 f"({PGVectorTableSchemeEnums.TEXT.value}, {PGVectorTableSchemeEnums.VECTOR.value}, {PGVectorTableSchemeEnums.METADATA.value}, {PGVectorTableSchemeEnums.ASSET_ID.value}, {PGVectorTableSchemeEnums.CHUNK_ID.value}) "
                                 "VALUES(:text, :vector, :metadata, :asset_id, :chunk_id)"
                                )
                
                metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata is not None else "{}"
                vector_ = "[" + ",".join([str(num) for num in vector]) + "]"
                
                await session.execute(query, {
                    "text": text,
                    "vector": vector_,
                    "metadata": metadata_json,
                    "asset_id": asset_id,
                    "chunk_id": chunk_id
                })
                
                await session.commit()
                
        return True
    
    async def insert_many(self, collection_name: str,
                        texts: List, 
                        vectors: List,
                        chunks_ids: List[str],
                        asset_ids: List[str],
                        metadatas: List = None,
                        batch_size: int = 100
                ):
        
        if not collection_name or len(collection_name) == 0:
            self.logger.error("collection name sent is empty")
            return None
        
        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return None
        
        if len(texts) == 0:
            self.logger.error("text passed is empty")
            return None
        
        if len(vectors) == 0 or len(vectors) < len(texts):
            self.logger.error(f"Vextor list passed to be inserted in VectorDB {self.prefix_name} is empty or less than number of texts")
            return None
        
        if not metadatas:
            metadatas = [None] * len(texts)
        
        elif len(metadatas) < len(texts):
            difference = len(texts) - len(metadatas)
            metadatas.extend([None] * difference)    
        
        metadatas_json = [json.dumps(metadata, ensure_ascii=False) if metadata is not None else "{}" for metadata in metadatas]
        vectors_list = ["[" + ",".join([str(num) for num in vector]) + "]" for vector in vectors]
            
        async with self.db_client() as session:
            async with session.begin():
               for batch in range(0, len(texts), batch_size):
                    batch_texts = texts[batch: batch + batch_size]
                    batch_vectors = vectors_list[batch: batch + batch_size]
                    batch_metadatas = metadatas_json[batch: batch + batch_size]
                    batch_chunks_ids = chunks_ids[batch: batch + batch_size] if chunks_ids else [None] * len(batch_texts)
                    batch_asset_ids = asset_ids[batch: batch + batch_size] if asset_ids else [None] * len(batch_texts)
                    
                    values = []
                    
                    for _text, _vector, _metadata, _chunk_id, _asset_id in zip(batch_texts, batch_vectors, batch_metadatas, batch_chunks_ids, batch_asset_ids):
                        values.append({
                            "text": _text,
                            "vector": _vector,
                            "metadata": _metadata,
                            "asset_id": _asset_id,
                            "chunk_id": _chunk_id
                            }
                        )
                    
                    batch_insert_query = sql_text(
                        f"INSERT INTO {collection_name} ( "
                        f"{PGVectorTableSchemeEnums.TEXT.value}, {PGVectorTableSchemeEnums.VECTOR.value}, {PGVectorTableSchemeEnums.METADATA.value}, {PGVectorTableSchemeEnums.ASSET_ID.value}, {PGVectorTableSchemeEnums.CHUNK_ID.value}"
                        f") "
                        f"VALUES (:text, :vector, :metadata, :asset_id, :chunk_id) "
                    )
                    
                    await session.execute(batch_insert_query, values)
                    await session.commit()
        
        return True
    

    async def search_by_vector(self, collection_name: str,
                            vector: list,
                            limit: int) -> List[RetrievedDocument]:
        
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not search for records in a non-existed collection: {collection_name}")
            return False
        
        vector_ = "[" + ",".join([ str(v) for v in vector ]) + "]"
        
        async with self.db_client() as session:
            async with session.begin():
                query = sql_text(
                    f"SELECT {PGVectorTableSchemeEnums.TEXT.value} as text, 1- ({PGVectorTableSchemeEnums.VECTOR.value} {self.similarity_search_method} :vector) as score "
                    f"FROM {collection_name} "                                 # (VECTOR <=> :ve)
                    "ORDER BY score DESC "
                    f"limit {limit} "
                )
                
                result = await session.execute(query, {
                    "vector": vector_
                })
                
                records = result.fetchall()
                
                return[
                    RetrievedDocument(
                        text=rec.text,
                        score=rec.score
                    )
                    for rec in records
                ]
                
    
    async def is_index_exist(self, collection_name: str):
        index_name = self.default_index_name(collection_name=collection_name)
        async with self.db_client() as session:
            async with session.begin():
                query = sql_text(
                    "SELECT 1 "
                    "FROM pg_indexes "
                    f"where indexname = :index_name "
                    f"and tablename = :collection_name "
                )
                
                result = await session.execute(query, {"collection_name": collection_name,
                                                       "index_name": index_name})
            
        return result.scalar_one_or_none()
            
    async def create_vector_index(self, collection_name: str, index_type: str = None):
        if await self.is_index_exist(collection_name=collection_name):
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                count_sql_query = sql_text(
                    "SELECT COUNT(*) "
                    f"FROM {collection_name} "
                )
                result = await session.execute(count_sql_query)
                count_result = result.scalar_one()
                
                if count_result < self.index_threshold:
                    return False
                
                index_name = self.default_index_name(collection_name=collection_name)
                indexing_type = self.indexing_type if index_type is None else index_type
                
                self.logger.info(f"START: Creating vector index ({index_name}) for collection: {collection_name}")
                
                creating_index_query = sql_text(
                    f"CREATE INDEX {index_name} on {collection_name} "
                    f"USING index {indexing_type} ({PGVectorTableSchemeEnums.VECTOR.value} {self.distance_method})"
                )
                
                await session.execute(creating_index_query)
                await session.commit()
                
                self.logger.info(f"END: Created vector index ({index_name}) for collection: {collection_name}")
    
    async def reset_vector_index(self, collection_name: str, index_type: str):
        async with self.db_client() as session:
            async with session.begin():
                    index_name = self.default_index_name(collection_name=collection_name)
                    delete_index_query = sql_text(
                        f"DROP INDEX IF EXISTS {index_name}"
                   )
                    await session.execute(delete_index_query)
                    await session.commit()

        await self.create_vector_index(collection_name=collection_name, index_type=index_type)
                
    
    async def delete_by_id(self, collection_name: str, asset_id: str):
        async with self.db_client() as session:
            async with session.begin():
                query = sql_text(
                    f"DELETE FROM {collection_name} " 
                    f"WHERE {PGVectorTableSchemeEnums.ASSET_ID} = :asset_id"
                )
                
                await session.execute(query, {"asset_id": asset_id})
                await session.commit()