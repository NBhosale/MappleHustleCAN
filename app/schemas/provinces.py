from pydantic import BaseModel

class CanadianProvinceResponse(BaseModel):
    code: str
    name: str

    class Config:
        orm_mode = True
