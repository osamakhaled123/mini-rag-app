from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, INTEGER, Index, func, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from enums.DataBaseEnum import DataBaseEnum

class Asset(SQLAlchemyBase):
    
    __tablename__ = DataBaseEnum.COLLECTION_ASSET_NAME.value
    
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    asset_type = Column(String, nullable=False)
    asset_name = Column(String, nullable=False)
    asset_size = Column(INTEGER, nullable=False)
    asset_config = Column(JSONB, nullable=True)
    asset_pushed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    asset_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    project = relationship("Project", back_populates="assets")
    chunks = relationship("DataChunk", back_populates="asset")
    
    __table_args__ = (
        Index("ix_asset_project_id", asset_project_id),
        Index("ix_asset_type", asset_type)
    )