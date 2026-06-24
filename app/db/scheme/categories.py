from pydantic import BaseModel, ConfigDict

class SchemeCategoriesBase(BaseModel):
    c_name: str

class SchemeCategoriesCreate(SchemeCategoriesBase):
    pass

class SchemeCategoriesRead(SchemeCategoriesBase):
    c_id: int

    model_config = ConfigDict(from_attributes=True)

    #커밋 연습