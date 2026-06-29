from pydantic import BaseModel, ConfigDict

class SchemeCategoriesBase(BaseModel):
    c_name: str

class SchemeCategoriesCreate(SchemeCategoriesBase):
    pass

class SchemeCategoriesRead(SchemeCategoriesBase):
    model_config = ConfigDict(from_attributes=True)# 관례상 위에 두는게 맞음
    
    c_id: int

    

