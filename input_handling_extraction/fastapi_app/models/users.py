from pydantic import BaseModel

class UserRegistration(BaseModel):
    username: str
    email: str 