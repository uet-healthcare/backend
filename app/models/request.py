from pydantic import BaseModel


class Post(BaseModel):
    title: str
    content: str


class UpdatePostRequest(Post):
    id: int


class IDRequest(BaseModel):
    id: int


class UsernameCheckRequest(BaseModel):
    username: str
