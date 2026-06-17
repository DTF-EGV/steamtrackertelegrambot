from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GameBase(BaseModel):
    steam_app_id: int

class GameCreate(GameBase):
    pass

class GameOut(GameBase):
    title: str
    current_price: float
    initial_price: float
    discount_percent: int
    last_updated: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserOut(UserBase):
    tracked_games: List[GameOut] = []

    class Config:
        from_attributes = True