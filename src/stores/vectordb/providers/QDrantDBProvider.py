from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import VectorDBEnums, DistanceMethodEnums
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct, FilterSelector, Filter, FieldCondition, MatchValue
import logging
from typing import List
from models.db_schemes import RetrievedDocument
from datetime import datetime, UTC
from uuid import uuid4
from fastapi.encoders import jsonable_encoder

class QDrantDBProvider(VectorDBInterface):
    def __init__(self, db_client: str, 
                 distance_method: str = None, 
                 default_vector_size: int = 786, 
                 index_threshold: int = 100):
        
        self.db_client = db_client
        self.distance_mehtod = None
        self.client = None
        self.collection_ids={}
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold
        
        if DistanceMethodEnums.DOT.value == distance_method:
            self.distance_mehtod = Distance.DOT
        
        elif DistanceMethodEnums.COSINE.value == distance_method:
            self.distance_mehtod = Distance.COSINE
        
        self.logger = logging.getLogger(__name__)
    
    async def connect(self):
        self.client = QdrantClient(path=self.db_client)
        
    async def disconnect(self):
        self.client = None
        
    async def get_collection_last_record_id(self, collection_name: str):
        if not await self.is_collection_exist(collection_name=collection_name):
            self.collection_ids[collection_name] = 0
            return 0
        
        records, _ = self.client.scroll(
            collection_name=collection_name,
            limit=1,
            with_payload=True,
            with_vectors=False,
            order_by=models.OrderBy(
                key="inserted_at",
                direction=models.Direction.DESC
            )
        )

        if not records:
            return 0
        
        last_record_indexed_id = records[0].id
        
        self.collection_ids[collection_name] = last_record_indexed_id
        return last_record_indexed_id
    
    async def is_collection_exist(self, collection_name: str) -> bool:
        if not self.client:
            self.logger.error(f"Client of {VectorDBEnums.QDRANT.value} is disconnected")
            return None
        
        if not collection_name or len(collection_name) == 0:
            self.logger.error("collection name sent is empty")
            return None
        
        return self.client.collection_exists(collection_name=collection_name)
    
    async def list_all_collections(self) -> List:
        if not self.client:
            self.logger.error(f"Client of {VectorDBEnums.QDRANT.value} is disconnected")
            return None
                
        return self.client.get_collections()

    async def delete_collection(self, collection_name: str):
        if not self.client:
            self.logger.error(f"Client of {VectorDBEnums.QDRANT.value} is disconnected")
            return None
        
        if await self.is_collection_exist(collection_name=collection_name):       
            self.logger.error(f"Deleting collection: {collection_name}") 
            return self.client.delete_collection(collection_name=collection_name)
        
        else:
            self.logger.error(f"{collection_name} collection is not exist")
            return None

    async def get_collection_info(self, collection_name: str) -> dict:
        if not self.client:
            self.logger.error(f"Client of {VectorDBEnums.QDRANT.value} is disconnected")
            return None
        
        if await self.is_collection_exist(collection_name=collection_name):         
            return self.client.get_collection(collection_name=collection_name)
        
        else:
            self.logger.error(f"{collection_name} collection is not exist")
            return None

    async def create_collection(self, collection_name: str, 
                          embedding_size: int, 
                          do_reset: bool = False):
        if not self.client:
            self.logger.error(f"Client of {VectorDBEnums.QDRANT.value} is disconnected")
            return None
        
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)
            
        if await self.is_collection_exist(collection_name=collection_name):
            return None

        self.default_vector_size = embedding_size
        self.collection_ids[collection_name] = 0
                
        self.logger.info(f"Creating a Qdrant collection: {collection_name}")
        self.client.create_collection(collection_name=collection_name,
                                      vectors_config=VectorParams(size=embedding_size, 
                                                                  distance=self.distance_mehtod))
        
        self.client.create_payload_index(
            collection_name=collection_name,
            field_name="asset_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        self.client.create_payload_index(
            collection_name=collection_name,
            field_name="chunk_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        return True
    
    async def insert_one(self, collection_name: str,
                   text: str,
                   vector: List,
                   chunk_id: str,
                   asset_id: str,
                   metadata: dict = None):
        
        if not self.client:
            self.logger.error(f"Client of {VectorDBEnums.QDRANT.value} is disconnected")
            return None
        
        if not collection_name or len(collection_name) == 0:
            self.logger.error("collection name sent is empty")
            return None
        
        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return None
        
        if not text or len(text) == 0:
            self.logger.error("text passed is empty")
            return None
        
        if len(vector) == 0:
            self.logger.error(f"Vextor list passed to be inserted in VectorDB {VectorDBEnums.QDRANT.value} is empty")
            return None
        
        #ids = await self.get_collection_last_record_id(collection_name=collection_name) + 1
        try:
            _ = self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(id=str(uuid4()),
                                vector=vector,
                                payload={"text": text,
                                        "metadata": metadata,
                                        "inserted_at": datetime.now(UTC).timestamp(),
                                        "chunk_id": chunk_id,
                                        "asset_id": asset_id
                                }
                            )
                ]
            )
        
            self.collection_ids[collection_name] += 1
            
        except Exception as e:
            self.logger.error(f"Error while inserting vector: {e}")
            return False
            
        return True
        
    async def insert_many(self, collection_name: str,
                    texts: List, 
                    vectors: List,
                    chunks_ids: List[str],
                    asset_ids: List[str],
                    metadatas: List = None,
                    batch_size: int = 100
            ):
        
        if not self.client:
            self.logger.error(f"Client of {VectorDBEnums.QDRANT.value} is disconnected")
            return None
        
        if not collection_name or len(collection_name) == 0:
            self.logger.error("collection name sent is empty")
            return None
        
        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return None
        
        if len(texts) == 0:
            self.logger.error("text passed is empty")
            return None
        
        if len(vectors) == 0:
            self.logger.error(f"Vextor list passed to be inserted in VectorDB {VectorDBEnums.QDRANT.value} is empty")
            return None
        
        if not metadatas:
            metadatas = [None] * len(texts)

        #ids = await self.get_collection_last_record_id(collection_name=collection_name) + 1
        
        #record_ids = list(range(ids, ids + len(texts)))
        
        try:
            for i in range(0, len(texts), batch_size):
                batch_vectors = vectors[i:i + batch_size]
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                #batch_record_ids = record_ids[i:i + batch_size]# SUBSTITUTE WITH UUID4
                batch_chunks_ids = chunks_ids[i:i + batch_size] if chunks_ids else [None] * len(batch_texts)
                batch_asset_ids = asset_ids[i:i + batch_size] if asset_ids else [None] * len(batch_texts)
                
                batch_points=[      #id=batch_record_ids[idx]...Updated
                        PointStruct(id=str(uuid4()),
                                    vector=batch_vectors[idx],
                                    payload={
                                        "text": batch_texts[idx],
                                        "metadatas": batch_metadatas[idx],
                                        "inserted_at": datetime.now(UTC).timestamp(),
                                        "chunk_id": batch_chunks_ids[idx],
                                        "asset_id": batch_asset_ids[idx]
                                    })
                        for idx in range(len(batch_texts))
                ]
                
                _ = self.client.upsert(collection_name=collection_name, points=batch_points)

            self.collection_ids[collection_name] += len(texts)
            
        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

            
        return True
    
    
    async def search_by_vector(self, collection_name: str,
                         vector: list,
                         limit: int) -> List[RetrievedDocument]:

        if not self.client:
            self.logger.error(f"Client of {VectorDBEnums.QDRANT.value} is disconnected")
            return None
        
        if not collection_name or len(collection_name) == 0:
            self.logger.error("collection name sent is empty")
            return None
        
        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return None
        
        if len(vector) == 0:
            self.logger.error(f"Vextor list passed to be inserted in VectorDB {VectorDBEnums.QDRANT.value} is empty")
            return None  
        
        if limit <= 0:
            self.logger.error(f"limit {limit} passed is not a positive number") 
            return None
        
        search_results = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            with_payload=True,
            limit=limit
        ).points
        
        if not search_results or len(search_results) == 0:   
            return []
           
        #UPDATE RetrievedDocument to catch (Optionally) all payload contents in QDRANT (BESIDES TEXT AND SCORE)   
        return jsonable_encoder([RetrievedDocument(**{"text": result.payload["text"],
                                     "score": result.score,
                                     "inserted_at": result.payload["inserted_at"],
                                     "chunk_id": result.payload["chunk_id"],
                                     "asset_id": result.payload["asset_id"],
                                     "id": result.id
                                     })
                for result in search_results])

    async def delete_by_id(self, collection_name: str, asset_id: str):
        if not self.client:
            self.logger.error(f"Client of {VectorDBEnums.QDRANT.value} is disconnected")
            return None

        if not collection_name or len(collection_name) == 0:
            self.logger.error("collection name sent is empty")
            return None
        
        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not delete a non-existed collection: {collection_name}")
            return None
        
        delete_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="asset_id", 
                    match=models.MatchValue(value=str(asset_id))
                )
            ]
        )
        
        pre_count = self.client.count(
            collection_name=collection_name,
            count_filter=delete_filter
        ).count
        
        if pre_count > 0:
            try:
                _ = self.client.delete(
                    collection_name=collection_name,
                    wait=True,
                    points_selector=FilterSelector(
                        filter=Filter(
                            must=[
                                FieldCondition(
                                    key="asset_id",
                                    match=MatchValue(
                                        value=str(asset_id)#IT MUST BE VALUES(asset record)
                                    )
                                )
                            ]
                        )
                    )
                )

            except Exception as e:
                self.logger.error(f"Error while deleting {asset_id}: {e}")
                return None
            
            #return True
            post_count = self.client.count(
                collection_name=collection_name,
                count_filter=delete_filter
            ).count

            return (pre_count - post_count)
        
        else:
            self.logger.error(f"No vetor embedding to delete related to {asset_id}")
            return None