from pydantic import BaseModel


class Post(BaseModel):
    title: str
    content: str


class UsernameCheckRequest(BaseModel):
    username: str
