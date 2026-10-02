from minirag.schemes import Project
from .BaseDataModel import BaseDataModel
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):
    def __init__(self, db_client: sessionmaker):
        super().__init__(db_client=db_client)
    
    @classmethod    
    async def create_instance(cls, db_client: sessionmaker):
        instance = cls(db_client=db_client)
        return instance
        
    async def creat_project(self, project: Project): 
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            await session.commit()
            await session.refresh(project)
        
        return project
    
    async def get_project_or_create_one(self, project_id: int):
        async with self.db_client() as session:
            async with session.begin():
                query = select(Project).where(Project.project_id == project_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()
            
                if project is None:
                    project_record = Project(
                        project_id = project_id
                    )
                    project = await self.creat_project(project = project_record)
                
                return project
    
    async def get_all_project(self, page: int=1, page_size: int=10):
        async with self.db_client() as session:
            async with session.begin():
                #count total number of documents
                query = select(func.count(Project.id))
                result = await session.execute(query)
                total_documents = result.scalar_one()

                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1
                
                cursor = select(Project).offset(
                    (page - 1) * page_size
                ).limit(page_size)
                
                result = await session.execute(cursor)
                projects = result.scalars().all()
                
                return projects, total_pages