from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
import os
from controllers import DataController, ProjectController, ProcessController, NLPController
from models.enums import ResponseSignal, AssetTypeEnum
import aiofiles
import logging
from .schemes.data import ProcessingRequest, AssetDeletionRequest
from models import ProjectModel, ChunkModel, AssetModel
from models.db_schemes import DataChunk, Asset 

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=['api_v1', 'data']
)

@data_router.post("/upload/{project_id}")
async def upload_file(request: Request,
                      project_id: str, 
                      file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    data_controller = DataController()
    
    is_valid, result_signal = data_controller.validate_data(file = file)
     
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":result_signal
            }
        )
    
    file_path, file_id = data_controller.generate_unique_file_path(
                file_name=file.filename,
                project_id=project_id)
    
    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk:= await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
        
    except Exception as e:
            logger.error(f"Error while uploading file: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal":ResponseSignal.FILE_UPLOAD_FAILED.value
                }
            )
      
    #store the assets into the database
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    
    asset_resource = Asset(
            asset_project_id=project.id,
            asset_name=file_id,
            asset_type=AssetTypeEnum.FILE.value,
            asset_size=os.path.getsize(file_path)
        )
    
    
    asset_record = await asset_model.create_asset(asset=asset_resource)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal":ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id" : str(asset_record.id)
        }
    )        
    
    
    
@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, 
                           project_id: str, 
                           process_request: ProcessingRequest
                           ):
    
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )
    process_controller = ProcessController(project_id=project_id)

    if do_reset == 1:
        collection_name = nlp_controller.creat_collection_name(project_id=project.project_id)
        _ = await nlp_controller.vectordb_client.delete_collection(collection_name=collection_name)
        
        _ = await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )   
    
    no_records=0
    processed_files=0
     
    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.id,
            asset_name=process_request.file_id
        )
        
        if not asset_record:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "signal":ResponseSignal.FILE_ID_ERROR.value
                }
        )
            
        project_files_ids = {
            asset_record.id: asset_record.asset_name
        }
    
    else:
        project_files = await asset_model.get_all_project_id_assets(
                                            asset_project_id=project.id, 
                                            asset_type=AssetTypeEnum.FILE.value)
        project_files_ids={
            asset.id: asset.asset_name
            for asset in project_files
        }
    
    if len(project_files_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.NO_FILES_ERROR.value
            }
        )
        
    for asset_id, file_id in project_files_ids.items():
                                            
        file_content = process_controller.get_file_content(file_id=file_id)
        
        if file_content is None:
            logger.error(f"Error while processing file: {file_id}")
            continue
        
        file_chunks = process_controller.process_file_content(
            file_id=file_id,
            file_content=file_content,
            chunk_size=chunk_size,
            overlap_size=overlap_size
            )
        
        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "signal": ResponseSignal.PROCESSING_FAILED.value
                }
            )     
        
        
        
        file_chunks_records = [
            DataChunk(chunk_text=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                    chunk_order=i+1,
                    chunk_project_id=project.id,
                    chunk_asset_id=asset_id)
            for i, chunk in enumerate(file_chunks)
        ]
        
        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        processed_files += 1
        
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "signal":ResponseSignal.FILE_PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": processed_files
        }
    )
    
    
