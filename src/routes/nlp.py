from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import JSONResponse
from helpers.config import Settings, get_settings
from routes.schemes.nlp import PushRequest, SearchRequest
from models import ProjectModel, ChunkModel
from models.enums import ResponseSignal
from controllers import NLPController
import logging
from tqdm.auto import tqdm

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/api/v1/nlp/index",
    tags=["api_v1", "nlp"]
)

@nlp_router.post("/push/{project_id}")
async def index_project(request: Request, 
                        project_id: str, 
                        push_request: PushRequest, 
                        app_settings: Settings = Depends(get_settings)):
    
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            }
        )
        
    nlp_controller = NLPController(
    vectordb_client=request.app.vectordb_client,
    generation_client=request.app.generation_client,
    embedding_client=request.app.embedding_client,
    template_parser=request.app.template_parser
)
    
    do_reset = push_request.do_reset    
    
    chunk_model = await ChunkModel.create_instance(request.app.db_client)
    
    inserted_items_count = 0
    page_no = 1
    has_records = True
    
    total_chunks_count = await chunk_model.get_total_chunks_count(project_id=project.id)
    pbar = tqdm(total=total_chunks_count, desc="Vector Indexing", position=0)
    
    while has_records:
        chunks = await chunk_model.get_chunks_by_project_id(chunk_project_id=project.id, 
                                                            page_no=page_no, 
                                                            page_size=app_settings.INDEXING_PAGE_SIZE)
        
        if not chunks or len(chunks) == 0:
            has_records=False
            break
                    
        is_inserted, collection_name = await nlp_controller.index_into_vector_db(
            project=project, chunks=chunks, do_reset=do_reset, batch_size=app_settings.INDEXING_PAGE_SIZE
        )
        
        do_reset=False
        
        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value
                }
            )
        
        pbar.update(len(chunks))
        inserted_items_count += len(chunks)
        page_no += 1
        
    return JSONResponse(
        content={
            "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESSS.value,
            "inserted_items_count": inserted_items_count,
            "collection_name": collection_name
        }
    )

    
    
@nlp_router.get("/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            }
        )
        
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )    
    collection_info, collection_name = await nlp_controller.get_vector_db_collection_info(project=project)
    
    if not collection_info:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.VECTORDB_COLLECTION_INFO_ERROR.value,
                "collection_name": collection_name
            }
    )
        
    return JSONResponse(
        content={
        "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
        "collection_name": collection_name,
        f"{nlp_controller.creat_collection_name(project_id=project.project_id)} info": collection_info
    }
)

@nlp_router.post("/search/{project_id}")
async def search_index(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            }
        )
        
    nlp_controller = NLPController(vectordb_client=request.app.vectordb_client,
                                   generation_client=request.app.generation_client,
                                   embedding_client=request.app.embedding_client,
                                   template_parser=request.app.template_parser)

    retrieved_documents = await nlp_controller.search_vector_db_collection(
        project=project, text=search_request.text, limit=search_request.limit
    )
    
    if not retrieved_documents or len(retrieved_documents) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value
            }
        )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "retrieved_documents": retrieved_documents
        }
    )
    
@nlp_router.post("/answer/{project_id}")
async def answer_rag(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            }
        )
        
    nlp_controller = NLPController(vectordb_client=request.app.vectordb_client,
                                   generation_client=request.app.generation_client,
                                   embedding_client=request.app.embedding_client,
                                   template_parser=request.app.template_parser)
    
    answer, full_prompt, messages = await nlp_controller.answer_rag_question(
        project=project, query=search_request.text, limit=search_request.limit
    )
    
    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.RAG_ANSWER_ERROR.value,
                "answer": answer,
                "full_prompt": full_prompt,
                "messages": messages
            }
        )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "messages": messages
        }
    )