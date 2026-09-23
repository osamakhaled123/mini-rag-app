from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from typing import List
from stores.llm.LLMEnums import DocumentTypeEnums
import json
from stores.llm.templates import TemplateParser
import logging

class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client, template_parser: TemplateParser):
        super().__init__()
        
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        self.logger = logging.getLogger("uvicorn.error")
        
    def creat_collection_name(self, project_id: str):
        return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()
    
    async def reset_vector_db_collection(self, project: Project):
        collection_name = self.creat_collection_name(project_id=project.project_id)
        await self.vectordb_client.delete_collection(collection_name=collection_name)
    
    async def get_vector_db_collection_info(self, project: Project):
        collection_name = self.creat_collection_name(project_id=project.project_id)
        collection_info = await self.vectordb_client.get_collection_info(collection_name=collection_name)
        
        if not collection_info:
            return None
        
        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        ), collection_name
            
    async def index_into_vector_db(self, project: Project, 
                                   chunks: List[DataChunk], 
                                   do_reset: bool=False, 
                                   batch_size: int = 100):
        #step_1: get collection_name
        collection_name = self.creat_collection_name(project_id=project.project_id)

        #step_2: manage_items
        texts = [chunk.chunk_text for chunk in chunks]
        chunk_ids = [str(chunk.id) for chunk in chunks]
        asset_ids = [str(chunk.chunk_asset_id) for chunk in chunks]
        metadatas = [chunk.chunk_metadata for chunk in chunks]
        
        print(len(texts))
        vectors = self.embedding_client.embed_texts(
            texts=texts, 
            documente_type=DocumentTypeEnums.DOCUMENT.value
        )
        if not vectors:
            return False, False
        
        #step_3: create collection if not exist
        _ = await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset 
        )
        
        #step_4: insert into vector database:
        if len(texts) == 1:
            _ = await self.vectordb_client.insert_one(
                collection_name=collection_name,
                text = texts[0],
                vector = vectors[0],
                metadata = metadatas[0],
                chunk_id = chunk_ids[0],
                asset_id = asset_ids[0]
                
            )
        
        else:
            _ = await self.vectordb_client.insert_many(
                collection_name=collection_name,
                texts = texts,
                vectors = vectors,
                metadatas = metadatas,
                chunks_ids = chunk_ids,
                asset_ids = asset_ids,
                batch_size=batch_size
            )    
    
        return True, collection_name
    
    
    async def search_vector_db_collection(self, project: Project, text: str, limit: int = 5):
        
        query_vector = None 
        collection_name = self.creat_collection_name(project_id=project.project_id)
        vectors = self.embedding_client.embed_texts(
            texts=text, documente_type=DocumentTypeEnums.QUERY.value
        )
        
        if not vectors or len(vectors) == 0:
            return None
        
        if isinstance(vectors, list) and len(vectors) > 0:
            query_vector = vectors[0]
        
        if not query_vector:
            return None
        
        retrieved_documents = await self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            limit=limit,
            vector=query_vector
        )
        
        if not retrieved_documents:
            return None

        return retrieved_documents
    
    async def answer_rag_question(self, project: Project, query: str, limit: int = 5): 
        
        #step_1: retrieve related documents
        retrieved_documents = await self.search_vector_db_collection(
            project=project, text=query, limit=limit
        )
        
        if not retrieved_documents or len(retrieved_documents) == 0:
            self.logger.error(f"No documents retrieved for project_id: {project.project_id} and query: {query}")
            return None, None, None

        system_prompt = self.template_parser.get(group="rag", key="system_prompt")
        
        document_prompt = "\n".join([
            self.template_parser.get(group="rag", key="document_prompt", vars={
                "doc_num": idx + 1,
                "chunk_text": self.generation_client.process_text(document["text"])
            })
            for idx, document in enumerate(retrieved_documents)
            ])
        
        footer_prompt = self.template_parser.get(group="rag", key="footer_prompt", vars={
            "query": query
        })
        
        messages = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value
            )
        ]
        
        full_prompt = "\n\n".join([document_prompt, footer_prompt])
        
        answer = self.generation_client.generate_texts(messages=messages, prompt=full_prompt)
        
        return answer, full_prompt, messages
    
    async def delete_vector_db_chunks_by_asset_id(self, project: Project, asset_id: str):#CHUNKS_IDS OR ASSET_IDS (SET(THE LIST))
        collection_name = self.creat_collection_name(project_id=project.project_id)
    
        counts = await self.vectordb_client.delete_by_id(
            collection_name=collection_name,
            asset_id=asset_id
        )
        
        return counts