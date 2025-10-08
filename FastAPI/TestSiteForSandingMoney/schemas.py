from pydantic import BaseModel, EmailStr, constr


class SignupIn(BaseModel):
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    email: EmailStr
    password: constr(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class CodeIn(BaseModel):
    code: constr(min_length=6, max_length=6)
