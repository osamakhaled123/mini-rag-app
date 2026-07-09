from .enums.DataBaseEnum import DataBaseEnum
from .db_schemes import Asset
from .BaseDataModel import BaseDataModel
from bson.objectid import ObjectId

class AssetModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSET_NAME.value]
    
    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client=db_client)
        await instance.init_collection()
        return instance   
     
    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()  #useless
        if DataBaseEnum.COLLECTION_ASSET_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSET_NAME.value]
            indexes = Asset.get_indexes()
            
            for index in indexes:
                self.collection.create_index(
                    keys=index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )
                
    async def create_asset(self, asset: Asset):
        record = await self.collection.insert_one(asset.model_dump(
            by_alias=True, exclude_unset=True))   

        asset.id = record.inserted_id 
        return asset       
    
    async def get_all_project_id_assets(self, asset_project_id: ObjectId):
        return await self.collection.find({
            "asset_project_id": asset_project_id
            if isinstance(asset_project_id, ObjectId) else str(asset_project_id)
        }).to_list(len=None)
        
        
        