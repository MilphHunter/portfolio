from pydantic import BaseModel


class TagBase(BaseModel):
    title: str


class TagResponse(TagBase):
    model_config = {"from_attributes": True}
    id: int


class FileUpdateRequest(BaseModel):
    file_id: int
    title: str
    tags: str
    status: bool
