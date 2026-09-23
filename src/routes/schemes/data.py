from pydantic import BaseModel
from typing import Optional

class ProcessingRequest(BaseModel):
    file_id: str = None
    chunk_size: Optional[int] = 100
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0

class AssetDeletionRequest(BaseModel):
    asset_name: str
    file: Optional[bool] = True
    documentDB: Optional[bool] = False
    chunks: Optional[bool] = False
    vectorDB: Optional[bool] = False