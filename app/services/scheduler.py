import asyncio
from aiogram import Bot
from app.database import SessionLocal
from app.models import Game, wishlist_association
from app.services.steam import steam_service

def fetch_and_update_games(bot: Bot):
    with SessionLocal() as db:
        games = db.query(Game).all()
        
        for game in games:
            # Создаем временный цикл событий для вызова асинхронного парсера внутри потока
            loop = asyncio.new_event_loop()
            steam_data = loop.run_until_complete(steam_service.get_game_details(game.steam_app_id))
            loop.close()
            
            if not steam_data:
                continue
                
            new_price = steam_data["current_price"]
            
            if new_price < game.current_price:
                game.current_price = new_price
                game.discount_percent = steam_data["discount_percent"]
                db.flush()
                
                user_ids = [r[0] for r in db.query(wishlist_association.c.user_id).filter(wishlist_association.c.game_id == game.steam_app_id).all()]
                
                for user_id in user_ids:
                    try:
                        # Отправку сообщения пушим в основной поток бота
                        asyncio.run_coroutine_threadsafe(
                            bot.send_message(
                                chat_id=user_id,
                                text=(
                                    f"🔥 **Скидка на игру из твоего списка!**\n\n"
                                    f"🎮 **{game.title}** подешевела!\n"
                                    f"Старая цена: {game.initial_price} руб.\n"
                                    f"Новая цена: {new_price} руб. (Скидка: {game.discount_percent}%)\n\n"
                                    f"Бегом в магазин! 🛒"
                                ),
                                parse_mode="Markdown"
                            ),
                            asyncio.get_event_loop()
                        )
                    except Exception:
                        pass
            else:
                game.current_price = new_price
                game.discount_percent = steam_data["discount_percent"]
                
        db.commit()

async def check_prices_job(bot: Bot):
    while True:
        await asyncio.to_thread(fetch_and_update_games, bot)
        await asyncio.sleep(3600)