from pydantic import BaseModel, Field
class User(BaseModel):
    Age : int | None = Field(alias="age",default=None)
    SkinType : str | None = Field(alias="skin_type",default=None)
    Concerns : list[str] | None = Field(alias="concerns",default=None)