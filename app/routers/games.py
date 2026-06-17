from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Game
from app.schemas import GameOut, GameCreate
from app.services.steam import steam_service

games_router = APIRouter()

@games_router.get("/", response_model=List[GameOut])
def get_all_games(db: Session = Depends(get_db)):
    return db.query(Game).all()

@games_router.post("/", response_model=GameOut)
async def add_game_via_api(game_in: GameCreate, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.steam_app_id == game_in.steam_app_id).first()
    if game:
        raise HTTPException(status_code=400, detail="Game already exists in database")
        
    steam_data = await steam_service.get_game_details(game_in.steam_app_id)
    if not steam_data:
        raise HTTPException(status_code=404, detail="Game not found in Steam")
        
    new_game = Game(
        steam_app_id=game_in.steam_app_id,
        title=steam_data["title"],
        current_price=steam_data["current_price"],
        initial_price=steam_data["initial_price"],
        discount_percent=steam_data["discount_percent"]
    )
    
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    return new_game