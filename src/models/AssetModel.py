from minirag.schemes import Asset
from .BaseDataModel import BaseDataModel
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func, delete
from sqlalchemy.dialects.postgresql import UUID

class AssetModel(BaseDataModel):
    def __init__(self, db_client: sessionmaker):
        super().__init__(db_client=db_client)
        
    @classmethod
    async def create_instance(cls, db_client: sessionmaker):
        instance = cls(db_client=db_client)
        return instance   
                
    async def create_asset(self, asset: Asset):       
        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)
            await session.commit()
            await session.refresh(asset)

        return asset
            
    async def get_all_project_id_assets(self, asset_project_id: UUID, asset_type: str = None):
        async with self.db_client() as session:
            async with session.begin():
                query = select(Asset).where(
                    Asset.asset_project_id == asset_project_id,
                    Asset.asset_type == asset_type 
                )
                records = await session.execute(query).scalars().all()
        return records
                
        
        # records = await self.collection.find({
        #     "asset_project_id": asset_project_id
        #     if isinstance(asset_project_id, UUID) else UUID(asset_project_id),
        #     **({"asset_type": asset_type} if asset_type is not None else {})
        # }).to_list(length=None)
        
        # return[
        #     Asset(**record)
        #     for record in records
        # ]
        
    async def get_asset_record(self, asset_project_id: UUID, asset_name: str):
        async with self.db_client() as session:
            async with session.begin():
                query = select(Asset).where(
                    Asset.asset_project_id == asset_project_id,
                    Asset.asset_name == asset_name
                )
                
                result = await session.execute(query)
                record = result.scalar_one_or_none()
        
        return record
                        
    async def delete_asset_record(self, asset_project_id: UUID, asset_id: UUID):
        async with self.db_client() as session:
            async with session.begin():
                query = delete(Asset).where(
                    Asset.id == asset_id,
                    Asset.asset_project_id == asset_project_id
                )
                
                result = await session.execute(query)
                
            return result.rowcount > 0