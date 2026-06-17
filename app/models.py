from sqlalchemy import Column, Integer, String, Float, BigInteger, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


wishlist_association = Table(
    "wishlists",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), primary_key=True),
    Column("game_id", Integer, ForeignKey("games.steam_app_id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime, default=datetime.utcnow)
)

class User(Base):
    __tablename__ = "users"

    
    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    
    
    tracked_games = relationship(
        "Game", 
        secondary=wishlist_association, 
        back_populates="subscribers"
    )

class Game(Base):
    __tablename__ = "games"

   
    steam_app_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    
    
    current_price = Column(Float, default=0.0)
    initial_price = Column(Float, default=0.0)  # Цена без скидки
    discount_percent = Column(Integer, default=0)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscribers = relationship(
        "User", 
        secondary=wishlist_association, 
        back_populates="tracked_games"
    )