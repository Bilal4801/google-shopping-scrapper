from pydantic import BaseModel


class GoogleShoppingData(BaseModel):
    query: str