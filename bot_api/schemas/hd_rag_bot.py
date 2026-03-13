from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    theme_code: str
    query: str
    user_id: str
    user_pid: str


class QueryResponse(BaseModel):
    response_id: str
    message: str
    links: list = []
    theme_code: str
    user_id: str
    user_pid: str


class UserMessageRequest(BaseModel):
    message: str


class UserMessageResponse(BaseModel):
    LLM_answ: str
    class_: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "LLM_answ": "Для доения коровы нужно...",
                "class_": "консультация",
            }
        }
    }


class ErrorResponse(BaseModel):
    status: str
    message: str


class UpdateMessageRequest(BaseModel):
    page_ids: str


class UpdateMessageResponse(BaseModel):
    status: str
    processed_pages: int
    details: List[dict]

