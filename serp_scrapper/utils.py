from pydantic import BaseModel


class GoogleShoppingData(BaseModel):
    search_query: str
    selected_country: str