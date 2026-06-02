from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
import os
from controllers import DataController, ProjectController
from models import ResponseSignal
import aiofiles
import logging

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=['api_v1', 'data']
)

@data_router.post("/upload/{project_id}")
async def upload_file(project_id: str, 
                      file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    
    data_controller = DataController()
    
    is_valid, result_signal = data_controller.validate_data(file = file)
     
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":result_signal
            }
        )
        
    project_controller = ProjectController()    
    project_dir = project_controller.get_project_path(project_id=project_id)
    
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
            
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal":ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id" :file_id
        }
    )        