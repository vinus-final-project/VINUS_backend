from pydantic import BaseModel, ConfigDict

class CategoriesBase(BaseModel):
    c_name: str

class CategoriesCreate(CategoriesBase):
    pass

class CategoriesRead(CategoriesBase):
    model_config = ConfigDict(from_attributes=True)# 관례상 위에 두는게 맞음
    
    c_id: int

    

