from pydantic import BaseModel


class PostExample(BaseModel):
    example: str


class PromptRead(BaseModel):
    id: int
    role: str
    crypto_role: str
    suggest_post: str
    post_examples: list[str]

    class Config:
        from_attributes = True
