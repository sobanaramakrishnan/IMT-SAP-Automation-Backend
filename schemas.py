from pydantic import BaseModel, EmailStr

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    user_role: str
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