@data_router.delete("/delete/{project_id}")
async def delete_file(request: Request,
                      project_id: str, 
                      delete_asset_request: AssetDeletionRequest):
    
    asset_name = delete_asset_request.asset_name
    file = delete_asset_request.file
    documentDB=delete_asset_request.documentDB
    vectorDB=delete_asset_request.vectorDB
    chunks=delete_asset_request.chunks
        
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)
    asset_record = await asset_model.get_asset_record(
        asset_project_id=project.id,
        asset_name=asset_name
    )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
        template_parser=request.app.template_parser
    )
    
    if not asset_record:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal":ResponseSignal.NO_FILES_ERROR.value,
                "asset_name": asset_name
            }
        )
        
    responses = []    
    project_controller = ProjectController()
    print(f"PROJECT_ID: {project.id}")

    if file:
        file_path = os.path.join(
            project_controller.get_project_path(project_id=project_id),
            asset_name
        )

        if os.path.exists(file_path):
            os.remove(file_path)
            responses.append({
                "signal":ResponseSignal.DOCUMENT_DELETED_FROM_DISK.value,
                "file_id": str(asset_record.id)
            })
        else:        
            responses.append({
                "signal":ResponseSignal.NO_FILES_ERROR.value,
                "file_id": str(asset_record.id)
            })
                  
    if documentDB:
        #ASSET REMOVING PROCESS FROM ASSET COLLECTION IN DATABASE
        is_deleted = await asset_model.delete_asset_record(
            asset_project_id=project.id, 
            asset_id = asset_record.id
        )
        
        if is_deleted > 0:
            responses.append({
                "signal":ResponseSignal.DOCUMENT_ASSET_DELETED_FROM_DATABASE.value,
                "file_id": str(asset_record.id)
            })
        
        else:
            responses.append({
            "signal":ResponseSignal.DOCUMENT_ASSET_DELETED_FROM_DATABASE_ERROR.value,
            "file_id": str(asset_record.id)
        })
        
        #RELATED CHUNKS REMOVING
        deleted_count = await chunk_model.delete_chunks_by_asset_id(asset_id=asset_record.id)
       
        if deleted_count > 0:
            responses.append({
                "signal":ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_DATABASE.value,
                "file_id": str(asset_record.id),
                "assets_chunks_deleted": deleted_count
            })
        
        else:
            responses.append({
                "signal":ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_DATABASE_ERROR.value,
                "file_id": str(asset_record.id)
            })
    
        #RELATED EMBEDDINGS CHUNKS REMOVING
        deleted_count = await nlp_controller.delete_vector_db_chunks_by_asset_id(project=project, asset_id=str(asset_record.id))
        if not deleted_count:
            responses.append({
                    "signal": ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_VECTORDB_ERROR.value,
                    "file_id": str(asset_record.id)
                }
            )
        
        else:
            responses.append({
                    "signal": ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_VECTORDB.value,
                    "file_id": str(asset_record.id),
                    "embeddings_deleted_count": deleted_count
                }
            )
    
    
    elif chunks:
        #RELATED CHUNKS REMOVING
        deleted_count = await chunk_model.delete_chunks_by_asset_id(asset_id=asset_record.id)
               
        if deleted_count > 0:
            responses.append({
                "signal":ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_DATABASE.value,
                "file_id": str(asset_record.id),
                "assets_chunks_deleted": deleted_count
            })
        
        else:
            responses.append({
                "signal":ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_DATABASE_ERROR.value,
                "file_id": str(asset_record.id)
            })
    
        #RELATED EMBEDDINGS CHUNKS REMOVING
        deleted_count = await nlp_controller.delete_vector_db_chunks_by_asset_id(project=project, asset_id=str(asset_record.id))
        if not deleted_count:
            responses.append({
                    "signal": ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_VECTORDB_ERROR.value,
                    "file_id": str(asset_record.id)
                }
            )
        
        else:
            responses.append({
                    "signal": ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_VECTORDB.value,
                    "file_id": str(asset_record.id),
                    "embeddings_deleted_count": deleted_count
                }
            )
    
    
    elif vectorDB:
        deleted_count = await nlp_controller.delete_vector_db_chunks_by_asset_id(project=project, asset_id=str(asset_record.id))
        if not deleted_count:
            responses.append({
                    "signal": ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_VECTORDB_ERROR.value,
                    "file_id": str(asset_record.id)
                }
            )
        
        else:
            responses.append({
                    "signal": ResponseSignal.DOCUMENT_CHUNKS_DELETED_FROM_VECTORDB.value,
                    "file_id": str(asset_record.id),
                    "embeddings_deleted_count": deleted_count
                }
            )
        
    else:
        responses.append({
            "signal": ResponseSignal.FILE_PASSED_TO_DELETE_NOT_REMOVED.value,
            "file_id": str(asset_record.id)
        })
    
    
    return JSONResponse(
        content={
            "Responses": responses
        }
    )
        