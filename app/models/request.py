from typing import Optional
from pydantic import BaseModel


class Post(BaseModel):
    status: str
    title: str
    content: str


class UpdatePostRequest(Post):
    id: int


class IDRequest(BaseModel):
    id: int


class UsernameCheckRequest(BaseModel):
    username: str


class UpdateUserMetadataRequest(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    about: Optional[str] = None
