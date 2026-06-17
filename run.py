import asyncio
import uvicorn
from aiogram import Bot, Dispatcher

from app.config import settings
from app.database import engine, Base
from app.bot.handlers import bot_router
from app.services.scheduler import check_prices_job

async def start_bot():
    # Создаем таблицы через стабильный синхронный движок без всяких async with
    Base.metadata.create_all(bind=engine)

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(bot_router)

    asyncio.create_task(check_prices_job(bot))

    print("Бот успешно запущен и отслеживает цены!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.create_task(start_bot())
    
    config = uvicorn.Config(app="app.main:app", host="127.0.0.1", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    
    loop.run_until_complete(server.serve())

if __name__ == "__main__":
    main()