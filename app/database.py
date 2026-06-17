from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# Мы временно убираем settings.DATABASE_URL и пишем строку жестко, чтобы убрать ошибку
from app.config import settings

# Принудительно используем синхронный драйвер psycopg2 и твой верный порт/пароль
DATABASE_URL_SYNC = "postgresql://postgres:123456@127.0.0.1:5051/postgres"

engine = create_engine(
    DATABASE_URL_SYNC, # используем синхронную строку напрямую
    echo=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()