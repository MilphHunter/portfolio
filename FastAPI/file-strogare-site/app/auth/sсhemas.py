from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserResponse(UserBase):
    model_config = {"from_attributes": True}
    id: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

    class Config:
        orm_mode = True
