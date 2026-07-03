from pydantic import BaseModel

class AuthorResponse(BaseModel):
    author: str
    count: int
