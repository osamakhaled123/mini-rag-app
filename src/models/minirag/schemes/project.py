from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, INTEGER, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from enums.DataBaseEnum import DataBaseEnum

class Project(SQLAlchemyBase):
    
    __tablename__ = DataBaseEnum.COLLECTION_PROJECT_NAME.value
    
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    project_id = Column(INTEGER, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    assets = relationship("Asset", back_populates="project")
    chunks = relationship("DataChunk", back_populates="project")
    
    __table_args__ = (
        Index("ix_project_id", project_id)
    )