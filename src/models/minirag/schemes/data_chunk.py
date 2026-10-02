from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, INTEGER, DateTime, func, Index, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import datetime
from pydantic import BaseModel
from enums.DataBaseEnum import DataBaseEnum

class DataChunk(SQLAlchemyBase):
    
    __tablename__ = DataBaseEnum.COLLECTION_CHUNK_NAME.value
    
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    chunk_text = Column(String, nullable=False)
    chunk_metadata = Column(JSONB, nullable=True)
    chunk_order = Column(INTEGER, nullable=False)
    
    chunk_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    chunk_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    
    project = relationship("Project", back_populates="chunks") 
    asset = relationship("Asset", back_populates="chunks")
    
    __table_args__ = (
        Index("ix_chunk_project_id", chunk_project_id),
        Index("ix_chunk_asset_id", chunk_asset_id)
    )
    
    
class RetrievedDocument(BaseModel):
    text: str
    score: float
    inserted_at: datetime        
    chunk_id: str
    asset_id: str
    id: str