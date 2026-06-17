from fastapi import FastAPI
from app.routers.games import games_router

app = FastAPI(title="Steam Wishlist Tracker API")

app.include_router(games_router, prefix="/api/games", tags=["Games"])

@app.get("/")
async def root():
    return {"message": "Steam Wishlist Tracker API is running"}